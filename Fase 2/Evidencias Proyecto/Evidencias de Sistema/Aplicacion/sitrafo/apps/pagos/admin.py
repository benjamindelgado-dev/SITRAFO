"""Administracion de Django para el dominio de pagos y moneda."""
from django.contrib import admin

from .models import DocumentoCobro, IndicadorEconomico, TransaccionPago


@admin.register(IndicadorEconomico)
class IndicadorEconomicoAdmin(admin.ModelAdmin):
    list_display = ["fecha", "codigo", "valor", "obtenido_en"]
    list_filter = ["codigo", "fecha"]
    date_hierarchy = "fecha"
    search_fields = ["codigo"]


class TransaccionInline(admin.TabularInline):
    model = TransaccionPago
    extra = 0
    readonly_fields = ["iniciada_en", "resuelta_en", "respuesta"]


@admin.register(DocumentoCobro)
class DocumentoCobroAdmin(admin.ModelAdmin):
    list_display = ["numero", "orden_compra", "tipo", "monto_uf",
                    "monto_clp_display", "estado", "vence_el", "vencido_display"]
    list_filter = ["tipo", "estado", "vence_el"]
    search_fields = ["numero", "orden_compra__numero"]
    autocomplete_fields = ["orden_compra"]
    inlines = [TransaccionInline]

    @admin.display(description="monto (CLP)")
    def monto_clp_display(self, obj):
        return f"${obj.monto_clp:,.0f}".replace(",", ".")

    @admin.display(description="vencido", boolean=True)
    def vencido_display(self, obj):
        return obj.esta_vencido


@admin.register(TransaccionPago)
class TransaccionPagoAdmin(admin.ModelAdmin):
    list_display = ["iniciada_en", "id_externo", "documento_cobro", "pasarela",
                    "monto", "estado", "coincide_display"]
    list_filter = ["estado", "pasarela", "iniciada_en"]
    search_fields = ["id_externo", "documento_cobro__numero"]
    readonly_fields = ["iniciada_en", "respuesta"]

    @admin.display(description="monto coincide", boolean=True)
    def coincide_display(self, obj):
        return obj.monto_coincide
