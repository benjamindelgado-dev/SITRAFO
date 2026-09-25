"""
Emite el documento de cobro del anticipo para las ordenes de compra que aun
no lo tienen (RN-15).

La emision ocurre automaticamente al generar la orden de compra desde la API.
Este comando cubre las ordenes creadas antes de que existiera esa regla o
cargadas por otros medios (por ejemplo, datos de demostracion).

Uso:
    python manage.py emitir_cobros
"""
from django.core.management.base import BaseCommand

from apps.comercial.models import OrdenCompra
from apps.pagos.services.cobros import ErrorCobro, emitir_anticipo


class Command(BaseCommand):
    help = "Emite el anticipo de las ordenes de compra que no lo tienen."

    def handle(self, *args, **options):
        emitidos = 0
        ordenes = OrdenCompra.objects.exclude(
            estado__codigo__in=["anulada", "entregada"]
        ).select_related("estado")

        for orden in ordenes:
            try:
                documento, creado = emitir_anticipo(orden)
            except ErrorCobro as error:
                self.stdout.write(self.style.ERROR(f"  {orden.numero}: {error}"))
                return
            if creado:
                emitidos += 1
                self.stdout.write(
                    f"  {orden.numero} -> {documento.numero}: {documento.monto_uf} UF "
                    f"(${documento.monto_clp:,.0f}), vence {documento.vence_el:%d-%m-%Y}"
                    .replace(",", ".")
                )

        self.stdout.write(self.style.SUCCESS(f"{emitidos} documento(s) de cobro emitido(s)."))
