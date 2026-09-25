"""Administracion de Django para el dominio de inventario."""
from django.contrib import admin

from .models import (
    Bodega,
    CategoriaMaterial,
    Material,
    MovimientoInventario,
    PrecioMaterial,
    Proveedor,
)


@admin.register(CategoriaMaterial)
class CategoriaMaterialAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo"]
    search_fields = ["nombre"]


class PrecioMaterialInline(admin.TabularInline):
    model = PrecioMaterial
    extra = 1
    autocomplete_fields = ["proveedor"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "categoria", "unidad_medida",
                    "stock_actual_display", "stock_minimo", "costo_vigente", "activo"]
    list_filter = ["categoria", "unidad_medida", "activo"]
    search_fields = ["codigo", "nombre"]
    autocomplete_fields = ["categoria"]
    inlines = [PrecioMaterialInline]

    @admin.display(description="costo vigente (UF)")
    def costo_vigente(self, obj):
        return obj.costo_vigente or "sin precio"

    @admin.display(description="stock actual")
    def stock_actual_display(self, obj):
        """El stock no se almacena: se calcula sobre movimiento_inventario."""
        return MovimientoInventario.stock_actual(obj)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ["rut", "razon_social", "email", "activo"]
    search_fields = ["rut", "razon_social"]


@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre", "ubicacion", "activo"]
    search_fields = ["codigo", "nombre"]


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """Kardex de movimientos (RF-INV-07)."""

    list_display = ["fecha_hora", "material", "bodega", "tipo",
                    "cantidad", "costo_unitario_uf", "usuario"]
    list_filter = ["tipo", "bodega", "fecha_hora"]
    search_fields = ["material__codigo", "material__nombre"]
    autocomplete_fields = ["material", "bodega", "proveedor", "usuario"]
    date_hierarchy = "fecha_hora"
