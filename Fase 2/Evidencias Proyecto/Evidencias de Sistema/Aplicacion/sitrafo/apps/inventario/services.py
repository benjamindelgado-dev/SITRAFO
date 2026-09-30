"""
Servicios del inventario (CU-INV-01 a CU-INV-06).

Reglas:
- RN-09: el stock no se almacena; es la suma de los movimientos. Toda
  entrada o salida es un movimiento con fecha, usuario y motivo, de modo que
  el kardex explica cualquier saldo.
- Ningun movimiento deja el saldo de una bodega en negativo.
- La recepcion registra el costo de la compra; si difiere del precio vigente
  puede abrir una nueva vigencia de precio, sin sobrescribir la anterior.
- El ajuste parte del conteo fisico: se registra la diferencia contra el
  sistema, con motivo obligatorio, y queda auditado.
"""
import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.seguridad.models import Auditoria

from .models import Material, MovimientoInventario, PrecioMaterial


class ErrorInventario(Exception):
    """Regla que impide el movimiento de inventario."""


def _numero(valor: Decimal) -> str:
    texto = format(Decimal(valor).normalize(), "f")
    return texto.rstrip("0").rstrip(".") if "." in texto else texto


def fijar_precio(material: Material, costo: Decimal, usuario, proveedor=None
                 ) -> PrecioMaterial:
    """Versiona el precio de compra: cierra el vigente y abre uno nuevo."""
    hoy = timezone.localdate()
    vigente = material.precios.filter(vigente_hasta__isnull=True).first()
    if vigente and vigente.costo_uf == costo:
        return vigente
    if vigente and vigente.vigente_desde >= hoy:
        vigente.costo_uf, vigente.proveedor = costo, proveedor or vigente.proveedor
        vigente.save(update_fields=["costo_uf", "proveedor"])
        precio = vigente
    else:
        if vigente:
            vigente.vigente_hasta = hoy - datetime.timedelta(days=1)
            vigente.save(update_fields=["vigente_hasta"])
        precio = PrecioMaterial.objects.create(material=material, proveedor=proveedor,
                                               costo_uf=costo, vigente_desde=hoy)
    Auditoria.objects.create(
        usuario=usuario, entidad="material", id_registro=str(material.pk),
        accion=Auditoria.Accion.MODIFICACION,
        valor_anterior={"costo_uf": str(vigente.costo_uf) if vigente else None},
        valor_nuevo={"costo_uf": str(costo)}, origen=Auditoria.Origen.ESCRITORIO,
    )
    return precio


@transaction.atomic
def recepcionar(material: Material, bodega, cantidad: Decimal, usuario, *,
                costo_unitario_uf: Decimal | None = None, proveedor=None,
                documento: str = "", actualizar_precio: bool = False
                ) -> MovimientoInventario:
    """Entrada de material comprado (CU-INV-03)."""
    cantidad = Decimal(str(cantidad))
    if cantidad <= 0:
        raise ErrorInventario("La cantidad recibida debe ser mayor que cero.")
    costo = (Decimal(str(costo_unitario_uf)) if costo_unitario_uf is not None
             else material.costo_vigente)
    if costo is None:
        raise ErrorInventario(f"{material.nombre} no tiene precio: indique el costo unitario.")
    if costo < 0:
        raise ErrorInventario("El costo no puede ser negativo.")

    movimiento = MovimientoInventario.objects.create(
        material=material, bodega=bodega, tipo=MovimientoInventario.Tipo.RECEPCION,
        cantidad=cantidad, costo_unitario_uf=costo, proveedor=proveedor, usuario=usuario,
        observacion=(f"Documento {documento.strip()}" if documento.strip()
                     else "Recepcion de compra")[:200],
    )
    if actualizar_precio or material.costo_vigente is None:
        fijar_precio(material, costo, usuario, proveedor)
    return movimiento


@transaction.atomic
def ajustar(material: Material, bodega, conteo_fisico: Decimal, motivo: str, usuario
            ) -> MovimientoInventario | None:
    """
    Ajuste por conteo fisico (CU-INV-04). Registra la diferencia contra el
    sistema; si no hay diferencia no se crea movimiento.
    """
    conteo = Decimal(str(conteo_fisico))
    if conteo < 0:
        raise ErrorInventario("El conteo fisico no puede ser negativo.")
    if len(motivo.strip()) < 5:
        raise ErrorInventario("Indique el motivo del ajuste.")
    sistema = MovimientoInventario.stock_actual(material, bodega)
    diferencia = conteo - sistema
    if diferencia == 0:
        return None

    movimiento = MovimientoInventario.objects.create(
        material=material, bodega=bodega, tipo=MovimientoInventario.Tipo.AJUSTE,
        cantidad=diferencia, costo_unitario_uf=material.costo_vigente or Decimal("0"),
        usuario=usuario, observacion=motivo.strip()[:200],
    )
    Auditoria.objects.create(
        usuario=usuario, entidad="inventario", id_registro=str(movimiento.pk),
        accion=Auditoria.Accion.MODIFICACION,
        valor_anterior={"material": material.codigo, "bodega": bodega.codigo,
                        "stock": _numero(sistema)},
        valor_nuevo={"stock": _numero(conteo), "motivo": motivo.strip()},
        origen=Auditoria.Origen.ESCRITORIO,
    )
    return movimiento


def kardex(material: Material, bodega=None, limite: int = 200, desde=None, hasta=None) -> dict:
    """
    Movimientos del material con saldo acumulado (CU-INV-05).

    Devuelve los ultimos movimientos, en orden cronologico, con el saldo que
    quedo despues de cada uno.
    """
    movimientos = MovimientoInventario.objects.filter(material=material).select_related(
        "bodega", "usuario", "proveedor", "consumo__tarea__orden_trabajo"
    )
    if bodega is not None:
        movimientos = movimientos.filter(bodega=bodega)
    movimientos = list(movimientos.order_by("fecha_hora", "id_movimiento"))

    # El saldo se acumula desde el origen; el rango de fechas solo filtra que
    # filas se muestran (RF-INV-07)
    saldo, filas = Decimal("0"), []
    for m in movimientos:
        saldo += m.cantidad
        fecha = timezone.localtime(m.fecha_hora).date()   # dia en hora de Chile
        if (desde and fecha < desde) or (hasta and fecha > hasta):
            continue
        referencia = m.observacion
        if m.consumo_id:
            referencia = f"{m.consumo.tarea.orden_trabajo.numero} / {m.consumo.tarea.nombre}"
        elif m.proveedor_id:
            referencia = f"{m.proveedor.razon_social} · {m.observacion}"
        filas.append({
            "fecha_hora": m.fecha_hora, "tipo": m.tipo, "tipo_nombre": m.get_tipo_display(),
            "bodega": m.bodega.nombre, "entrada": m.cantidad if m.cantidad > 0 else None,
            "salida": -m.cantidad if m.cantidad < 0 else None, "saldo": saldo,
            "costo_unitario_uf": m.costo_unitario_uf, "usuario": m.usuario.username,
            "referencia": referencia,
        })
    return {"material": material.nombre, "unidad": material.unidad_medida,
            "saldo": saldo, "movimientos": filas[-limite:]}


def materiales_bajo_minimo():
    """Materiales activos cuyo stock total esta bajo el minimo (CU-INV-06)."""
    stocks = dict(MovimientoInventario.objects.values_list("material").annotate(
        t=Sum("cantidad")).values_list("material", "t"))
    return [m for m in Material.objects.filter(activo=True)
            if (stocks.get(m.pk) or Decimal("0")) < m.stock_minimo]


@transaction.atomic
def devolver(material: Material, bodega, cantidad: Decimal, usuario, *, sentido: str,
             motivo: str, proveedor=None) -> MovimientoInventario:
    """
    Devolucion (RF-INV-04).

    - desde_taller: material sobrante que vuelve del taller a la bodega (+).
    - a_proveedor: material que se devuelve al proveedor (-); no puede dejar
      saldo negativo.
    """
    cantidad = Decimal(str(cantidad))
    if cantidad <= 0:
        raise ErrorInventario("La cantidad devuelta debe ser mayor que cero.")
    if len(motivo.strip()) < 5:
        raise ErrorInventario("Indique el motivo de la devolucion.")
    if sentido not in ("desde_taller", "a_proveedor"):
        raise ErrorInventario("Indique si la devolucion viene del taller o va al proveedor.")
    signo = Decimal("1") if sentido == "desde_taller" else Decimal("-1")
    if signo < 0:
        disponible = MovimientoInventario.stock_actual(material, bodega)
        if cantidad > disponible:
            raise ErrorInventario(f"Solo hay {_numero(disponible)} {material.unidad_medida} "
                                  f"de {material.nombre} en {bodega.nombre}.")
    return MovimientoInventario.objects.create(
        material=material, bodega=bodega, tipo=MovimientoInventario.Tipo.DEVOLUCION,
        cantidad=signo * cantidad, costo_unitario_uf=material.costo_vigente or Decimal("0"),
        proveedor=proveedor, usuario=usuario,
        observacion=(("Devolucion desde taller: " if signo > 0 else "Devolucion a proveedor: ")
                     + motivo.strip())[:200],
    )


def costo_promedio(material: Material) -> Decimal | None:
    """
    Costo promedio ponderado de las entradas (recepciones) del material
    (RF-INV-08). Es la base para valorizar el inventario.
    """
    from django.db.models import DecimalField, F

    entradas = MovimientoInventario.objects.filter(
        material=material, tipo=MovimientoInventario.Tipo.RECEPCION)
    totales = entradas.aggregate(
        total_cantidad=Sum("cantidad"),
        total_valor=Sum(F("cantidad") * F("costo_unitario_uf"),
                        output_field=DecimalField(max_digits=18, decimal_places=4)))
    if not totales["total_cantidad"]:
        return material.costo_vigente
    return (totales["total_valor"] / totales["total_cantidad"]).quantize(Decimal("0.0001"))
