"""Serializadores del dominio comercial."""
from decimal import Decimal

from rest_framework import serializers

from apps.clientes.models import Cliente

from .models import (
    Cotizacion,
    CotizacionHistorial,
    CotizacionLinea,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraLinea,
    SolicitudEspecificacion,
    SolicitudHistorial,
    SolicitudPresupuesto,
)


class EstadoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoDocumento
        fields = ["id_estado", "tipo_documento", "codigo", "nombre", "es_final"]


class HistorialSerializer(serializers.Serializer):
    """Historial de estados, comun a los documentos del flujo (RN-14)."""

    estado_anterior = serializers.CharField(
        source="estado_anterior.nombre", default=None, read_only=True
    )
    estado_nuevo = serializers.CharField(source="estado_nuevo.nombre", read_only=True)
    usuario = serializers.CharField(source="usuario.username", read_only=True)
    fecha_hora = serializers.DateTimeField(read_only=True)
    observacion = serializers.CharField(read_only=True)


class SolicitudEspecificacionSerializer(serializers.ModelSerializer):
    parametro_nombre = serializers.CharField(
        source="parametro.nombre", read_only=True
    )
    unidad = serializers.CharField(source="parametro.unidad", read_only=True)

    class Meta:
        model = SolicitudEspecificacion
        fields = ["parametro", "parametro_nombre", "unidad", "valor"]


class SolicitudPresupuestoSerializer(serializers.ModelSerializer):
    especificaciones = SolicitudEspecificacionSerializer(many=True, required=False)
    # Para una cuenta web el cliente lo asigna el sistema desde el usuario
    # autenticado, nunca el propio payload (RN-16).
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(), required=False
    )
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)
    estado_codigo = serializers.CharField(source="estado.codigo", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.razon_social", read_only=True)
    ejecutivo_nombre = serializers.CharField(
        source="ejecutivo.username", read_only=True, default=None
    )
    modelo_nombre = serializers.CharField(source="modelo.nombre", read_only=True)
    historial = HistorialSerializer(many=True, read_only=True)

    class Meta:
        model = SolicitudPresupuesto
        fields = ["id_solicitud", "numero", "cliente", "cliente_nombre", "modelo",
                  "modelo_nombre", "direccion", "cantidad", "fecha_deseada", "estado",
                  "estado_nombre", "estado_codigo", "ejecutivo", "ejecutivo_nombre",
                  "creado_en",
                  "especificaciones", "historial"]
        read_only_fields = ["numero", "creado_en", "estado", "ejecutivo"]

    def validate(self, attrs):
        usuario = self.context["request"].user
        if not usuario.es_interno:
            if usuario.cliente_id is None:
                raise serializers.ValidationError(
                    "La cuenta no tiene un cliente asociado."
                )
            attrs["cliente_id"] = usuario.cliente_id
            attrs.pop("cliente", None)
        elif not attrs.get("cliente"):
            raise serializers.ValidationError(
                {"cliente": "Un usuario interno debe indicar el cliente."}
            )
        return attrs

    def create(self, validated_data):
        """
        Crea la solicitud con su especificacion tecnica y su estado inicial.

        El numero correlativo y el estado los asigna el sistema, no el cliente.
        """
        especificaciones = validated_data.pop("especificaciones", [])
        validated_data["numero"] = SolicitudPresupuesto.generar_numero()
        validated_data["estado"] = EstadoDocumento.objects.get(
            tipo_documento="solicitud", codigo="recibida"
        )
        solicitud = SolicitudPresupuesto.objects.create(**validated_data)

        for item in especificaciones:
            SolicitudEspecificacion.objects.create(solicitud=solicitud, **item)

        SolicitudHistorial.objects.create(
            solicitud=solicitud,
            estado_nuevo=solicitud.estado,
            usuario=self.context["request"].user,
            observacion="Solicitud recibida desde la aplicacion web.",
        )
        return solicitud


class CotizacionLineaSerializer(serializers.ModelSerializer):
    modelo_nombre = serializers.CharField(source="modelo.nombre", read_only=True)
    costo_estimado_uf = serializers.DecimalField(
        max_digits=12, decimal_places=4, read_only=True
    )

    class Meta:
        model = CotizacionLinea
        fields = ["id_linea", "modelo", "modelo_nombre", "cantidad",
                  "costo_material_uf", "costo_hh_uf", "costo_estimado_uf",
                  "margen_pct", "precio_uf"]


class CotizacionSerializer(serializers.ModelSerializer):
    lineas = CotizacionLineaSerializer(many=True, read_only=True)
    historial = HistorialSerializer(many=True, read_only=True)
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)
    estado_codigo = serializers.CharField(source="estado.codigo", read_only=True)
    cliente_nombre = serializers.CharField(
        source="cliente.razon_social", read_only=True
    )
    total_clp = serializers.DecimalField(
        max_digits=16, decimal_places=0, read_only=True
    )
    esta_vigente = serializers.BooleanField(read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)
    orden_compra = serializers.SerializerMethodField()

    def get_orden_compra(self, cotizacion) -> str | None:
        """Numero de la orden de compra generada, si existe (RN-06)."""
        orden = next(iter(cotizacion.ordenes_compra.all()), None)
        return orden.numero if orden else None

    class Meta:
        model = Cotizacion
        fields = ["id_cotizacion", "numero", "version", "solicitud", "cliente",
                  "cliente_nombre", "estado", "estado_nombre", "estado_codigo", "ejecutivo",
                  "valor_uf", "fecha_valor_uf", "total_uf", "total_clp",
                  "descuento_pct", "plazo_dias_habiles", "fecha_entrega",
                  "vence_el", "esta_vigente", "dias_para_vencer", "orden_compra",
                  "creado_en", "lineas", "historial"]
        read_only_fields = ["numero", "version", "total_uf", "creado_en"]


class OrdenCompraLineaSerializer(serializers.ModelSerializer):
    modelo_nombre = serializers.CharField(
        source="cotizacion_linea.modelo.nombre", read_only=True
    )

    class Meta:
        model = OrdenCompraLinea
        fields = ["id_linea_oc", "cotizacion_linea", "modelo_nombre",
                  "cantidad", "precio_uf"]


class OrdenCompraSerializer(serializers.ModelSerializer):
    lineas = OrdenCompraLineaSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.razon_social", read_only=True)
    cotizacion_numero = serializers.CharField(source="cotizacion.numero", read_only=True)
    anticipo = serializers.SerializerMethodField()
    saldo = serializers.SerializerMethodField()
    estado_codigo = serializers.CharField(source="estado.codigo", read_only=True)
    ordenes_trabajo = serializers.SerializerMethodField()
    historial = HistorialSerializer(many=True, read_only=True)
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)
    monto_anticipo_uf = serializers.DecimalField(
        max_digits=14, decimal_places=4, read_only=True
    )
    monto_saldo_uf = serializers.DecimalField(
        max_digits=14, decimal_places=4, read_only=True
    )

    class Meta:
        model = OrdenCompra
        fields = ["id_orden_compra", "numero", "cotizacion", "cotizacion_numero",
                  "cliente", "cliente_nombre", "estado", "estado_nombre", "estado_codigo",
                  "total_uf",
                  "anticipo_pct", "monto_anticipo_uf", "monto_saldo_uf", "anticipo", "saldo",
                  "ordenes_trabajo",
                  "creado_en", "lineas", "historial"]
        read_only_fields = ["numero", "creado_en"]

    def get_ordenes_trabajo(self, orden) -> list[str]:
        return [ot.numero for ot in orden.ordenes_trabajo.all()]

    @staticmethod
    def _cobro(orden, tipo) -> dict | None:
        documento = next(
            (d for d in orden.documentos_cobro.all()
             if d.tipo == tipo and d.estado != "anulado"),
            None,
        )
        if documento is None:
            return None
        return {"numero": documento.numero, "estado": documento.estado,
                "monto_clp": str(documento.monto_clp),
                "vence_el": documento.vence_el.isoformat()}

    def get_anticipo(self, orden) -> dict | None:
        """Documento de cobro del anticipo y su estado de pago (RN-15)."""
        return self._cobro(orden, "anticipo")

    def get_saldo(self, orden) -> dict | None:
        """Cobro del saldo: se emite al cerrar la ultima orden de trabajo."""
        return self._cobro(orden, "saldo")


class CotizarSolicitudSerializer(serializers.Serializer):
    """Datos que el ejecutivo puede ajustar al elaborar la cotizacion."""

    precio_uf = serializers.DecimalField(
        max_digits=12, decimal_places=4, required=False, allow_null=True, min_value=Decimal("0")
    )
    margen_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0")
    )
    descuento_pct = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=0,
        min_value=Decimal("0"), max_value=Decimal("100"),
    )
    plazo_dias_habiles = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=365
    )
