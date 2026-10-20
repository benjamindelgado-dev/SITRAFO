"""Formato de las respuestas de la API publica (tambien documenta el esquema)."""
from rest_framework import serializers


class EstadoSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()


class EtapaSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    completada = serializers.BooleanField()
    actual = serializers.BooleanField()
    fecha = serializers.DateTimeField(allow_null=True)


class ProductoSerializer(serializers.Serializer):
    orden_trabajo = serializers.CharField(help_text="Numero de la orden de trabajo.")
    modelo = serializers.CharField()
    cantidad = serializers.IntegerField()
    estado = serializers.CharField()
    avance_pct = serializers.FloatField()


class EntregaSerializer(serializers.Serializer):
    fecha_estimada = serializers.DateField(allow_null=True)
    origen = serializers.CharField(
        allow_null=True,
        help_text="'comprometida' si viene de la cotizacion; 'calculada' si se obtuvo "
                  "sumando el plazo en dias habiles.",
    )
    dias_habiles_restantes = serializers.IntegerField(allow_null=True)
    considera_feriados = serializers.BooleanField(
        allow_null=True, help_text="Falso si faltan feriados cargados para el periodo.",
    )
    atrasado = serializers.BooleanField()


class HistorialSerializer(serializers.Serializer):
    fecha_hora = serializers.DateTimeField()
    documento = serializers.CharField()
    estado = serializers.CharField()


class SeguimientoSerializer(serializers.Serializer):
    numero = serializers.CharField(help_text="Numero de la orden de compra.")
    estado = EstadoSerializer()
    anulado = serializers.BooleanField()
    fecha_pedido = serializers.DateField()
    etapa_actual = serializers.CharField()
    avance_pct = serializers.IntegerField(help_text="Avance general del pedido (0 a 100).")
    etapas = EtapaSerializer(many=True)
    productos = ProductoSerializer(many=True)
    entrega = EntregaSerializer()
    historial = HistorialSerializer(many=True)
    consultado_en = serializers.DateTimeField()


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


# --------------------------------------------------------------------------
# Cotizador
# --------------------------------------------------------------------------
class ModeloCatalogoSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    familia = serializers.CharField(source="familia.nombre")
    descripcion = serializers.CharField()


class ItemEntradaSerializer(serializers.Serializer):
    modelo = serializers.CharField(help_text="Codigo del modelo (ej.: TD-100).")
    cantidad = serializers.IntegerField(min_value=1)

    def validate_cantidad(self, cantidad):
        from apps.comercial.services import validar_cantidad

        error = validar_cantidad(cantidad)
        if error:
            raise serializers.ValidationError(error)
        return cantidad

    def validate_modelo(self, codigo):
        from .cotizador import modelos_cotizables

        modelo = modelos_cotizables().filter(codigo__iexact=codigo.strip()).first()
        if modelo is None:
            raise serializers.ValidationError(
                f"No existe un modelo publicado con el codigo '{codigo}'.")
        return modelo


class EstimacionEntradaSerializer(serializers.Serializer):
    items = ItemEntradaSerializer(many=True, help_text="Entre 1 y 10 modelos.")

    def validate_items(self, items):
        from .cotizador import MAXIMO_ITEMS

        if not 1 <= len(items) <= MAXIMO_ITEMS:
            raise serializers.ValidationError(
                f"Debe indicar entre 1 y {MAXIMO_ITEMS} modelos.")
        codigos = [i["modelo"].codigo for i in items]
        if len(codigos) != len(set(codigos)):
            raise serializers.ValidationError(
                "Un modelo aparece mas de una vez: sume las cantidades en un solo item.")
        return items


class ModeloResumenSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    familia = serializers.CharField()


class ItemEstimadoSerializer(serializers.Serializer):
    modelo = ModeloResumenSerializer()
    cantidad = serializers.IntegerField()
    disponible = serializers.BooleanField(
        help_text="Falso si el modelo se cotiza segun especificacion (sin precio referencial).")
    precio_unitario_uf = serializers.DecimalField(14, 2, allow_null=True)
    subtotal_uf = serializers.DecimalField(14, 2, allow_null=True)
    subtotal_clp = serializers.DecimalField(16, 0, allow_null=True)
    solicitar_presupuesto = serializers.URLField(
        help_text="Enlace al formulario de solicitud con el modelo y la cantidad.")


class IndicadorSerializer(serializers.Serializer):
    valor = serializers.DecimalField(12, 2, allow_null=True)
    fecha = serializers.DateField(allow_null=True)


class IndicadoresSerializer(serializers.Serializer):
    uf = IndicadorSerializer()
    dolar = IndicadorSerializer()


class PlazoSerializer(serializers.Serializer):
    dias_habiles = serializers.IntegerField()
    fecha_entrega_estimada = serializers.DateField()
    considera_feriados = serializers.BooleanField()


class EstimacionSerializer(serializers.Serializer):
    items = ItemEstimadoSerializer(many=True)
    total_uf = serializers.DecimalField(16, 2, allow_null=True)
    total_clp = serializers.DecimalField(18, 0, allow_null=True)
    total_usd = serializers.DecimalField(16, 2, allow_null=True)
    indicadores = IndicadoresSerializer()
    plazo = PlazoSerializer()
    valida_hasta = serializers.DateField()
    avisos = serializers.ListField(child=serializers.CharField())
    consultado_en = serializers.DateTimeField()
