"""Administracion de Django para el dominio comercial."""
from django.contrib import admin, messages

from apps.configuracion.services import notificaciones

from .models import (
    Cotizacion,
    CotizacionHistorial,
    CotizacionLinea,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraHistorial,
    OrdenCompraLinea,
    SolicitudEspecificacion,
    SolicitudHistorial,
    SolicitudPresupuesto,
)


@admin.register(EstadoDocumento)
class EstadoDocumentoAdmin(admin.ModelAdmin):
    list_display = ["tipo_documento", "codigo", "nombre", "es_final"]
    list_filter = ["tipo_documento", "es_final"]
    search_fields = ["codigo", "nombre"]


class EspecificacionInline(admin.TabularInline):
    model = SolicitudEspecificacion
    extra = 1
    autocomplete_fields = ["parametro"]


class SolicitudHistorialInline(admin.TabularInline):
    model = SolicitudHistorial
    extra = 0
    can_delete = False
    readonly_fields = ["estado_anterior", "estado_nuevo", "usuario",
                       "fecha_hora", "observacion"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SolicitudPresupuesto)
class SolicitudPresupuestoAdmin(admin.ModelAdmin):
    list_display = ["numero", "cliente", "modelo", "cantidad", "estado",
                    "ejecutivo", "creado_en"]
    list_filter = ["estado", "creado_en"]
    search_fields = ["numero", "cliente__razon_social", "cliente__rut"]
    autocomplete_fields = ["cliente", "modelo", "ejecutivo"]
    inlines = [EspecificacionInline, SolicitudHistorialInline]
    date_hierarchy = "creado_en"


class CotizacionLineaInline(admin.TabularInline):
    model = CotizacionLinea
    extra = 1
    autocomplete_fields = ["modelo"]
    readonly_fields = ["costo_estimado_display"]

    @admin.display(description="costo estimado (UF)")
    def costo_estimado_display(self, obj):
        return obj.costo_estimado_uf if obj.pk else "-"


class CotizacionHistorialInline(admin.TabularInline):
    model = CotizacionHistorial
    extra = 0
    can_delete = False
    readonly_fields = ["estado_anterior", "estado_nuevo", "usuario",
                       "fecha_hora", "observacion"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ["numero", "version", "cliente", "estado", "total_uf",
                    "total_clp_display", "vence_el", "vigente_display"]
    list_filter = ["estado", "creado_en"]
    search_fields = ["numero", "cliente__razon_social"]
    autocomplete_fields = ["solicitud", "cliente", "ejecutivo"]
    inlines = [CotizacionLineaInline, CotizacionHistorialInline]
    date_hierarchy = "creado_en"
    readonly_fields = ["total_uf"]

    fieldsets = (
        ("Identificacion", {"fields": ("numero", "version", "solicitud", "cliente")}),
        ("Gestion", {"fields": ("estado", "ejecutivo")}),
        ("Moneda", {
            "fields": ("valor_uf", "fecha_valor_uf"),
            "description": "El valor de la UF queda congelado en el documento (RN-03).",
        }),
        ("Condiciones comerciales", {
            "fields": ("total_uf", "descuento_pct", "plazo_dias_habiles",
                       "fecha_entrega", "vence_el"),
        }),
    )

    @admin.display(description="total (CLP)")
    def total_clp_display(self, obj):
        return f"${obj.total_clp:,.0f}".replace(",", ".")

    @admin.display(description="vigente", boolean=True)
    def vigente_display(self, obj):
        return obj.esta_vigente

    actions = ["enviar_por_correo"]

    @admin.action(description="Enviar la cotizacion al cliente por correo")
    def enviar_por_correo(self, request, queryset):
        """RF-COM-09. Reenvio manual, por ejemplo si el cliente no la recibio."""
        enviadas = sum(
            1 for c in queryset if notificaciones.notificar_cotizacion_emitida(c)
        )
        fallidas = queryset.count() - enviadas
        self.message_user(request, f"{enviadas} cotizacion(es) enviada(s).")
        if fallidas:
            self.message_user(
                request,
                f"{fallidas} no se pudieron enviar (sin destinatario o servicio "
                "no disponible). Revise el registro de integraciones.",
                level=messages.WARNING,
            )


class OrdenCompraLineaInline(admin.TabularInline):
    model = OrdenCompraLinea
    extra = 1


class OrdenCompraHistorialInline(admin.TabularInline):
    model = OrdenCompraHistorial
    extra = 0
    can_delete = False
    readonly_fields = ["estado_anterior", "estado_nuevo", "usuario",
                       "fecha_hora", "observacion"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ["numero", "cliente", "estado", "total_uf",
                    "anticipo_display", "saldo_display", "creado_en"]
    list_filter = ["estado", "creado_en"]
    search_fields = ["numero", "cliente__razon_social"]
    autocomplete_fields = ["cotizacion", "cliente"]
    inlines = [OrdenCompraLineaInline, OrdenCompraHistorialInline]
    date_hierarchy = "creado_en"

    @admin.display(description="anticipo (UF)")
    def anticipo_display(self, obj):
        return obj.monto_anticipo_uf

    @admin.display(description="saldo (UF)")
    def saldo_display(self, obj):
        return obj.monto_saldo_uf
