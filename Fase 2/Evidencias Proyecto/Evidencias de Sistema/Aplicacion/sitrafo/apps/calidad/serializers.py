"""Serializadores del control de calidad."""

from rest_framework import serializers

from apps.catalogo.models import ModeloProducto

from . import services
from .models import ControlCalidad, NoConformidad, ProtocoloCalidad, PuntoControl


class PuntoControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntoControl
        fields = ["id_punto", "secuencia", "nombre", "tipo_ensayo", "unidad",
                  "valor_esperado", "tolerancia_inf", "tolerancia_sup", "obligatorio"]


class ProtocoloSerializer(serializers.ModelSerializer):
    modelo_codigo = serializers.CharField(source="modelo.codigo", read_only=True)
    modelo_nombre = serializers.CharField(source="modelo.nombre", read_only=True)
    puntos = PuntoControlSerializer(many=True, read_only=True)
    aplicado = serializers.SerializerMethodField()

    class Meta:
        model = ProtocoloCalidad
        fields = ["id_protocolo", "modelo", "modelo_codigo", "modelo_nombre", "nombre",
                  "version", "norma_referencia", "activo", "aplicado", "puntos"]

    def get_aplicado(self, protocolo) -> bool:
        return protocolo.controles.exists()


class PuntoEntradaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=120)
    tipo_ensayo = serializers.CharField(max_length=60, required=False, allow_blank=True)
    unidad = serializers.CharField(max_length=20, required=False, allow_blank=True)
    valor_esperado = serializers.DecimalField(max_digits=14, decimal_places=4,
                                              required=False, allow_null=True)
    tolerancia_inf = serializers.DecimalField(max_digits=14, decimal_places=4,
                                              required=False, allow_null=True)
    tolerancia_sup = serializers.DecimalField(max_digits=14, decimal_places=4,
                                              required=False, allow_null=True)
    obligatorio = serializers.BooleanField(required=False, default=True)


class ProtocoloEntradaSerializer(serializers.Serializer):
    modelo = serializers.PrimaryKeyRelatedField(queryset=ModeloProducto.objects.all())
    nombre = serializers.CharField(max_length=120)
    norma_referencia = serializers.CharField(max_length=80, required=False,
                                             allow_blank=True, default="")
    puntos = PuntoEntradaSerializer(many=True)


class NoConformidadSerializer(serializers.ModelSerializer):
    punto = serializers.CharField(source="resultado.punto.nombre", read_only=True)
    valor_medido = serializers.DecimalField(source="resultado.valor_medido", max_digits=14,
                                            decimal_places=4, read_only=True)
    orden_trabajo = serializers.CharField(source="resultado.control.orden_trabajo.numero",
                                          read_only=True)
    responsable_nombre = serializers.CharField(source="responsable.username", read_only=True)
    cerrada_por = serializers.CharField(source="usuario_cierre.username", read_only=True,
                                        default=None)

    class Meta:
        model = NoConformidad
        fields = ["id_no_conformidad", "orden_trabajo", "punto", "valor_medido",
                  "descripcion", "severidad", "estado", "responsable_nombre",
                  "accion_correctiva", "abierta_en", "cerrada_en", "cerrada_por"]


class ControlCalidadSerializer(serializers.ModelSerializer):
    orden_trabajo_numero = serializers.CharField(source="orden_trabajo.numero", read_only=True)
    protocolo_nombre = serializers.SerializerMethodField()
    inspector_nombre = serializers.CharField(source="inspector.username", read_only=True)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    puntos = serializers.SerializerMethodField()

    class Meta:
        model = ControlCalidad
        fields = ["id_control", "orden_trabajo", "orden_trabajo_numero", "protocolo",
                  "protocolo_nombre", "inspector_nombre", "fecha_hora", "estado",
                  "estado_nombre", "puntos"]

    def get_protocolo_nombre(self, control) -> str:
        return str(control.protocolo)

    def get_puntos(self, control) -> list[dict]:
        filas = []
        for fila in services.estado_de_puntos(control):
            punto, resultado, nc = fila["punto"], fila["resultado"], fila["no_conformidad"]
            filas.append({
                **PuntoControlSerializer(punto).data,
                "valor_medido": str(resultado.valor_medido) if resultado else None,
                "conforme": resultado.conforme if resultado else None,
                "mediciones": control.resultados.filter(punto=punto).count(),
                "no_conformidad": ({"id": nc.pk, "estado": nc.estado,
                                    "severidad": nc.severidad} if nc else None),
            })
        return filas


class IniciarControlSerializer(serializers.Serializer):
    orden_trabajo = serializers.IntegerField()
    protocolo = serializers.IntegerField()


class ResultadoEntradaSerializer(serializers.Serializer):
    punto = serializers.IntegerField()
    valor = serializers.DecimalField(max_digits=14, decimal_places=4)
    observacion = serializers.CharField(required=False, allow_blank=True, default="")
    severidad = serializers.ChoiceField(choices=NoConformidad.Severidad.choices,
                                        required=False, default="mayor")
    descripcion = serializers.CharField(required=False, allow_blank=True, default="")


