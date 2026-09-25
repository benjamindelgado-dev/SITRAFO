"""Administracion de Django para el dominio de produccion."""
from django.contrib import admin

from .models import (
    ConsumoMaterial,
    Empleado,
    OrdenTrabajo,
    OrdenTrabajoHistorial,
    RegistroHoraHombre,
    TareaOT,
    TarifaHoraHombre,
)


class TarifaInline(admin.TabularInline):
    model = TarifaHoraHombre
    extra = 1


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ["rut", "nombre", "cargo", "tarifa_display", "activo"]
    list_filter = ["cargo", "activo"]
    search_fields = ["rut", "nombre"]
    autocomplete_fields = ["usuario"]
    inlines = [TarifaInline]

    @admin.display(description="tarifa vigente (UF/h)")
    def tarifa_display(self, obj):
        tarifa = obj.tarifa_vigente_a()
        return tarifa.valor_hora_uf if tarifa else "sin tarifa"


class TareaInline(admin.TabularInline):
    model = TareaOT
    extra = 1
    autocomplete_fields = ["empleado"]
    readonly_fields = ["horas_registradas_display"]

    @admin.display(description="horas registradas")
    def horas_registradas_display(self, obj):
        return obj.horas_registradas if obj.pk else "-"


class OTHistorialInline(admin.TabularInline):
    model = OrdenTrabajoHistorial
    extra = 0
    can_delete = False
    readonly_fields = ["estado_anterior", "estado_nuevo", "usuario",
                       "fecha_hora", "observacion"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ["numero", "modelo", "cantidad", "estado", "avance_pct",
                    "costo_estimado_uf", "costo_real_uf", "desviacion_display"]
    list_filter = ["estado", "creado_en"]
    search_fields = ["numero", "orden_compra__numero"]
    autocomplete_fields = ["orden_compra", "modelo"]
    inlines = [TareaInline, OTHistorialInline]
    readonly_fields = ["costo_real_uf", "avance_pct", "cierre_display"]
    actions = ["recalcular"]
    date_hierarchy = "creado_en"

    fieldsets = (
        ("Identificacion", {"fields": ("numero", "orden_compra", "modelo", "cantidad")}),
        ("Estado", {"fields": ("estado", "fecha_inicio", "fecha_cierre", "avance_pct")}),
        ("Costeo", {
            "fields": ("costo_estimado_uf", "costo_real_uf"),
            "description": "El costo real se consolida desde los consumos y las horas hombre (RN-11).",
        }),
        ("Condiciones de cierre", {"fields": ("cierre_display",)}),
    )

    @admin.display(description="desviacion")
    def desviacion_display(self, obj):
        if obj.costo_real_uf is None:
            return "sin costo real"
        signo = "+" if obj.desviacion_uf >= 0 else ""
        return f"{signo}{obj.desviacion_uf} UF ({signo}{obj.desviacion_pct}%)"

    @admin.display(description="puede cerrarse")
    def cierre_display(self, obj):
        if not obj.pk:
            return "-"
        puede, impedimentos = obj.puede_cerrarse()
        if puede:
            return "Si, cumple todas las condiciones."
        return "No: " + " ".join(impedimentos)

    @admin.action(description="Recalcular costo real y avance")
    def recalcular(self, request, queryset):
        for ot in queryset:
            ot.recalcular_costo_real()
            ot.recalcular_avance()
        self.message_user(request, f"{queryset.count()} orden(es) recalculada(s).")


@admin.register(TareaOT)
class TareaOTAdmin(admin.ModelAdmin):
    list_display = ["orden_trabajo", "secuencia", "nombre", "estado",
                    "empleado", "horas_estimadas", "horas_registradas"]
    list_filter = ["estado"]
    search_fields = ["nombre", "orden_trabajo__numero"]
    autocomplete_fields = ["orden_trabajo", "empleado"]


@admin.register(ConsumoMaterial)
class ConsumoMaterialAdmin(admin.ModelAdmin):
    list_display = ["fecha", "tarea", "material", "cantidad",
                    "costo_unitario_uf", "costo_total_display", "planificado"]
    list_filter = ["planificado", "fecha"]
    search_fields = ["material__nombre", "tarea__orden_trabajo__numero"]
    autocomplete_fields = ["tarea", "material", "bodega", "empleado"]

    @admin.display(description="costo total (UF)")
    def costo_total_display(self, obj):
        return obj.costo_total_uf


@admin.register(RegistroHoraHombre)
class RegistroHoraHombreAdmin(admin.ModelAdmin):
    list_display = ["fecha", "empleado", "tarea", "horas",
                    "valor_hora_uf", "costo_total_display", "anulado"]
    list_filter = ["anulado", "fecha"]
    search_fields = ["empleado__nombre", "tarea__orden_trabajo__numero"]
    autocomplete_fields = ["tarea", "empleado", "usuario_registro"]
    date_hierarchy = "fecha"

    @admin.display(description="costo total (UF)")
    def costo_total_display(self, obj):
        return obj.costo_total_uf
