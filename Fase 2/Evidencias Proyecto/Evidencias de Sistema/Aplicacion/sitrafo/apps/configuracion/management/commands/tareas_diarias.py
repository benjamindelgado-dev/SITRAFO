"""
Tareas automaticas diarias (RF-PAG-05, RF-COM-12).

1. Sincroniza UF, UTM y dolar del dia (mindicador).
2. Sincroniza los feriados del anio en curso y del siguiente.
3. Vence las cotizaciones emitidas cuya vigencia ya paso.

Cada tarea es independiente: si un servicio externo no responde, las demas
se ejecutan igual (RF-INT-03). En Render se programa como Cron Job; en
desarrollo se ejecuta a mano.

Uso:
    python manage.py tareas_diarias
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.comercial.models import Cotizacion, CotizacionHistorial, EstadoDocumento
from apps.configuracion.services.feriados import ClienteFeriados
from apps.configuracion.services.indicadores import ClienteIndicadores


class Command(BaseCommand):
    help = "Sincroniza indicadores y feriados, y vence cotizaciones."

    def handle(self, *args, **options):
        hoy = timezone.localdate()

        resultado = ClienteIndicadores().sincronizar_dia()
        self.stdout.write(f"Indicadores: {resultado}")

        for anio in (hoy.year, hoy.year + 1):
            resultado = ClienteFeriados().sincronizar_anio(anio)
            self.stdout.write(f"Feriados {anio}: {resultado.get('total', 0)} "
                              f"({'ok' if resultado['exitoso'] else resultado['error']})")

        vencidas = vencer_cotizaciones(hoy)
        self.stdout.write(self.style.SUCCESS(f"Cotizaciones vencidas: {vencidas}."))


@transaction.atomic
def vencer_cotizaciones(hoy) -> int:
    """Una cotizacion emitida y no respondida pasa a vencida al pasar su fecha."""
    sistema = get_user_model().objects.filter(is_superuser=True).order_by("pk").first()
    vencida = EstadoDocumento.objects.get(tipo_documento="cotizacion", codigo="vencida")
    cantidad = 0
    for cotizacion in Cotizacion.objects.filter(estado__codigo="emitida", vence_el__lt=hoy):
        anterior = cotizacion.estado
        cotizacion.estado = vencida
        cotizacion.save(update_fields=["estado"])
        if sistema:
            CotizacionHistorial.objects.create(
                cotizacion=cotizacion, estado_anterior=anterior, estado_nuevo=vencida,
                usuario=sistema,
                observacion=f"Vencida automaticamente: vigencia hasta {cotizacion.vence_el:%d-%m-%Y}.",
            )
        cantidad += 1
    return cantidad
