"""Vistas de la API para el dominio de clientes."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from apps.common.mixins import FiltradoPorClienteMixin
from apps.common.permissions import CuentaOperativa, EsUsuarioInterno

from .models import Cliente, Comuna, ContactoCliente, DireccionCliente, Region
from .serializers import (
    ClienteSerializer,
    ComunaSerializer,
    ContactoClienteSerializer,
    DireccionClienteSerializer,
    RegionSerializer,
)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogo territorial. Lectura para cualquier cuenta operativa."""

    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [CuentaOperativa]
    pagination_class = None


class ComunaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comuna.objects.select_related("region")
    serializer_class = ComunaSerializer
    permission_classes = [CuentaOperativa]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["region"]
    search_fields = ["nombre"]


class ClienteViewSet(viewsets.ModelViewSet):
    """
    Gestion de clientes.

    El cliente web solo accede a su propio registro; el ejecutivo comercial
    accede a todos.
    """

    serializer_class = ClienteSerializer
    permission_classes = [CuentaOperativa]
    modulo_permiso = "cliente"
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["tipo_persona", "estado"]
    search_fields = ["rut", "razon_social", "nombre_fantasia"]

    def get_queryset(self):
        queryset = Cliente.objects.prefetch_related("contactos", "direcciones")
        usuario = self.request.user
        if usuario.is_superuser or usuario.es_interno:
            return queryset
        if usuario.cliente_id is None:
            return queryset.none()
        return queryset.filter(id_cliente=usuario.cliente_id)


class ContactoClienteViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    queryset = ContactoCliente.objects.select_related("cliente")
    serializer_class = ContactoClienteSerializer
    permission_classes = [CuentaOperativa]
    modulo_permiso = "cliente"
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "principal"]


class DireccionClienteViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    queryset = DireccionCliente.objects.select_related("cliente", "comuna")
    serializer_class = DireccionClienteSerializer
    permission_classes = [CuentaOperativa]
    modulo_permiso = "cliente"
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "tipo"]
