"""Vistas de la API para el inventario."""
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from apps.common.permissions import CuentaOperativa, PermisoPorRol

from .models import Bodega, Material
from .serializers import BodegaSerializer, MaterialSerializer

# El operario necesita ver materiales y bodegas para registrar un consumo,
# aunque no tenga acceso a la gestion de inventario
LECTURA = ["material.leer", "bodega.leer", "kardex.leer", "taller.crear"]


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Material.objects.filter(activo=True).select_related("categoria")
    serializer_class = MaterialSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    permisos_alternativos = {"list": LECTURA, "retrieve": LECTURA}
    filter_backends = [SearchFilter]
    search_fields = ["codigo", "nombre"]
    pagination_class = None


class BodegaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bodega.objects.filter(activo=True)
    serializer_class = BodegaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    permisos_alternativos = {"list": LECTURA, "retrieve": LECTURA}
    pagination_class = None
