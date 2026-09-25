"""Serializadores de la ejecucion productiva."""
from decimal import Decimal

from rest_framework import serializers

from apps.comercial.serializers import HistorialSerializer

from .models import Empleado, OrdenTrabajo, RegistroHoraHombre, TareaOT


class EmpleadoSerializer(serializers.ModelSerializer):
    tarifa_vigente_uf = serializers.SerializerMethodField()
    username = serializers.CharField(source="usuario.username", read_only=True, default=None)

    class Meta:
        model = Empleado
        fields = ["id_empleado", "rut", "nombre", "cargo", "activo", "username",
                  "tarifa_vigente_uf"]

    def get_tarifa_vigente_uf(self, empleado):
        tarifa = empleado.tarifa_vigente_a()
        return str(tarifa.valor_hora_uf) if tarifa else None


class RegistroHoraSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="empleado.nombre", read_only=True)
    costo_total_uf = serializers.DecimalField(max_digits=12, decimal_places=4,
                                              read_only=True)

    class Meta:
        model = RegistroHoraHombre
        fields = ["id_registro", "empleado", "empleado_nombre", "fecha", "horas",
                  "valor_hora_uf", "costo_total_uf", "anulado"]


class TareaSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source="empleado.nombre", read_only=True,
                                            default=None)
    horas_registradas = serializers.SerializerMethodField()
    orden_trabajo_numero = serializers.CharField(source="orden_trabajo.numero",
                                                 read_only=True)
    modelo_nombre = serializers.CharField(source="orden_trabajo.modelo.nombre",
                                          read_only=True)
    registros = RegistroHoraSerializer(source="registros_hora", many=True, read_only=True)

    class Meta:
        model = TareaOT
        fields = ["id_tarea", "orden_trabajo", "orden_trabajo_numero", "modelo_nombre",
                  "nombre", "secuencia", "horas_estimadas", "horas_registradas",
                  "estado", "empleado", "empleado_nombre", "registros"]

    def get_horas_registradas(self, tarea) -> str:
        total = sum((r.horas for r in tarea.registros_hora.all() if not r.anulado),
                    Decimal("0"))
        return str(total)


class OrdenTrabajoSerializer(serializers.ModelSerializer):
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)
    estado_codigo = serializers.CharField(source="estado.codigo", read_only=True)
    modelo_nombre = serializers.CharField(source="modelo.nombre", read_only=True)
    orden_compra_numero = serializers.CharField(source="orden_compra.numero", read_only=True)
    cliente_nombre = serializers.CharField(source="orden_compra.cliente.razon_social",
                                           read_only=True)
    costo_materiales_uf = serializers.DecimalField(max_digits=14, decimal_places=4,
                                                   read_only=True)
    costo_hh_uf = serializers.DecimalField(max_digits=14, decimal_places=4, read_only=True)
    desviacion_pct = serializers.DecimalField(max_digits=8, decimal_places=2,
                                              read_only=True)
    desviacion_requiere_justificacion = serializers.BooleanField(read_only=True)
    tareas = TareaSerializer(many=True, read_only=True)
    historial = HistorialSerializer(many=True, read_only=True)
    impedimentos_cierre = serializers.SerializerMethodField()

    class Meta:
        model = OrdenTrabajo
        fields = ["id_orden_trabajo", "numero", "orden_compra", "orden_compra_numero",
                  "cliente_nombre", "modelo", "modelo_nombre", "cantidad", "estado",
                  "estado_nombre", "estado_codigo", "costo_estimado_uf", "costo_real_uf",
                  "costo_materiales_uf", "costo_hh_uf", "desviacion_pct",
                  "desviacion_requiere_justificacion", "avance_pct", "fecha_inicio",
                  "fecha_cierre", "impedimentos_cierre", "tareas", "historial"]
        read_only_fields = fields

    def get_impedimentos_cierre(self, ot) -> list[str]:
        if ot.estado.codigo in ("cerrada", "anulada", "planificada"):
            return []
        return ot.puede_cerrarse()[1]


# -- Entradas de las acciones ----------------------------------------------
class RegistrarHorasSerializer(serializers.Serializer):
    horas = serializers.DecimalField(max_digits=6, decimal_places=2,
                                     min_value=Decimal("0.25"))
    fecha = serializers.DateField(required=False)
    empleado = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(activo=True), required=False
    )


class RegistrarConsumoSerializer(serializers.Serializer):
    material = serializers.IntegerField()
    bodega = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=4,
                                        min_value=Decimal("0.0001"))
    empleado = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.filter(activo=True), required=False
    )
