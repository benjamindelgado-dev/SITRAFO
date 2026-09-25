"""Vistas de la API para el dominio de catalogo."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa, PermisoPorRol
from apps.seguridad.models import Auditoria

from .models import FamiliaProducto, ModeloProducto, ParametroTecnico
from .serializers import (
    FamiliaProductoSerializer,
    ModeloProductoDetalleSerializer,
    ModeloProductoListaSerializer,
    ParametroTecnicoSerializer,
)


class FamiliaProductoViewSet(viewsets.ModelViewSet):
    queryset = FamiliaProducto.objects.filter(activo=True)
    serializer_class = FamiliaProductoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "catalogo"
    acciones_cliente = ("list", "retrieve")
    search_fields = ["nombre"]


class ParametroTecnicoViewSet(viewsets.ModelViewSet):
    queryset = ParametroTecnico.objects.prefetch_related("valores")
    serializer_class = ParametroTecnicoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "catalogo"
    acciones_cliente = ("list", "retrieve")
    search_fields = ["codigo", "nombre"]


class ModeloProductoViewSet(viewsets.ModelViewSet):
    """
    Catalogo de modelos.

    El cliente web solo ve los modelos publicados: la visibilidad se
    administra desde la aplicacion de escritorio (RF-ADM-06).
    """

    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "catalogo"
    acciones_cliente = ("list", "retrieve")
    permisos_accion = {"publicar": "catalogo.actualizar"}
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["familia", "publicado"]
    search_fields = ["codigo", "nombre", "descripcion"]
    ordering_fields = ["codigo", "nombre"]

    def get_queryset(self):
        queryset = (
            ModeloProducto.objects.select_related("familia")
            .prefetch_related("precios", "materiales__material",
                              "tareas_estandar", "parametros_asignados__parametro")
            .filter(activo=True)
        )
        usuario = self.request.user
        if not (usuario.is_superuser or usuario.es_interno):
            queryset = queryset.filter(publicado=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ModeloProductoListaSerializer
        return ModeloProductoDetalleSerializer

    @action(detail=True, methods=["post"])
    def publicar(self, request, pk=None):
        """
        Publica o retira el modelo del catalogo web (RF-ADM-06).

        Es el caso mas directo de la regla segun la cual la aplicacion de
        escritorio administra la aplicacion web.
        """
        modelo = self.get_object()
        anterior = modelo.publicado
        modelo.publicado = not anterior
        modelo.save(update_fields=["publicado"])

        Auditoria.objects.create(
            usuario=request.user,
            entidad="modelo_producto",
            id_registro=str(modelo.pk),
            accion=Auditoria.Accion.MODIFICACION,
            valor_anterior={"publicado": anterior},
            valor_nuevo={"publicado": modelo.publicado},
            origen=Auditoria.Origen.ESCRITORIO,
        )
        return Response(ModeloProductoDetalleSerializer(modelo).data)
