"""
Precio referencial para la API publica del cotizador.

Usa el mismo costeo que el area comercial aplica al elaborar una cotizacion
(costear_modelo, RF-COM-04): lista de materiales valorizada, horas estandar
por la tarifa de referencia, recargo indirecto y margen por defecto. Si el
modelo no tiene costeo, usa su precio base del catalogo.

La respuesta entrega solo el precio de venta referencial: nunca los costos
internos ni el margen, que son informacion reservada de la empresa.
"""
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.catalogo.models import ModeloProducto
from apps.comercial.services import PLAZO_DEFECTO_DIAS_HABILES, costear_modelo
from apps.configuracion import parametros
from apps.configuracion.services.feriados import plazo_en_dias_habiles
from apps.configuracion.services.indicadores import valor_uf
from apps.pagos.services.cobros import tipo_cambio_usd

DOS = Decimal("0.01")
PESO = Decimal("1")
MAXIMO_ITEMS = 10
AVISO = ("Estimacion referencial: no constituye una cotizacion. El precio definitivo "
         "depende de la especificacion tecnica y se confirma en la cotizacion formal.")


def modelos_cotizables():
    """Modelos visibles en el catalogo web (publicados y activos)."""
    return (ModeloProducto.objects.filter(publicado=True, activo=True)
            .select_related("familia").prefetch_related("precios").order_by("codigo"))


def _redondear(valor: Decimal | None, paso: Decimal) -> Decimal | None:
    return None if valor is None else valor.quantize(paso, rounding=ROUND_HALF_UP)


def _a_pesos(monto_uf: Decimal | None, uf: Decimal | None) -> Decimal | None:
    return None if monto_uf is None or uf is None else _redondear(monto_uf * uf, PESO)


def _url_solicitud(modelo, cantidad: int) -> str:
    ruta = reverse("web:solicitar")
    return f"{settings.SITIO_URL.rstrip('/')}{ruta}?modelo={modelo.pk}&cantidad={cantidad}"


def estimar(items: list[dict]) -> dict:
    """
    Calcula el precio referencial de una lista de modelos y cantidades.

    Cada item trae el ModeloProducto ya validado y la cantidad. Un modelo sin
    costeo ni precio base se informa como no disponible, sin detener el resto.
    """
    hoy = timezone.localdate()
    uf, fecha_uf, _ = valor_uf()
    dolar = tipo_cambio_usd()

    resultado_items = []
    total_uf = Decimal("0")
    todos_disponibles = True
    for item in items:
        modelo, cantidad = item["modelo"], item["cantidad"]
        precio = costear_modelo(modelo).precio_sugerido_uf
        disponible = bool(precio and precio > 0)
        precio_unitario = _redondear(precio, DOS) if disponible else None
        subtotal = precio_unitario * cantidad if disponible else None
        if disponible:
            total_uf += subtotal
        else:
            todos_disponibles = False
        resultado_items.append({
            "modelo": {"codigo": modelo.codigo, "nombre": modelo.nombre,
                       "familia": modelo.familia.nombre},
            "cantidad": cantidad,
            "disponible": disponible,
            "precio_unitario_uf": precio_unitario,
            "subtotal_uf": subtotal,
            "subtotal_clp": _a_pesos(subtotal, uf),
            "solicitar_presupuesto": _url_solicitud(modelo, cantidad),
        })

    hay_total = any(i["disponible"] for i in resultado_items)
    total_uf = _redondear(total_uf, DOS) if hay_total else None
    total_clp = _a_pesos(total_uf, uf)
    total_usd = (_redondear(total_clp / dolar.valor, DOS)
                 if total_clp is not None and dolar else None)

    entrega, con_feriados = plazo_en_dias_habiles(hoy, PLAZO_DEFECTO_DIAS_HABILES)
    validez = parametros.validez_estimacion_dias()
    avisos = [AVISO]
    if not todos_disponibles:
        avisos.append("Uno o mas modelos no tienen precio referencial: se cotizan segun "
                      "especificacion. Use el enlace de solicitud de presupuesto.")
    if uf is None:
        avisos.append("No hay valor de UF disponible: los montos en pesos y dolares se "
                      "omiten.")
    elif fecha_uf != hoy:
        avisos.append(f"Se uso el ultimo valor de UF conocido, del {fecha_uf:%d-%m-%Y}.")

    return {
        "items": resultado_items,
        "total_uf": total_uf,
        "total_clp": total_clp,
        "total_usd": total_usd,
        "indicadores": {
            "uf": {"valor": uf, "fecha": fecha_uf},
            "dolar": {"valor": dolar.valor if dolar else None,
                      "fecha": dolar.fecha if dolar else None},
        },
        "plazo": {
            "dias_habiles": PLAZO_DEFECTO_DIAS_HABILES,
            "fecha_entrega_estimada": entrega,
            "considera_feriados": con_feriados,
        },
        "valida_hasta": hoy + timedelta(days=validez),
        "avisos": avisos,
        "consultado_en": timezone.now(),
    }
