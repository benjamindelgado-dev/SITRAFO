"""Administracion de Django para el dominio de configuracion."""
from django.contrib import admin

from .models import AvisoSitio, Feriado, LogIntegracion, ParametroSistema


@admin.register(ParametroSistema)
class ParametroSistemaAdmin(admin.ModelAdmin):
    """Panel de administracion del canal web (RF-ADM-01 a RF-ADM-04)."""

    list_display = ["clave", "valor", "ambito", "tipo_dato",
                    "descripcion", "modificado_en", "usuario"]
    list_filter = ["ambito", "tipo_dato"]
    search_fields = ["clave", "descripcion"]
    readonly_fields = ["modificado_en"]
    autocomplete_fields = ["usuario"]


@admin.register(AvisoSitio)
class AvisoSitioAdmin(admin.ModelAdmin):
    list_display = ["titulo", "tipo", "vigente_desde", "vigente_hasta",
                    "activo", "publicado_display"]
    list_filter = ["tipo", "activo"]
    search_fields = ["titulo", "cuerpo"]
    autocomplete_fields = ["usuario"]

    @admin.display(description="publicado ahora", boolean=True)
    def publicado_display(self, obj):
        return obj.esta_publicado


@admin.register(Feriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ["fecha", "nombre", "tipo", "obtenido_en"]
    list_filter = ["tipo", "fecha"]
    search_fields = ["nombre"]
    date_hierarchy = "fecha"


@admin.register(LogIntegracion)
class LogIntegracionAdmin(admin.ModelAdmin):
    """Solo lectura: lo escribe el sistema, no el usuario (RF-INT-01)."""

    list_display = ["fecha_hora", "servicio", "endpoint", "metodo",
                    "codigo_respuesta", "latencia_ms", "exitoso"]
    list_filter = ["servicio", "exitoso", "fecha_hora"]
    search_fields = ["servicio", "endpoint", "mensaje_error"]
    date_hierarchy = "fecha_hora"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
