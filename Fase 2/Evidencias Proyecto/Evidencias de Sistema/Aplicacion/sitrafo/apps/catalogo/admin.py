"""Administracion de Django para el dominio de catalogo."""
from django.contrib import admin

from .models import (
    BomModelo,
    FamiliaProducto,
    ModeloParametro,
    ModeloProducto,
    ParametroTecnico,
    PrecioBaseModelo,
    TareaEstandarModelo,
    ValorParametro,
)


@admin.register(FamiliaProducto)
class FamiliaProductoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion", "activo"]
    search_fields = ["nombre"]


class ValorParametroInline(admin.TabularInline):
    model = ValorParametro
    extra = 2


@admin.register(ParametroTecnico)
class ParametroTecnicoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "unidad", "tipo_dato", "obligatorio"]
    list_filter = ["tipo_dato", "obligatorio"]
    search_fields = ["codigo", "nombre"]
    inlines = [ValorParametroInline]


class ModeloParametroInline(admin.TabularInline):
    model = ModeloParametro
    extra = 1
    autocomplete_fields = ["parametro"]


class PrecioBaseInline(admin.TabularInline):
    model = PrecioBaseModelo
    extra = 1
    autocomplete_fields = ["usuario"]


class BomInline(admin.TabularInline):
    model = BomModelo
    extra = 1
    autocomplete_fields = ["material"]
    verbose_name_plural = "Lista de materiales (BOM)"


class TareaEstandarInline(admin.TabularInline):
    model = TareaEstandarModelo
    extra = 1


@admin.register(ModeloProducto)
class ModeloProductoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "familia", "precio_vigente_display",
                    "horas_estandar_totales", "publicado", "activo"]
    list_filter = ["familia", "publicado", "activo"]
    search_fields = ["codigo", "nombre"]
    autocomplete_fields = ["familia"]
    inlines = [ModeloParametroInline, PrecioBaseInline, BomInline, TareaEstandarInline]
    actions = ["publicar", "despublicar"]

    @admin.display(description="precio vigente (UF)")
    def precio_vigente_display(self, obj):
        return obj.precio_vigente or "sin precio"

    @admin.action(description="Publicar en el catalogo web")
    def publicar(self, request, queryset):
        actualizados = queryset.update(publicado=True)
        self.message_user(request, f"{actualizados} modelo(s) publicado(s).")

    @admin.action(description="Retirar del catalogo web")
    def despublicar(self, request, queryset):
        actualizados = queryset.update(publicado=False)
        self.message_user(request, f"{actualizados} modelo(s) retirado(s).")
