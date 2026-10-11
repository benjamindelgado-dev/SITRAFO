"""Serializadores del dominio de configuracion."""
from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from .models import AvisoSitio, Feriado, LogIntegracion, ParametroSistema


class ParametroSistemaSerializer(serializers.ModelSerializer):
    valor_tipado = serializers.SerializerMethodField()
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = ParametroSistema
        fields = ["id_parametro_sistema", "clave", "valor", "valor_tipado",
                  "tipo_dato", "ambito", "descripcion", "usuario",
                  "usuario_nombre", "modificado_en"]
        read_only_fields = ["clave", "tipo_dato", "ambito", "modificado_en", "usuario"]

    def get_valor_tipado(self, obj):
        return obj.valor_tipado

    def validate_valor(self, valor):
        """Valida el valor segun el tipo y el rango del parametro."""
        from .parametros import validar_valor

        parametro = self.instance
        if parametro is None:
            return valor
        valor = valor.strip()
        if parametro.tipo_dato == ParametroSistema.TipoDato.NUMERICO:
            valor = valor.replace(",", ".")
            error = validar_valor(parametro.clave, valor)
            if error is None:
                try:
                    Decimal(valor)
                except InvalidOperation:
                    error = "Ingrese un numero."
            if error:
                raise serializers.ValidationError(error)
        elif parametro.tipo_dato == ParametroSistema.TipoDato.BOOLEANO:
            if valor.lower() not in ("true", "false"):
                raise serializers.ValidationError("Use true o false.")
        return valor


class AvisoSitioSerializer(serializers.ModelSerializer):
    esta_publicado = serializers.BooleanField(read_only=True)

    class Meta:
        model = AvisoSitio
        fields = ["id_aviso", "titulo", "cuerpo", "tipo", "vigente_desde",
                  "vigente_hasta", "activo", "esta_publicado", "usuario"]
        read_only_fields = ["usuario"]


class FeriadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feriado
        fields = ["id_feriado", "fecha", "nombre", "tipo", "obtenido_en"]


class LogIntegracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogIntegracion
        fields = ["id_log", "servicio", "endpoint", "metodo", "codigo_respuesta",
                  "latencia_ms", "exitoso", "mensaje_error", "fecha_hora"]
