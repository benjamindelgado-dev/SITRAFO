"""Vistas de la API para el inventario (HU-10)."""
from django.db import IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa, PermisoPorRol

from . import services
from .models import Bodega, CategoriaMaterial, Material, Proveedor
from .serializers import (
    AjusteSerializer,
    BodegaSerializer,
    CategoriaSerializer,
    MaterialEntradaSerializer,
    MaterialSerializer,
    ProveedorSerializer,
    RecepcionSerializer,
)

# El operario necesita ver materiales y bodegas para registrar un consumo,
# aunque no tenga acceso a la gestion de inventario
LECTURA = ["material.leer", "bodega.leer", "kardex.leer", "taller.crear"]


def _conflicto(error):
    return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)


class MaterialViewSet(viewsets.ModelViewSet):
    """
    Materiales con stock calculado. ?bajo_minimo=1 devuelve solo los que
    estan bajo su stock minimo (alerta de reposicion, CU-INV-06).
    """

    serializer_class = MaterialSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "material"
    permisos_alternativos = {"list": LECTURA, "retrieve": LECTURA,
                             "kardex": ["kardex.leer", "bodega.leer"]}
    permisos_accion = {
        "recepcion": "bodega.crear",
        "ajuste": "bodega.actualizar",
        # Un material con movimientos no se borra: se desactiva
        "destroy": None, "update": None,
    }
    filter_backends = [SearchFilter]
    search_fields = ["codigo", "nombre"]
    pagination_class = None

    def get_queryset(self):
        consulta = Material.objects.select_related("categoria").prefetch_related("precios")
        if self.action == "list":
            consulta = consulta.filter(activo=True)
        return consulta.order_by("codigo")

    def list(self, request, *args, **kwargs):
        if request.query_params.get("bajo_minimo"):
            materiales = services.materiales_bajo_minimo()
            return Response(self.get_serializer(materiales, many=True).data)
        return super().list(request, *args, **kwargs)

    def _guardar(self, request, material=None):
        entrada = MaterialEntradaSerializer(instance=material, data=request.data,
                                            partial=material is not None)
        entrada.is_valid(raise_exception=True)
        datos = dict(entrada.validated_data)
        costo = datos.pop("costo_uf", None)
        with transaction.atomic():
            if material is None:
                material = Material.objects.create(**datos)
            else:
                datos.pop("codigo", None)   # el codigo identifica al material
                for campo, valor in datos.items():
                    setattr(material, campo, valor)
                material.save()
            if costo is not None:
                services.fijar_precio(material, costo, request.user)
        return Response(MaterialSerializer(material).data,
                        status=status.HTTP_200_OK if entrada.instance else
                        status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        return self._guardar(request)

    def partial_update(self, request, *args, **kwargs):
        return self._guardar(request, self.get_object())

    @action(detail=True, methods=["post"])
    def recepcion(self, request, pk=None):
        material = self.get_object()
        entrada = RecepcionSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            services.recepcionar(
                material, datos["bodega"], datos["cantidad"], request.user,
                costo_unitario_uf=datos.get("costo_unitario_uf"),
                proveedor=datos.get("proveedor"), documento=datos["documento"],
                actualizar_precio=datos["actualizar_precio"],
            )
        except services.ErrorInventario as error:
            return _conflicto(error)
        return Response(MaterialSerializer(material).data)

    @action(detail=True, methods=["post"])
    def ajuste(self, request, pk=None):
        material = self.get_object()
        entrada = AjusteSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            movimiento = services.ajustar(material, datos["bodega"], datos["conteo_fisico"],
                                          datos["motivo"], request.user)
        except services.ErrorInventario as error:
            return _conflicto(error)
        respuesta = dict(MaterialSerializer(material).data)
        respuesta["ajustado"] = movimiento is not None
        return Response(respuesta)

    @action(detail=True, methods=["get"])
    def kardex(self, request, pk=None):
        material = self.get_object()
        bodega = None
        if request.query_params.get("bodega"):
            bodega = Bodega.objects.filter(pk=request.query_params["bodega"]).first()
        datos = services.kardex(material, bodega)
        return Response({
            **datos,
            "saldo": str(datos["saldo"]),
            "movimientos": [
                {**m, "entrada": str(m["entrada"]) if m["entrada"] is not None else None,
                 "salida": str(m["salida"]) if m["salida"] is not None else None,
                 "saldo": str(m["saldo"]), "costo_unitario_uf": str(m["costo_unitario_uf"])}
                for m in datos["movimientos"]
            ],
        })


class BodegaViewSet(viewsets.ModelViewSet):
    queryset = Bodega.objects.filter(activo=True)
    serializer_class = BodegaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "bodega"
    permisos_alternativos = {"list": LECTURA, "retrieve": LECTURA}
    permisos_accion = {"destroy": None}
    pagination_class = None


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = CategoriaMaterial.objects.filter(activo=True).order_by("nombre")
    serializer_class = CategoriaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "material"
    permisos_alternativos = {"list": LECTURA, "retrieve": LECTURA}
    permisos_accion = {"destroy": None}
    pagination_class = None


class ProveedorViewSet(viewsets.ModelViewSet):
    serializer_class = ProveedorSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "material"
    permisos_alternativos = {"list": ["material.leer", "bodega.leer"],
                             "retrieve": ["material.leer", "bodega.leer"]}
    permisos_accion = {"destroy": None}
    filter_backends = [SearchFilter]
    search_fields = ["rut", "razon_social"]
    pagination_class = None

    def get_queryset(self):
        return Proveedor.objects.order_by("razon_social")

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"rut": "Ya existe un proveedor con ese RUT."}) from None
