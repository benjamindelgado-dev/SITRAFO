"""
Concilia las transacciones que quedaron pendientes (CU-PAG-02, excepcion de
ausencia de respuesta de la pasarela).

Consulta en PayPal el estado real de cada orden y marca el documento como
pagado solo si la captura esta completada y el monto coincide.

Uso:
    python manage.py conciliar_pagos
"""
from django.core.management.base import BaseCommand

from apps.pagos.models import TransaccionPago
from apps.pagos.services.cobros import conciliar_pendiente


class Command(BaseCommand):
    help = "Revisa en PayPal las transacciones pendientes de conciliacion."

    def handle(self, *args, **options):
        pendientes = TransaccionPago.objects.filter(
            estado=TransaccionPago.Estado.PENDIENTE_CONCILIACION
        ).select_related("documento_cobro")

        if not pendientes.exists():
            self.stdout.write("No hay transacciones pendientes de conciliacion.")
            return

        for transaccion in pendientes:
            resultado = conciliar_pendiente(transaccion)
            self.stdout.write(
                f"  {transaccion.documento_cobro.numero} / {transaccion.id_externo}: {resultado}"
            )
