"""
Emite los documentos de cobro que falten (RN-15): el anticipo de las ordenes
de compra que aun no lo tienen y el saldo de las que ya terminaron su
fabricacion.

La emision ocurre automaticamente al generar la orden de compra desde la API.
Este comando cubre las ordenes creadas antes de que existiera esa regla o
cargadas por otros medios (por ejemplo, datos de demostracion).

Uso:
    python manage.py emitir_cobros
"""
from django.core.management.base import BaseCommand

from apps.comercial.models import OrdenCompra
from apps.pagos.services.cobros import ErrorCobro, emitir_anticipo, emitir_saldo


class Command(BaseCommand):
    help = "Emite los anticipos y saldos pendientes de emision."

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
            if orden.estado.codigo == "en_produccion":
                try:
                    saldo, creado_saldo = emitir_saldo(orden)
                except ErrorCobro:
                    creado_saldo = False
                if creado_saldo:
                    emitidos += 1
                    self.stdout.write(f"  {orden.numero} -> {saldo.numero}: saldo "
                                      f"{saldo.monto_uf} UF")
            if creado:
                emitidos += 1
                self.stdout.write(
                    f"  {orden.numero} -> {documento.numero}: {documento.monto_uf} UF "
                    f"(${documento.monto_clp:,.0f}), vence {documento.vence_el:%d-%m-%Y}"
                    .replace(",", ".")
                )

        self.stdout.write(self.style.SUCCESS(f"{emitidos} documento(s) de cobro emitido(s)."))
