"""
Carga los estados de documento iniciales.

Uso:
    python manage.py cargar_estados
"""
from django.core.management.base import BaseCommand

from apps.comercial.models import EstadoDocumento

ESTADOS = {
    "solicitud": [
        ("recibida", "Recibida", False),
        ("asignada", "Asignada", False),
        ("cotizada", "Cotizada", False),
        ("desestimada", "Desestimada", True),
    ],
    "cotizacion": [
        ("borrador", "Borrador", False),
        ("en_aprobacion", "En aprobacion", False),
        ("emitida", "Emitida", False),
        ("aceptada", "Aceptada", True),
        ("rechazada", "Rechazada", True),
        ("vencida", "Vencida", True),
        ("anulada", "Anulada", True),
    ],
    "orden_compra": [
        ("pendiente", "Pendiente", False),
        ("confirmada", "Confirmada", False),
        ("en_produccion", "En produccion", False),
        ("entregada", "Entregada", True),
        ("anulada", "Anulada", True),
    ],
    "orden_trabajo": [
        ("planificada", "Planificada", False),
        ("en_ejecucion", "En ejecucion", False),
        ("en_calidad", "En control de calidad", False),
        ("cerrada", "Cerrada", True),
        ("anulada", "Anulada", True),
    ],
}


class Command(BaseCommand):
    help = "Carga los estados de documento del flujo comercial y productivo."

    def handle(self, *args, **options):
        creados = 0
        for tipo, estados in ESTADOS.items():
            for codigo, nombre, es_final in estados:
                _, nuevo = EstadoDocumento.objects.get_or_create(
                    tipo_documento=tipo,
                    codigo=codigo,
                    defaults={"nombre": nombre, "es_final": es_final},
                )
                creados += int(nuevo)
        total = EstadoDocumento.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Estados creados: {creados}. Total en el sistema: {total}."
            )
        )
