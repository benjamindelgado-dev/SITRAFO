"""Serializadores del inventario."""
from rest_framework import serializers

from .models import Bodega, Material, MovimientoInventario


class BodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bodega
        fields = ["id_bodega", "codigo", "nombre", "ubicacion", "activo"]


class MaterialSerializer(serializers.ModelSerializer):
    """Incluye el stock calculado por agregacion y su comparacion con el minimo."""

    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    costo_vigente_uf = serializers.DecimalField(
        source="costo_vigente", max_digits=12, decimal_places=4, read_only=True
    )
    stock_total = serializers.SerializerMethodField()
    stock_por_bodega = serializers.SerializerMethodField()
    bajo_minimo = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = ["id_material", "codigo", "nombre", "categoria", "categoria_nombre",
                  "unidad_medida", "stock_minimo", "costo_vigente_uf", "stock_total",
                  "stock_por_bodega", "bajo_minimo", "activo"]

    def get_stock_total(self, material) -> str:
        return str(MovimientoInventario.stock_actual(material))

    def get_stock_por_bodega(self, material) -> dict:
        return {
            str(b.pk): str(MovimientoInventario.stock_actual(material, b))
            for b in Bodega.objects.filter(activo=True)
        }

    def get_bajo_minimo(self, material) -> bool:
        return MovimientoInventario.stock_actual(material) < material.stock_minimo
