"""Vistas de la API para el control de calidad."""
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa, PermisoPorRol
from apps.produccion.models import OrdenTrabajo

from . import services
from .models import ControlCalidad, NoConformidad, ProtocoloCalidad, PuntoControl
from .serializers import (
    ControlCalidadSerializer,
    IniciarControlSerializer,
    NoConformidadSerializer,
    ProtocoloEntradaSerializer,
    ProtocoloSerializer,
    ResultadoEntradaSerializer,
)


def _conflicto(error):
    return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)


class ProtocoloViewSet(viewsets.ReadOnlyModelViewSet):
    """Protocolos de calidad por modelo (CU-CAL-01, CU-CAL-02)."""

    serializer_class = ProtocoloSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "protocolo_calidad"
    permisos_alternativos = {
        # El inspector necesita ver los protocolos para ejecutar ensayos
        "list": ["protocolo_calidad.leer", "ensayo.leer"],
        "retrieve": ["protocolo_calidad.leer", "ensayo.leer"],
    }
    permisos_accion = {"create": "protocolo_calidad.crear",
                       "update": "protocolo_calidad.actualizar"}
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["modelo", "activo"]
    pagination_class = None

    def get_queryset(self):
        return (ProtocoloCalidad.objects.select_related("modelo")
                .prefetch_related("puntos").order_by("modelo__codigo", "nombre", "-version"))

    def _guardar(self, request, protocolo=None):
        entrada = ProtocoloEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            resultado = services.guardar_protocolo(
                request.user, modelo=datos["modelo"], nombre=datos["nombre"],
                norma_referencia=datos["norma_referencia"], puntos=datos["puntos"],
                protocolo=protocolo,
            )
        except services.ErrorCalidad as error:
            return _conflicto(error)
        return Response(ProtocoloSerializer(resultado).data,
                        status=status.HTTP_201_CREATED if protocolo is None or
                        resultado.pk != protocolo.pk else status.HTTP_200_OK)

    def create(self, request):
        return self._guardar(request)

    def update(self, request, pk=None):
        return self._guardar(request, self.get_object())


class ControlCalidadViewSet(viewsets.ReadOnlyModelViewSet):
    """Ejecucion de ensayos sobre ordenes en calidad (CU-CAL-03, CU-CAL-04)."""

    serializer_class = ControlCalidadSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "ensayo"
    permisos_accion = {"create": "ensayo.crear", "registrar_resultado": "ensayo.crear"}
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["orden_trabajo", "estado"]
    pagination_class = None

    def get_queryset(self):
        return (ControlCalidad.objects
                .select_related("orden_trabajo", "protocolo", "inspector")
                .prefetch_related("protocolo__puntos", "resultados__no_conformidad")
                .order_by("-fecha_hora"))

    def create(self, request):
        entrada = IniciarControlSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        ot = get_object_or_404(OrdenTrabajo, pk=entrada.validated_data["orden_trabajo"])
        protocolo = get_object_or_404(ProtocoloCalidad,
                                      pk=entrada.validated_data["protocolo"])
        try:
            control = services.iniciar_control(ot, protocolo, request.user)
        except services.ErrorCalidad as error:
            return _conflicto(error)
        return Response(self.get_serializer(control).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def registrar_resultado(self, request, pk=None):
        control = self.get_object()
        entrada = ResultadoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        punto = get_object_or_404(PuntoControl, pk=datos["punto"])
        try:
            services.registrar_resultado(
                control, punto, datos["valor"], request.user,
                observacion=datos["observacion"], severidad=datos["severidad"],
                descripcion=datos["descripcion"],
            )
        except services.ErrorCalidad as error:
            return _conflicto(error)
        return Response(self.get_serializer(self.get_queryset().get(pk=control.pk)).data)


class NoConformidadViewSet(viewsets.ReadOnlyModelViewSet):
    """No conformidades (CU-CAL-05)."""

    serializer_class = NoConformidadSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "no_conformidad"
    permisos_accion = {"cerrar": "no_conformidad.actualizar"}
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "severidad"]
    pagination_class = None

    def get_queryset(self):
        return (NoConformidad.objects
                .select_related("resultado__punto", "resultado__control__orden_trabajo",
                                "responsable", "usuario_cierre")
                .order_by("estado", "-abierta_en"))

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        nc = self.get_object()
        try:
            services.cerrar_no_conformidad(nc, request.user,
                                           request.data.get("accion_correctiva", ""))
        except services.ErrorCalidad as error:
            return _conflicto(error)
        return Response(self.get_serializer(nc).data)
