"""Vistas de la API para el dominio comercial."""
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.common.mixins import FiltradoPorClienteMixin
from apps.common.permissions import CuentaOperativa, EsUsuarioInterno
from apps.pagos.services.cobros import ErrorCobro, emitir_anticipo

from .models import (
    Cotizacion,
    CotizacionHistorial,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraHistorial,
    OrdenCompraLinea,
    SolicitudPresupuesto,
)
from .serializers import (
    CotizacionSerializer,
    EstadoDocumentoSerializer,
    OrdenCompraSerializer,
    SolicitudPresupuestoSerializer,
)


class EstadoDocumentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstadoDocumento.objects.all()
    serializer_class = EstadoDocumentoSerializer
    permission_classes = [CuentaOperativa]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo_documento"]
    pagination_class = None


class SolicitudPresupuestoViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    """Solicitudes de presupuesto (CU-COM-01, CU-COM-02)."""

    queryset = (
        SolicitudPresupuesto.objects.select_related("cliente", "modelo", "estado")
        .prefetch_related("especificaciones__parametro", "historial")
    )
    serializer_class = SolicitudPresupuestoSerializer
    permission_classes = [CuentaOperativa]
    modulo_permiso = "solicitud"
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "cliente", "ejecutivo"]
    search_fields = ["numero"]
    ordering_fields = ["creado_en", "numero"]

    @action(detail=True, methods=["post"], permission_classes=[CuentaOperativa, EsUsuarioInterno])
    def asignar(self, request, pk=None):
        """Asigna la solicitud a un ejecutivo comercial (CU-COM-02)."""
        solicitud = self.get_object()
        estado_anterior = solicitud.estado
        solicitud.ejecutivo = request.user
        solicitud.estado = EstadoDocumento.objects.get(
            tipo_documento="solicitud", codigo="asignada"
        )
        solicitud.save(update_fields=["ejecutivo", "estado"])

        from .models import SolicitudHistorial

        SolicitudHistorial.objects.create(
            solicitud=solicitud,
            estado_anterior=estado_anterior,
            estado_nuevo=solicitud.estado,
            usuario=request.user,
            observacion=f"Asignada a {request.user.username}.",
        )
        return Response(self.get_serializer(solicitud).data)


class CotizacionViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    """Cotizaciones. Incluye la aceptacion y el rechazo del cliente."""

    queryset = (
        Cotizacion.objects.select_related("cliente", "estado", "solicitud")
        .prefetch_related("lineas__modelo", "historial")
    )
    serializer_class = CotizacionSerializer
    permission_classes = [CuentaOperativa]
    modulo_permiso = "cotizacion"
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "cliente"]
    search_fields = ["numero"]
    ordering_fields = ["creado_en", "vence_el"]

    def _cambiar_estado(self, cotizacion, codigo, usuario, observacion=""):
        anterior = cotizacion.estado
        cotizacion.estado = EstadoDocumento.objects.get(
            tipo_documento="cotizacion", codigo=codigo
        )
        cotizacion.save(update_fields=["estado"])
        CotizacionHistorial.objects.create(
            cotizacion=cotizacion,
            estado_anterior=anterior,
            estado_nuevo=cotizacion.estado,
            usuario=usuario,
            observacion=observacion,
        )
        return cotizacion

    @action(detail=True, methods=["post"])
    def aceptar(self, request, pk=None):
        """
        Aceptacion por el cliente (CU-COM-08).

        La vigencia se vuelve a verificar al confirmar, no solo al desplegar
        la vista: una cotizacion puede vencer entre ambos momentos.
        """
        cotizacion = self.get_object()

        if cotizacion.estado.codigo != "emitida":
            return Response(
                {"detalle": "Solo puede aceptarse una cotizacion emitida."},
                status=status.HTTP_409_CONFLICT,
            )

        if not cotizacion.esta_vigente:
            self._cambiar_estado(
                cotizacion, "vencida", request.user,
                "Vencida al momento de intentar aceptarla.",
            )
            return Response(
                {
                    "detalle": "La cotizacion vencio el "
                               f"{cotizacion.vence_el}. Solicite una nueva.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        self._cambiar_estado(
            cotizacion, "aceptada", request.user, "Aceptada por el cliente."
        )
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        """Rechazo por el cliente, con motivo (CU-COM-08, flujo A5)."""
        cotizacion = self.get_object()

        if cotizacion.estado.codigo != "emitida":
            return Response(
                {"detalle": "Solo puede rechazarse una cotizacion emitida."},
                status=status.HTTP_409_CONFLICT,
            )

        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return Response(
                {"motivo": "Debe indicar el motivo del rechazo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self._cambiar_estado(cotizacion, "rechazada", request.user, motivo)
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"],
            permission_classes=[CuentaOperativa, EsUsuarioInterno])
    def emitir(self, request, pk=None):
        """Emision al cliente (CU-COM-07). Verifica la aprobacion previa."""
        cotizacion = self.get_object()

        if cotizacion.requiere_aprobacion and cotizacion.estado.codigo != "en_aprobacion":
            return Response(
                {
                    "detalle": "El descuento supera el umbral autorizado: "
                               "requiere aprobacion interna antes de emitir.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        cotizacion.recalcular_total()
        self._cambiar_estado(
            cotizacion, "emitida", request.user, "Emitida al cliente."
        )
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"],
            permission_classes=[CuentaOperativa, EsUsuarioInterno])
    def generar_orden_compra(self, request, pk=None):
        """
        Genera la orden de compra desde una cotizacion aceptada (RN-06).

        Es el unico camino para crear una orden de compra.
        """
        cotizacion = self.get_object()

        if cotizacion.estado.codigo != "aceptada":
            return Response(
                {"detalle": "Solo una cotizacion aceptada origina una orden de compra."},
                status=status.HTTP_409_CONFLICT,
            )

        if cotizacion.ordenes_compra.exists():
            return Response(
                {"detalle": "Esta cotizacion ya tiene una orden de compra."},
                status=status.HTTP_409_CONFLICT,
            )

        estado_oc = EstadoDocumento.objects.get(
            tipo_documento="orden_compra", codigo="pendiente"
        )
        orden = OrdenCompra.objects.create(
            numero=OrdenCompra.generar_numero(),
            cotizacion=cotizacion,
            cliente=cotizacion.cliente,
            estado=estado_oc,
            total_uf=cotizacion.total_uf,
        )
        for linea in cotizacion.lineas.all():
            OrdenCompraLinea.objects.create(
                orden_compra=orden,
                cotizacion_linea=linea,
                cantidad=linea.cantidad,
                precio_uf=linea.precio_uf,
            )
        OrdenCompraHistorial.objects.create(
            orden_compra=orden,
            estado_nuevo=estado_oc,
            usuario=request.user,
            observacion=f"Generada desde la cotizacion {cotizacion.numero}.",
        )

        # RN-15: el anticipo nace con la orden. Si no hay UF disponible para
        # congelarlo, la orden igual se crea y el anticipo se emite despues
        # con el comando emitir_cobros (degradacion controlada, RF-INT-03).
        try:
            emitir_anticipo(orden)
        except ErrorCobro:
            pass

        return Response(
            OrdenCompraSerializer(orden).data, status=status.HTTP_201_CREATED
        )


class OrdenCompraViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    queryset = (
        OrdenCompra.objects.select_related("cliente", "estado", "cotizacion")
        .prefetch_related("lineas__cotizacion_linea__modelo", "historial")
    )
    serializer_class = OrdenCompraSerializer
    permission_classes = [CuentaOperativa]
    modulo_permiso = "orden_compra"
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "cliente"]
    search_fields = ["numero"]

    @action(detail=True, methods=["post"],
            permission_classes=[CuentaOperativa, EsUsuarioInterno])
    def confirmar(self, request, pk=None):
        """Confirma la orden, habilitando la generacion de la OT (RN-07)."""
        orden = self.get_object()
        if orden.estado.codigo != "pendiente":
            return Response(
                {"detalle": "Solo una orden pendiente puede confirmarse."},
                status=status.HTTP_409_CONFLICT,
            )
        anterior = orden.estado
        orden.estado = EstadoDocumento.objects.get(
            tipo_documento="orden_compra", codigo="confirmada"
        )
        orden.save(update_fields=["estado"])
        OrdenCompraHistorial.objects.create(
            orden_compra=orden,
            estado_anterior=anterior,
            estado_nuevo=orden.estado,
            usuario=request.user,
            observacion="Orden confirmada.",
        )
        return Response(self.get_serializer(orden).data)
