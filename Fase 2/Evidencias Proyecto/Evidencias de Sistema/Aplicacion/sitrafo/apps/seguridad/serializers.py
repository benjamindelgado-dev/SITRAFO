"""Serializadores de la administracion de usuarios internos."""
from rest_framework import serializers

from .models import Rol, Usuario


class RolSerializer(serializers.ModelSerializer):
    cantidad_permisos = serializers.IntegerField(source="permisos_asignados.count",
                                                 read_only=True)

    class Meta:
        model = Rol
        fields = ["id_rol", "nombre", "descripcion", "activo", "cantidad_permisos"]


class UsuarioInternoSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    empleado = serializers.SerializerMethodField()
    es_superusuario = serializers.BooleanField(source="is_superuser", read_only=True)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id_usuario", "username", "email", "estado", "estado_nombre",
                  "es_superusuario", "roles", "empleado", "ultimo_acceso", "creado_en"]

    def get_roles(self, usuario) -> list[dict]:
        return [{"id_rol": r.id_rol, "nombre": r.nombre} for r in usuario.roles.all()]

    def get_empleado(self, usuario) -> dict | None:
        empleado = getattr(usuario, "empleado", None)
        if empleado is None:
            return None
        return {"id_empleado": empleado.pk, "nombre": empleado.nombre,
                "cargo": empleado.cargo}


class UsuarioEntradaSerializer(serializers.Serializer):
    username = serializers.RegexField(r"^[\w.@+-]+$", max_length=60, required=False,
                                      error_messages={"invalid": "Use letras, numeros "
                                                      "y . @ + - _ sin espacios."})
    email = serializers.EmailField(max_length=150, required=False)
    roles = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), many=True,
                                               required=False)
    empleado = serializers.IntegerField(required=False, allow_null=True)
    clave = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate_username(self, valor):
        if Usuario.objects.filter(username__iexact=valor).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese nombre.")
        return valor

    def validate_email(self, valor):
        existente = Usuario.objects.filter(email__iexact=valor)
        if self.instance is not None:
            existente = existente.exclude(pk=self.instance.pk)
        if existente.exists():
            raise serializers.ValidationError("Ese correo ya esta en uso.")
        return valor
