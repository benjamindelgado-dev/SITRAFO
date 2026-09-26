"""Serializadores del inventario."""
from decimal import Decimal

from rest_framework import serializers

from .models import Bodega, CategoriaMaterial, Material, MovimientoInventario, Proveedor


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


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaMaterial
        fields = ["id_categoria", "nombre", "activo"]


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ["id_proveedor", "rut", "razon_social", "email", "telefono", "activo"]


class MaterialEntradaSerializer(serializers.ModelSerializer):
    """Alta y edicion de materiales; el costo abre una nueva vigencia de precio."""

    costo_uf = serializers.DecimalField(max_digits=12, decimal_places=4, required=False,
                                        allow_null=True, min_value=Decimal("0"))

    class Meta:
        model = Material
        fields = ["categoria", "codigo", "nombre", "unidad_medida", "stock_minimo",
                  "activo", "costo_uf"]


class RecepcionSerializer(serializers.Serializer):
    bodega = serializers.PrimaryKeyRelatedField(queryset=Bodega.objects.filter(activo=True))
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=4)
    costo_unitario_uf = serializers.DecimalField(max_digits=12, decimal_places=4,
                                                 required=False, allow_null=True)
    proveedor = serializers.PrimaryKeyRelatedField(
        queryset=Proveedor.objects.filter(activo=True), required=False, allow_null=True)
    documento = serializers.CharField(required=False, allow_blank=True, default="")
    actualizar_precio = serializers.BooleanField(required=False, default=False)


class AjusteSerializer(serializers.Serializer):
    bodega = serializers.PrimaryKeyRelatedField(queryset=Bodega.objects.filter(activo=True))
    conteo_fisico = serializers.DecimalField(max_digits=12, decimal_places=4)
    motivo = serializers.CharField()
