"""
Reportes de gestion (RF-REP-01 a RF-REP-05).

Cada reporte devuelve una estructura tabular comun, de modo que la misma
salida se muestra en la aplicacion de escritorio y se exporta a Excel o PDF
(RF-REP-06):

    {"titulo", "descripcion", "columnas", "filas", "totales"}

Los reportes leen los datos operativos: no hay tablas de reporte que
mantener sincronizadas.
"""
import datetime
from collections import defaultdict
from decimal import Decimal

from django.db.models import DecimalField, F, Sum

from apps.comercial.models import (
    Cotizacion,
    OrdenCompra,
    OrdenCompraHistorial,
    SolicitudPresupuesto,
)
from apps.produccion.models import ConsumoMaterial, OrdenTrabajo, RegistroHoraHombre

CERO = Decimal("0")


def _mes(fecha) -> str:
    return fecha.strftime("%Y-%m")


def comercial(desde: datetime.date, hasta: datetime.date) -> dict:
    """RF-REP-01: embudo comercial por mes."""
    rango = {"creado_en__date__gte": desde, "creado_en__date__lte": hasta}
    meses = defaultdict(lambda: {"solicitudes": 0, "emitidas": 0, "aceptadas": 0,
                                 "vendido": CERO})
    for s in SolicitudPresupuesto.objects.filter(**rango).only("creado_en"):
        meses[_mes(s.creado_en)]["solicitudes"] += 1
    for c in Cotizacion.objects.filter(**rango).exclude(
            estado__codigo__in=["borrador", "en_aprobacion", "anulada"]).select_related("estado"):
        meses[_mes(c.creado_en)]["emitidas"] += 1
        if c.estado.codigo == "aceptada":
            meses[_mes(c.creado_en)]["aceptadas"] += 1
    for o in OrdenCompra.objects.filter(**rango).exclude(estado__codigo="anulada"):
        meses[_mes(o.creado_en)]["vendido"] += o.total_uf

    filas, total = [], {"solicitudes": 0, "emitidas": 0, "aceptadas": 0, "vendido": CERO}
    for mes in sorted(meses):
        m = meses[mes]
        tasa = (Decimal(m["aceptadas"]) / m["emitidas"] * 100) if m["emitidas"] else CERO
        filas.append([mes, m["solicitudes"], m["emitidas"], m["aceptadas"],
                      round(tasa, 1), m["vendido"]])
        for k in total:
            total[k] += m[k]
    tasa_total = (Decimal(total["aceptadas"]) / total["emitidas"] * 100
                  if total["emitidas"] else CERO)
    return {
        "titulo": "Indicadores comerciales",
        "descripcion": "Solicitudes, cotizaciones emitidas y aceptadas, tasa de conversion "
                       "y monto vendido (ordenes de compra no anuladas).",
        "columnas": ["Mes", "Solicitudes", "Cotizaciones emitidas", "Aceptadas",
                     "Conversion %", "Vendido UF"],
        "filas": filas,
        "totales": ["Total", total["solicitudes"], total["emitidas"], total["aceptadas"],
                    round(tasa_total, 1), total["vendido"]],
    }


def costos(desde, hasta) -> dict:
    """RF-REP-02: costo estimado contra costo real por orden de trabajo."""
    ots = (OrdenTrabajo.objects
           .filter(creado_en__date__gte=desde, creado_en__date__lte=hasta)
           .exclude(estado__codigo="anulada")
           .select_related("modelo", "estado", "orden_compra__cliente").order_by("numero"))
    filas, estimado, real = [], CERO, CERO
    for ot in ots:
        filas.append([ot.numero, ot.orden_compra.cliente.razon_social, ot.modelo.codigo,
                      ot.estado.nombre, ot.costo_estimado_uf, ot.costo_real_uf,
                      ot.desviacion_pct])
        estimado += ot.costo_estimado_uf
        real += ot.costo_real_uf
    desviacion = ((real - estimado) / estimado * 100).quantize(Decimal("0.01")) \
        if estimado else CERO
    return {
        "titulo": "Costo estimado contra costo real",
        "descripcion": "Ordenes de trabajo del periodo. El costo real de las ordenes en "
                       "fabricacion es parcial.",
        "columnas": ["Orden", "Cliente", "Modelo", "Estado", "Estimado UF", "Real UF",
                     "Desviacion %"],
        "filas": filas,
        "totales": ["Total", "", "", "", estimado, real, desviacion],
    }


def consumos(desde, hasta) -> dict:
    """RF-REP-03: consumo de materiales por material y orden de trabajo."""
    datos = (ConsumoMaterial.objects
             .filter(fecha__date__gte=desde, fecha__date__lte=hasta)
             .values("material__codigo", "material__nombre", "material__unidad_medida",
                     "tarea__orden_trabajo__numero")
             .annotate(total_cantidad=Sum("cantidad"),
                       costo=Sum(F("cantidad") * F("costo_unitario_uf"),
                                 output_field=DecimalField(max_digits=14, decimal_places=4)))
             .order_by("material__codigo", "tarea__orden_trabajo__numero"))
    filas, total = [], CERO
    for d in datos:
        filas.append([d["material__codigo"], d["material__nombre"],
                      d["tarea__orden_trabajo__numero"], d["total_cantidad"],
                      d["material__unidad_medida"], d["costo"]])
        total += d["costo"] or CERO
    return {
        "titulo": "Consumo de materiales",
        "descripcion": "Material consumido en taller, por orden de trabajo, valorizado al "
                       "costo congelado en cada consumo.",
        "columnas": ["Codigo", "Material", "Orden", "Cantidad", "Unidad", "Costo UF"],
        "filas": filas,
        "totales": ["Total", "", "", "", "", total],
    }


def horas(desde, hasta) -> dict:
    """RF-REP-04: horas hombre por empleado y orden de trabajo."""
    registros = (RegistroHoraHombre.objects
                 .filter(anulado=False, fecha__gte=desde, fecha__lte=hasta)
                 .select_related("empleado", "tarea__orden_trabajo"))
    agrupado = defaultdict(lambda: [CERO, CERO])
    for r in registros:
        clave = (r.empleado.nombre, r.empleado.cargo, r.tarea.orden_trabajo.numero)
        agrupado[clave][0] += r.horas
        agrupado[clave][1] += r.horas * r.valor_hora_uf
    filas, total_h, total_c = [], CERO, CERO
    for (nombre, cargo, ot), (h, c) in sorted(agrupado.items()):
        filas.append([nombre, cargo, ot, h, c])
        total_h += h
        total_c += c
    return {
        "titulo": "Horas hombre",
        "descripcion": "Horas registradas y no anuladas, valorizadas con la tarifa vigente "
                       "a la fecha de cada registro.",
        "columnas": ["Empleado", "Cargo", "Orden", "Horas", "Costo UF"],
        "filas": filas,
        "totales": ["Total", "", "", total_h, total_c],
    }


def plazos(desde, hasta) -> dict:
    """RF-REP-05: cumplimiento de la fecha de entrega comprometida."""
    entregas = (OrdenCompraHistorial.objects
                .filter(estado_nuevo__codigo="entregada",
                        fecha_hora__date__gte=desde, fecha_hora__date__lte=hasta)
                .select_related("orden_compra__cotizacion", "orden_compra__cliente"))
    filas, a_tiempo = [], 0
    for h in entregas:
        orden = h.orden_compra
        comprometida = orden.cotizacion.fecha_entrega
        real = h.fecha_hora.date()
        dias = (real - comprometida).days if comprometida else None
        cumple = dias is not None and dias <= 0
        a_tiempo += int(cumple)
        filas.append([orden.numero, orden.cliente.razon_social,
                      comprometida.strftime("%d-%m-%Y") if comprometida else "-",
                      real.strftime("%d-%m-%Y"),
                      "-" if dias is None else dias,
                      "A tiempo" if cumple else "Atrasada"])
    cumplimiento = round(Decimal(a_tiempo) / len(filas) * 100, 1) if filas else CERO
    return {
        "titulo": "Cumplimiento de plazos de entrega",
        "descripcion": "Ordenes entregadas en el periodo. Dias negativos: entregada antes "
                       "de la fecha comprometida.",
        "columnas": ["Orden", "Cliente", "Comprometida", "Entregada", "Dias de diferencia",
                     "Resultado"],
        "filas": filas,
        "totales": ["Total", f"{len(filas)} entregas", "", "", "",
                    f"{cumplimiento} % a tiempo"],
    }


REPORTES = {"comercial": comercial, "costos": costos, "consumos": consumos,
            "horas": horas, "plazos": plazos}
