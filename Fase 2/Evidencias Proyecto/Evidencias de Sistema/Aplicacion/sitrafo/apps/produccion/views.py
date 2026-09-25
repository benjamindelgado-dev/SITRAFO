"""Vistas de la API para la ejecucion productiva."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa, PermisoPorRol
from apps.inventario.models import Bodega, Material

from . import services
from .models import Empleado, OrdenTrabajo, RegistroHoraHombre, TareaOT
from .serializers import (
    EmpleadoSerializer,
    OrdenTrabajoSerializer,
    RegistrarConsumoSerializer,
    RegistrarHorasSerializer,
    TareaSerializer,
)


def _conflicto(error):
    return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)


class OrdenTrabajoViewSet(viewsets.ReadOnlyModelViewSet):
    """Ordenes de trabajo (CU-OT-01 a CU-OT-08)."""

    queryset = (
        OrdenTrabajo.objects.select_related("estado", "modelo", "orden_compra__cliente")
        .prefetch_related("tareas__empleado", "tareas__registros_hora",
                          "tareas__consumos", "historial__estado_nuevo",
                          "historial__estado_anterior", "historial__usuario")
        .order_by("-creado_en")
    )
    serializer_class = OrdenTrabajoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "orden_trabajo"
    permisos_accion = {
        "iniciar": "orden_trabajo.actualizar",
        "enviar_calidad": "orden_trabajo.actualizar",
        "cerrar": "orden_trabajo.actualizar",
    }
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "orden_compra"]

    def _accion(self, operacion, *args):
        ot = self.get_object()
        try:
            operacion(ot, self.request.user, *args)
        except services.ErrorProduccion as error:
            return _conflicto(error)
        return Response(self.get_serializer(self.get_queryset().get(pk=ot.pk)).data)

    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        return self._accion(services.iniciar)

    @action(detail=True, methods=["post"])
    def enviar_calidad(self, request, pk=None):
        return self._accion(services.enviar_a_calidad)

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        return self._accion(services.cerrar, request.data.get("justificacion", ""))


class TareaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tareas de las ordenes de trabajo y registro en taller.

    Con ?mias=1 devuelve solo las tareas asignadas al empleado del usuario,
    que es lo que ve el operario en la vista de taller.
    """

    serializer_class = TareaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    permisos_alternativos = {
        "list": ["orden_trabajo.leer", "taller.leer"],
        "retrieve": ["orden_trabajo.leer", "taller.leer"],
    }
    permisos_accion = {
        "asignar": "orden_trabajo.actualizar",
        "registrar_horas": "taller.crear",
        "registrar_consumo": "taller.crear",
        "anular_horas": "taller.anular",
        "terminar": "taller.actualizar",
    }
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["orden_trabajo", "estado", "empleado"]

    def get_queryset(self):
        queryset = TareaOT.objects.select_related(
            "empleado", "orden_trabajo__modelo", "orden_trabajo__estado"
        ).prefetch_related("registros_hora__empleado")
        if self.request.query_params.get("mias"):
            empleado = getattr(self.request.user, "empleado", None)
            if empleado is None:
                return queryset.none()
            queryset = queryset.filter(
                empleado=empleado, orden_trabajo__estado__codigo="en_ejecucion"
            ).exclude(estado=TareaOT.Estado.TERMINADA)
        return queryset.order_by("orden_trabajo__numero", "secuencia")

    def _empleado(self, datos):
        """El empleado indicado, o el del usuario que registra."""
        empleado = datos.get("empleado") or getattr(self.request.user, "empleado", None)
        if empleado is None:
            raise services.ErrorProduccion(
                "Su usuario no esta asociado a un empleado: indique el empleado."
            )
        if (empleado != getattr(self.request.user, "empleado", None)
                and not self.request.user.has_perm("orden_trabajo.actualizar")):
            raise services.ErrorProduccion("Solo puede registrar a su propio nombre.")
        return empleado

    def _respuesta(self, tarea):
        return Response(self.get_serializer(self.get_queryset().get(pk=tarea.pk)).data)

    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        tarea = self.get_object()
        empleado = get_object_or_404(Empleado, pk=request.data.get("empleado"))
        try:
            services.asignar_empleado(tarea, empleado)
        except services.ErrorProduccion as error:
            return _conflicto(error)
        return self._respuesta(tarea)

    @action(detail=True, methods=["post"])
    def registrar_horas(self, request, pk=None):
        tarea = self.get_object()
        entrada = RegistrarHorasSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            services.registrar_horas(
                tarea, self._empleado(datos), datos.get("fecha") or timezone.localdate(),
                datos["horas"], request.user,
            )
        except services.ErrorProduccion as error:
            return _conflicto(error)
        return self._respuesta(tarea)

    @action(detail=True, methods=["post"])
    def registrar_consumo(self, request, pk=None):
        tarea = self.get_object()
        entrada = RegistrarConsumoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        material = get_object_or_404(Material, pk=datos["material"], activo=True)
        bodega = get_object_or_404(Bodega, pk=datos["bodega"], activo=True)
        try:
            services.registrar_consumo(
                tarea, material, bodega, datos["cantidad"], self._empleado(datos),
                request.user,
            )
        except services.ErrorProduccion as error:
            return _conflicto(error)
        return self._respuesta(tarea)

    @action(detail=True, methods=["post"])
    def anular_horas(self, request, pk=None):
        tarea = self.get_object()
        registro = get_object_or_404(RegistroHoraHombre, pk=request.data.get("registro"),
                                     tarea=tarea)
        if not services.puede_registrar_en(tarea, request.user):
            return _conflicto("Solo puede anular registros de sus tareas.")
        try:
            services.anular_horas(registro, request.user, request.data.get("motivo", ""))
        except services.ErrorProduccion as error:
            return _conflicto(error)
        return self._respuesta(tarea)

    @action(detail=True, methods=["post"])
    def terminar(self, request, pk=None):
        tarea = self.get_object()
        try:
            services.terminar_tarea(tarea, request.user)
        except services.ErrorProduccion as error:
            return _conflicto(error)
        return self._respuesta(tarea)


class EmpleadoViewSet(viewsets.ReadOnlyModelViewSet):
    """Empleados con su tarifa vigente. Lo usa la planificacion de tareas."""

    queryset = Empleado.objects.filter(activo=True).select_related("usuario")
    serializer_class = EmpleadoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    permisos_alternativos = {
        "list": ["empleado.leer", "orden_trabajo.actualizar"],
        "retrieve": ["empleado.leer", "orden_trabajo.actualizar"],
    }
    pagination_class = None
