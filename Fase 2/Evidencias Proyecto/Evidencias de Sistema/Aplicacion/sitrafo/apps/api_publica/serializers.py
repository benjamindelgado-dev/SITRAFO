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
