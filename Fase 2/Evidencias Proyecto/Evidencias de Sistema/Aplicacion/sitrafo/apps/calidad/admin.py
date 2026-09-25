"""Administracion de Django para el dominio de control de calidad."""
from django.contrib import admin

from .models import (
    ControlCalidad,
    NoConformidad,
    ProtocoloCalidad,
    PuntoControl,
    ResultadoControl,
)


class PuntoControlInline(admin.TabularInline):
    model = PuntoControl
    extra = 1


@admin.register(ProtocoloCalidad)
class ProtocoloCalidadAdmin(admin.ModelAdmin):
    list_display = ["nombre", "modelo", "version", "norma_referencia", "activo"]
    list_filter = ["activo", "modelo"]
    search_fields = ["nombre", "modelo__codigo"]
    autocomplete_fields = ["modelo"]
    inlines = [PuntoControlInline]


class ResultadoInline(admin.TabularInline):
    model = ResultadoControl
    extra = 1
    autocomplete_fields = ["punto"]
    readonly_fields = ["conforme", "registrado_en"]


@admin.register(ControlCalidad)
class ControlCalidadAdmin(admin.ModelAdmin):
    list_display = ["orden_trabajo", "protocolo", "inspector",
                    "fecha_hora", "estado", "pendientes_display"]
    list_filter = ["estado", "fecha_hora"]
    search_fields = ["orden_trabajo__numero"]
    autocomplete_fields = ["orden_trabajo", "protocolo", "inspector"]
    inlines = [ResultadoInline]

    @admin.display(description="puntos obligatorios pendientes")
    def pendientes_display(self, obj):
        return obj.puntos_pendientes.count() if obj.pk else "-"

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.actualizar_estado()


@admin.register(PuntoControl)
class PuntoControlAdmin(admin.ModelAdmin):
    list_display = ["nombre", "protocolo", "tipo_ensayo", "unidad",
                    "tolerancia_inf", "tolerancia_sup", "obligatorio"]
    list_filter = ["obligatorio", "tipo_ensayo"]
    search_fields = ["nombre", "protocolo__nombre"]


@admin.register(NoConformidad)
class NoConformidadAdmin(admin.ModelAdmin):
    list_display = ["id_no_conformidad", "resultado", "severidad",
                    "estado", "responsable", "abierta_en", "cerrada_en"]
    list_filter = ["estado", "severidad", "abierta_en"]
    search_fields = ["descripcion"]
    autocomplete_fields = ["responsable", "usuario_cierre"]
    readonly_fields = ["abierta_en", "cerrada_en", "usuario_cierre"]
