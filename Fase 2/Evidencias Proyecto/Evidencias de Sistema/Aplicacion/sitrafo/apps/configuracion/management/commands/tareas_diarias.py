"""
Tareas automaticas diarias (RF-PAG-05, RF-COM-12).

1. Sincroniza UF, UTM y dolar del dia (mindicador).
2. Sincroniza los feriados del anio en curso y del siguiente.
3. Vence las cotizaciones emitidas cuya vigencia ya paso.
4. Concilia en PayPal los pagos que quedaron pendientes (CU-PAG-03) y envia el
   comprobante cuando se confirman.

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

        for linea in conciliar_pendientes():
            self.stdout.write(linea)


def conciliar_pendientes() -> list[str]:
    """Revisa cada pago pendiente de conciliacion; un fallo no detiene a los demas."""
    from apps.pagos.models import TransaccionPago
    from apps.pagos.services.cobros import conciliar_pendiente

    pendientes = TransaccionPago.objects.filter(
        estado=TransaccionPago.Estado.PENDIENTE_CONCILIACION).select_related("documento_cobro")
    lineas = [f"Pagos pendientes de conciliacion: {pendientes.count()}"]
    for transaccion in pendientes:
        try:
            with transaction.atomic():
                resultado = conciliar_pendiente(transaccion)
        except Exception as error:  # noqa: BLE001
            resultado = f"error: {error}"
        lineas.append(f"  {transaccion.documento_cobro.numero}: {resultado}")
    return lineas


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
