"""
Bandeja de pendientes del usuario interno.

Lista lo que el usuario tiene que hacer ahora, segun los permisos de su rol y
el estado actual de los documentos. No se guarda: se calcula en cada consulta,
de modo que un pendiente desaparece solo en cuanto alguien lo atiende (a
diferencia de un aviso por correo, que queda en la bandeja aunque ya no
corresponda).

Cada pendiente indica el panel del escritorio donde se atiende.
"""
from django.db.models import Count, Exists, OuterRef

from apps.calidad.models import ControlCalidad, NoConformidad
from apps.comercial.models import Cotizacion, OrdenCompra, SolicitudPresupuesto
from apps.inventario.models import MovimientoInventario
from apps.inventario.services import materiales_bajo_minimo
from apps.pagos.models import DocumentoCobro
from apps.produccion.models import OrdenTrabajo, TareaOT


def _item(tipo, titulo, detalle, panel, referencia, fecha, urgente=False) -> dict:
    return {"tipo": tipo, "titulo": titulo, "detalle": detalle, "panel": panel,
            "referencia": referencia, "fecha": fecha.isoformat() if fecha else None,
            "urgente": urgente}


def _modelo(objeto) -> str:
    modelo = getattr(objeto, "modelo", None)
    return modelo.codigo if modelo else "sin modelo"


def _comercial(usuario) -> list[dict]:
    items = []
    if usuario.has_perm("solicitud.actualizar"):
        for s in (SolicitudPresupuesto.objects.select_related("cliente", "modelo")
                  .filter(estado__codigo="recibida")):
            items.append(_item(
                "solicitud_nueva", f"Asignar y cotizar la solicitud {s.numero}",
                f"{s.cliente.razon_social} · {s.cantidad} x {_modelo(s)}",
                "Solicitudes", s.numero, s.creado_en))
        for s in (SolicitudPresupuesto.objects.select_related("cliente", "modelo")
                  .filter(estado__codigo="asignada", ejecutivo=usuario)):
            items.append(_item(
                "solicitud_asignada", f"Cotizar la solicitud {s.numero}",
                f"{s.cliente.razon_social} · {s.cantidad} x {_modelo(s)}",
                "Solicitudes", s.numero, s.modificado_en))

    if usuario.has_perm("cotizacion.aprobar"):
        for c in (Cotizacion.objects.select_related("cliente", "ejecutivo")
                  .filter(estado__codigo="en_aprobacion").exclude(ejecutivo=usuario)):
            items.append(_item(
                "cotizacion_aprobar", f"Aprobar o devolver la cotizacion {c.numero}",
                f"{c.cliente.razon_social} · descuento {c.descuento_pct.normalize():f}% · "
                f"elaborada por {c.ejecutivo}",
                "Cotizaciones", c.numero, c.modificado_en, urgente=True))

    if usuario.has_perm("cotizacion.actualizar"):
        for c in (Cotizacion.objects.select_related("cliente")
                  .filter(estado__codigo="borrador", ejecutivo=usuario)):
            ultimo = c.historial.order_by("-creado_en").first()
            devuelta = ultimo and ultimo.observacion.startswith("Devuelta")
            items.append(_item(
                "cotizacion_borrador",
                f"{'Corregir' if devuelta else 'Emitir'} la cotizacion {c.numero}",
                ultimo.observacion if devuelta else
                f"{c.cliente.razon_social} · borrador sin emitir",
                "Cotizaciones", c.numero, c.modificado_en, urgente=bool(devuelta)))

    if usuario.has_perm("orden_compra.actualizar"):
        saldo_pagado = DocumentoCobro.objects.filter(
            orden_compra=OuterRef("pk"), tipo=DocumentoCobro.Tipo.SALDO,
            estado=DocumentoCobro.Estado.PAGADO)
        abiertas = OrdenTrabajo.objects.filter(orden_compra=OuterRef("pk")).exclude(
            estado__codigo__in=["cerrada", "anulada"])
        for o in (OrdenCompra.objects.select_related("cliente")
                  .filter(estado__codigo="en_produccion")
                  .filter(Exists(saldo_pagado)).exclude(Exists(abiertas))):
            items.append(_item(
                "orden_entregar", f"Registrar la entrega de la orden {o.numero}",
                f"{o.cliente.razon_social} · saldo pagado",
                "Ordenes de compra", o.numero, o.modificado_en, urgente=True))
    return items


def _produccion(usuario) -> list[dict]:
    if not usuario.has_perm("orden_trabajo.actualizar"):
        return []
    items = []
    for o in (OrdenCompra.objects.select_related("cliente")
              .filter(estado__codigo="confirmada")
              .annotate(n=Count("ordenes_trabajo")).filter(n=0)):
        items.append(_item(
            "orden_sin_ot", f"Generar las ordenes de trabajo de {o.numero}",
            f"{o.cliente.razon_social} · anticipo pagado",
            "Ordenes de compra", o.numero, o.modificado_en, urgente=True))

    sin_terminar = TareaOT.objects.filter(orden_trabajo=OuterRef("pk")).exclude(
        estado=TareaOT.Estado.TERMINADA)
    consulta = (OrdenTrabajo.objects.select_related("modelo", "orden_compra", "estado")
                .filter(estado__codigo__in=["planificada", "en_ejecucion", "liberada"])
                .annotate(pendiente=Exists(sin_terminar)))
    for ot in consulta:
        codigo = ot.estado.codigo
        if codigo == "planificada":
            titulo = f"Planificar e iniciar la orden {ot.numero}"
        elif codigo == "liberada":
            titulo = f"Cerrar la orden {ot.numero} (liberada por calidad)"
        elif not ot.pendiente:
            titulo = f"Enviar a calidad la orden {ot.numero} (tareas terminadas)"
        else:
            continue                                    # en fabricacion: nada que decidir
        items.append(_item(
            f"ot_{codigo}", titulo,
            f"{ot.cantidad} x {_modelo(ot)} · {ot.orden_compra.numero}",
            "Ordenes de trabajo", ot.numero, ot.modificado_en,
            urgente=codigo == "liberada"))

    for nc in (NoConformidad.objects.select_related("resultado__control__orden_trabajo")
               .filter(estado=NoConformidad.Estado.ABIERTA)):
        ot = nc.resultado.control.orden_trabajo
        items.append(_item(
            "nc_corregir", f"Corregir la no conformidad de la orden {ot.numero}",
            nc.descripcion, "No conformidades", ot.numero, nc.abierta_en, urgente=True))
    return items


def _calidad(usuario) -> list[dict]:
    if not usuario.has_perm("ensayo.actualizar"):
        return []
    items = []
    for ot in (OrdenTrabajo.objects.select_related("modelo", "orden_compra")
               .filter(estado__codigo="en_calidad")
               .prefetch_related("controles_calidad")):
        controles = list(ot.controles_calidad.all())
        estados = {c.estado for c in controles}
        if not controles:
            titulo = f"Iniciar el control de calidad de la orden {ot.numero}"
        elif ControlCalidad.Estado.CON_NO_CONFORMIDADES in estados:
            titulo = f"Cerrar la no conformidad y repetir el ensayo de {ot.numero}"
        elif ControlCalidad.Estado.CONFORME in estados:
            titulo = f"Aprobar y liberar la orden {ot.numero} (ensayos conformes)"
        else:
            titulo = f"Registrar los ensayos de la orden {ot.numero}"
        items.append(_item(
            "ot_en_calidad", titulo,
            f"{ot.cantidad} x {_modelo(ot)} · {ot.orden_compra.numero}",
            "Control de calidad", ot.numero, ot.modificado_en,
            urgente=ControlCalidad.Estado.CONFORME in estados))
    return items


def _bodega(usuario) -> list[dict]:
    if not usuario.has_perm("kardex.actualizar"):
        return []
    items = []
    for m in materiales_bajo_minimo():
        stock = MovimientoInventario.stock_actual(m)
        items.append(_item(
            "stock_bajo", f"Reponer {m.nombre}",
            f"Stock {stock.normalize():f} {m.unidad_medida}, minimo "
            f"{m.stock_minimo.normalize():f}",
            "Inventario", m.codigo, None, urgente=stock <= 0))
    return items


def pendientes_de(usuario) -> list[dict]:
    """Pendientes del usuario: primero los urgentes, luego los mas antiguos."""
    items = _comercial(usuario) + _produccion(usuario) + _calidad(usuario) + _bodega(usuario)
    return sorted(items, key=lambda i: (not i["urgente"], i["fecha"] or "9999"))

