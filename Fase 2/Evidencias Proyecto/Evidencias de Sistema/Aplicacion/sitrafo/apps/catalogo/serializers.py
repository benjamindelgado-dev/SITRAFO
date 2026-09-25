"""Serializadores del dominio de catalogo."""
from decimal import Decimal

from rest_framework import serializers

from .models import (
    BomModelo,
    FamiliaProducto,
    ModeloParametro,
    ModeloProducto,
    ParametroTecnico,
    TareaEstandarModelo,
    ValorParametro,
)


class ValorParametroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValorParametro
        fields = ["id_valor", "valor", "orden"]


class ParametroTecnicoSerializer(serializers.ModelSerializer):
    valores = ValorParametroSerializer(many=True, read_only=True)

    class Meta:
        model = ParametroTecnico
        fields = ["id_parametro", "codigo", "nombre", "unidad",
                  "tipo_dato", "obligatorio", "valores"]


class FamiliaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamiliaProducto
        fields = ["id_familia", "nombre", "descripcion", "activo"]


class ModeloParametroSerializer(serializers.ModelSerializer):
    parametro = ParametroTecnicoSerializer(read_only=True)

    class Meta:
        model = ModeloParametro
        fields = ["parametro", "valor_defecto", "obligatorio"]


class BomModeloSerializer(serializers.ModelSerializer):
    material_codigo = serializers.CharField(source="material.codigo", read_only=True)
    material_nombre = serializers.CharField(source="material.nombre", read_only=True)
    unidad = serializers.CharField(source="material.unidad_medida", read_only=True)

    class Meta:
        model = BomModelo
        fields = ["id_bom", "material", "material_codigo", "material_nombre",
                  "unidad", "cantidad", "observacion"]


class TareaEstandarSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaEstandarModelo
        fields = ["id_tarea_estandar", "nombre", "secuencia", "horas_estimadas"]


class ModeloProductoListaSerializer(serializers.ModelSerializer):
    """Version liviana para el listado del catalogo web."""

    familia_nombre = serializers.CharField(source="familia.nombre", read_only=True)
    precio_vigente = serializers.DecimalField(
        max_digits=12, decimal_places=4, read_only=True
    )

    class Meta:
        model = ModeloProducto
        fields = ["id_modelo", "codigo", "nombre", "familia",
                  "familia_nombre", "precio_vigente", "publicado"]


class ModeloProductoDetalleSerializer(serializers.ModelSerializer):
    """Ficha completa del modelo."""

    familia = FamiliaProductoSerializer(read_only=True)
    parametros_asignados = ModeloParametroSerializer(many=True, read_only=True)
    materiales = BomModeloSerializer(many=True, read_only=True)
    tareas_estandar = TareaEstandarSerializer(many=True, read_only=True)
    precio_vigente = serializers.DecimalField(
        max_digits=12, decimal_places=4, read_only=True
    )
    horas_estandar_totales = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = ModeloProducto
        fields = ["id_modelo", "codigo", "nombre", "descripcion", "familia",
                  "publicado", "activo", "precio_vigente",
                  "horas_estandar_totales", "parametros_asignados",
                  "materiales", "tareas_estandar"]


class ParametroDelModeloEntrada(serializers.Serializer):
    parametro = serializers.PrimaryKeyRelatedField(queryset=ParametroTecnico.objects.all())
    valor_defecto = serializers.CharField(required=False, allow_blank=True, default="")
    obligatorio = serializers.BooleanField(required=False, default=False)

    def to_internal_value(self, datos):
        valor = super().to_internal_value(datos)
        valor["parametro"] = valor["parametro"].pk
        return valor


class ModeloProductoEscrituraSerializer(serializers.ModelSerializer):
    """
    Alta y edicion del modelo desde la aplicacion de escritorio.

    El precio base es opcional y exige permiso sobre precios: lo verifica la
    vista, porque en la matriz son modulos distintos.
    """

    parametros = ParametroDelModeloEntrada(many=True, required=False)
    precio_base_uf = serializers.DecimalField(
        max_digits=12, decimal_places=4, required=False, allow_null=True,
        min_value=Decimal("0"),
    )

    class Meta:
        model = ModeloProducto
        fields = ["familia", "codigo", "nombre", "descripcion", "parametros",
                  "precio_base_uf"]
