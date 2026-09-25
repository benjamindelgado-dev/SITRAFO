"""Serializadores del dominio de clientes."""
from rest_framework import serializers

from .models import Cliente, Comuna, ContactoCliente, DireccionCliente, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id_region", "nombre", "codigo"]


class ComunaSerializer(serializers.ModelSerializer):
    region_nombre = serializers.CharField(source="region.nombre", read_only=True)

    class Meta:
        model = Comuna
        fields = ["id_comuna", "nombre", "region", "region_nombre"]


class ContactoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactoCliente
        fields = ["id_contacto", "cliente", "nombre", "cargo",
                  "email", "telefono", "principal"]


class DireccionClienteSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)
    direccion_completa = serializers.SerializerMethodField()

    class Meta:
        model = DireccionCliente
        fields = ["id_direccion", "cliente", "comuna", "comuna_nombre", "tipo",
                  "calle", "numero", "latitud", "longitud", "validada",
                  "direccion_completa"]
        read_only_fields = ["latitud", "longitud", "validada"]

    def get_direccion_completa(self, obj) -> str:
        return str(obj)


class ClienteSerializer(serializers.ModelSerializer):
    contactos = ContactoClienteSerializer(many=True, read_only=True)
    direcciones = DireccionClienteSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = ["id_cliente", "rut", "razon_social", "nombre_fantasia",
                  "tipo_persona", "giro", "estado", "creado_en",
                  "contactos", "direcciones"]
        read_only_fields = ["creado_en"]

    def validate_rut(self, valor):
        """El validador del modelo se ejecuta tambien en la API (RF-CLI-02)."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.common.validators import limpiar_rut, validar_rut

        try:
            validar_rut(valor)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return limpiar_rut(valor)
