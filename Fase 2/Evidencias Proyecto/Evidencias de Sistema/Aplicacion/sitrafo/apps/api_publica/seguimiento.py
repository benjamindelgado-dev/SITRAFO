"""
Estado de un pedido para la API publica de seguimiento.

Arma una vista resumida de la orden de compra y sus ordenes de trabajo:
etapa actual, porcentaje de avance, fecha estimada de entrega en dias
habiles e historial de estados. No expone montos, responsables ni
observaciones internas.
"""
from datetime import timedelta

from django.utils import timezone

from apps.configuracion.models import Feriado
from apps.configuracion.services.feriados import plazo_en_dias_habiles

# Etapas visibles para el cliente, en orden
ETAPAS = [
    ("recibido", "Pedido recibido"),
    ("confirmado", "Anticipo pagado y pedido confirmado"),
    ("fabricacion", "En fabricacion"),
    ("calidad", "Control de calidad"),
    ("listo", "Listo para entrega"),
    ("entregado", "Entregado"),
]
RECIBIDO, CONFIRMADO, FABRICACION, CALIDAD, LISTO, ENTREGADO = range(len(ETAPAS))

# Etapa alcanzada segun el estado de cada documento
ETAPA_ORDEN_COMPRA = {
    "pendiente": RECIBIDO,
    "confirmada": CONFIRMADO,
    "en_produccion": FABRICACION,
    "entregada": ENTREGADO,
}
ETAPA_ORDEN_TRABAJO = {
    "planificada": CONFIRMADO,
    "en_ejecucion": FABRICACION,
    "en_calidad": CALIDAD,
    "liberada": LISTO,
    "cerrada": LISTO,
}

# Porcentaje de avance al alcanzar cada etapa. Durante la fabricacion se
# suma el avance real de las ordenes de trabajo (de 15 % a 75 %).
AVANCE_ETAPA = {RECIBIDO: 5, CONFIRMADO: 15, FABRICACION: 15, CALIDAD: 85, LISTO: 95,
                ENTREGADO: 100}
TRAMO_FABRICACION = 60


def _fecha_local(momento):
    return timezone.localtime(momento).date() if momento else None


def _primera_fecha(historiales, codigos):
    fechas = [h.fecha_hora for h in historiales if h.estado_nuevo.codigo in codigos]
    return min(fechas) if fechas else None


def _ultima_fecha(historiales, codigos):
    fechas = [h.fecha_hora for h in historiales if h.estado_nuevo.codigo in codigos]
    return max(fechas) if fechas else None


def _dias_habiles_entre(desde, hasta) -> int:
    """Dias habiles desde 'desde' (excluido) hasta 'hasta' (incluido)."""
    if hasta <= desde:
        return 0
    feriados = set(Feriado.objects.filter(fecha__gt=desde, fecha__lte=hasta)
                   .values_list("fecha", flat=True))
    dias, fecha = 0, desde
    while fecha < hasta:
        fecha += timedelta(days=1)
        if fecha.weekday() < 5 and fecha not in feriados:
            dias += 1
    return dias


def _entrega(orden, etapa: int, hoy):
    cotizacion = orden.cotizacion
    fecha, origen, con_feriados = None, None, True
    if cotizacion.fecha_entrega:
        fecha, origen = cotizacion.fecha_entrega, "comprometida"
    elif cotizacion.plazo_dias_habiles:
        fecha, con_feriados = plazo_en_dias_habiles(
            _fecha_local(orden.creado_en), cotizacion.plazo_dias_habiles
        )
        origen = "calculada"
    if fecha is None:
        return {"fecha_estimada": None, "origen": None, "dias_habiles_restantes": None,
                "considera_feriados": None, "atrasado": False}
    entregado = etapa == ENTREGADO
    return {
        "fecha_estimada": fecha,
        "origen": origen,
        "dias_habiles_restantes": 0 if entregado else _dias_habiles_entre(hoy, fecha),
        "considera_feriados": con_feriados,
        "atrasado": not entregado and hoy > fecha,
    }


def estado_pedido(orden) -> dict:
    """Resumen del pedido listo para serializar."""
    hoy = timezone.localdate()
    historial_oc = list(orden.historial.select_related("estado_nuevo"))
    ordenes_trabajo = list(
        orden.ordenes_trabajo.select_related("estado", "modelo")
        .prefetch_related("historial__estado_nuevo")
    )
    activas = [ot for ot in ordenes_trabajo if ot.estado.codigo != "anulada"]
    historial_ot = [h for ot in activas for h in ot.historial.all()]

    anulado = orden.estado.codigo == "anulada"
    etapa = ETAPA_ORDEN_COMPRA.get(orden.estado.codigo, RECIBIDO)
    if activas and etapa not in (RECIBIDO, ENTREGADO):
        etapa = min(ETAPA_ORDEN_TRABAJO.get(ot.estado.codigo, CONFIRMADO) for ot in activas)

    if anulado:
        avance = 0
    elif etapa == FABRICACION and activas:
        promedio = sum(float(ot.avance_pct or 0) for ot in activas) / len(activas)
        avance = AVANCE_ETAPA[FABRICACION] + round(TRAMO_FABRICACION * promedio / 100)
    else:
        avance = AVANCE_ETAPA[etapa]

    fechas = {
        RECIBIDO: orden.creado_en,
        CONFIRMADO: _primera_fecha(historial_oc, {"confirmada"}),
        FABRICACION: _primera_fecha(historial_ot, {"en_ejecucion"}),
        CALIDAD: _primera_fecha(historial_ot, {"en_calidad"}),
        LISTO: _ultima_fecha(historial_ot, {"liberada", "cerrada"}),
        ENTREGADO: _primera_fecha(historial_oc, {"entregada"}),
    }
    etapas = [
        {
            "codigo": codigo,
            "nombre": nombre,
            "completada": not anulado and (indice < etapa or etapa == ENTREGADO),
            "actual": not anulado and indice == etapa,
            "fecha": fechas[indice] if not anulado and indice <= etapa else None,
        }
        for indice, (codigo, nombre) in enumerate(ETAPAS)
    ]

    historial = [
        {"fecha_hora": h.fecha_hora, "documento": orden.numero, "estado": h.estado_nuevo.nombre}
        for h in historial_oc
    ] + [
        {"fecha_hora": h.fecha_hora, "documento": ot.numero, "estado": h.estado_nuevo.nombre}
        for ot in activas for h in ot.historial.all()
    ]
    historial.sort(key=lambda h: h["fecha_hora"])

    return {
        "numero": orden.numero,
        "estado": {"codigo": orden.estado.codigo, "nombre": orden.estado.nombre},
        "anulado": anulado,
        "fecha_pedido": _fecha_local(orden.creado_en),
        "etapa_actual": "anulado" if anulado else ETAPAS[etapa][0],
        "avance_pct": avance,
        "etapas": etapas,
        "productos": [
            {"orden_trabajo": ot.numero, "modelo": ot.modelo.nombre, "cantidad": ot.cantidad,
             "estado": ot.estado.nombre, "avance_pct": float(ot.avance_pct or 0)}
            for ot in ordenes_trabajo
        ],
        "entrega": _entrega(orden, etapa, hoy),
        "historial": historial,
        "consultado_en": timezone.now(),
    }
