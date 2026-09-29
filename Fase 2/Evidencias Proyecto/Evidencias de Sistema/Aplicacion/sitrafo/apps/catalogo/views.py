"""Vistas de la API para el dominio de catalogo."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.common.permissions import (
    CuentaOperativa,
    PermisoPorRol,
    registrar_acceso_denegado,
)
from apps.seguridad.models import Auditoria

from . import services
from .models import FamiliaProducto, ModeloProducto, ParametroTecnico
from .serializers import (
    FamiliaProductoSerializer,
    ModeloProductoDetalleSerializer,
    ModeloProductoEscrituraSerializer,
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
    permisos_accion = {
        "publicar": "catalogo.actualizar",
        "receta": "bom.leer",
        "guardar_receta": "bom.actualizar",
        "costeo": "cotizacion.crear",
        # Un modelo con cotizaciones no se borra: se retira del catalogo
        "destroy": None,
    }
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
        if self.action in ("create", "update", "partial_update"):
            return ModeloProductoEscrituraSerializer
        return ModeloProductoDetalleSerializer

    def _guardar(self, request, modelo=None):
        entrada = ModeloProductoEscrituraSerializer(
            instance=modelo, data=request.data, partial=modelo is not None
        )
        entrada.is_valid(raise_exception=True)
        datos = dict(entrada.validated_data)
        if datos.get("precio_base_uf") is not None and not request.user.has_perm(
            "precio.actualizar"
        ):
            registrar_acceso_denegado(request, self, "precio", ["precio.actualizar"])
            return Response({"detail": "Su rol no autoriza fijar precios."},
                            status=status.HTTP_403_FORBIDDEN)
        if modelo is not None:
            datos.pop("codigo", None)   # el codigo identifica al modelo: no cambia
        try:
            modelo = services.guardar_modelo(datos, request.user, modelo)
        except services.ErrorCatalogo as error:
            return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)
        modelo = self.get_queryset().get(pk=modelo.pk)
        return Response(ModeloProductoDetalleSerializer(modelo).data,
                        status=status.HTTP_200_OK if entrada.instance else
                        status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        return self._guardar(request)

    def update(self, request, *args, **kwargs):
        return self._guardar(request, self.get_object())

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

    @action(detail=True, methods=["get"])
    def receta(self, request, pk=None):
        """Lista de materiales y tareas estandar del modelo, con su costeo."""
        from apps.comercial.services import costear_modelo

        modelo = self.get_object()
        costeo = costear_modelo(modelo)
        return Response({
            "modelo": modelo.codigo,
            "materiales": [
                {"material": b.material_id, "codigo": b.material.codigo,
                 "nombre": b.material.nombre, "unidad": b.material.unidad_medida,
                 "cantidad": str(b.cantidad), "observacion": b.observacion,
                 "costo_unitario_uf": str(b.material.costo_vigente or "")}
                for b in modelo.materiales.select_related("material").order_by("material__codigo")
            ],
            "tareas": [
                {"nombre": t.nombre, "secuencia": t.secuencia,
                 "horas_estimadas": str(t.horas_estimadas)}
                for t in modelo.tareas_estandar.order_by("secuencia")
            ],
            "costo_material_uf": str(costeo.costo_material_uf),
            "costo_hh_uf": str(costeo.costo_hh_uf),
            "horas_estandar": str(costeo.horas_estandar),
            "tarifa_referencia_uf": str(costeo.tarifa_referencia_uf or ""),
        })

    @action(detail=True, methods=["post"])
    def guardar_receta(self, request, pk=None):
        """Reemplaza la receta completa del modelo (RF-CAT-04, 05)."""
        modelo = self.get_object()
        try:
            services.guardar_receta(modelo, request.user,
                                    materiales=request.data.get("materiales", []),
                                    tareas=request.data.get("tareas", []))
        except (services.ErrorCatalogo, KeyError, ArithmeticError, ValueError) as error:
            mensaje = str(error) if isinstance(error, services.ErrorCatalogo) else \
                "Datos incompletos o no numericos en la receta."
            return Response({"detalle": mensaje}, status=status.HTTP_409_CONFLICT)
        return self.receta(request, pk)

    @action(detail=True, methods=["get"])
    def costeo(self, request, pk=None):
        """Costo unitario y precio sugerido, para agregar lineas a una cotizacion."""
        from apps.comercial.services import costear_modelo

        modelo = self.get_object()
        c = costear_modelo(modelo, request.query_params.get("margen"))
        return Response({
            "modelo": modelo.nombre, "costo_material_uf": str(c.costo_material_uf),
            "costo_hh_uf": str(c.costo_hh_uf), "costo_estimado_uf": str(c.costo_estimado_uf),
            "margen_pct": str(c.margen_pct), "precio_base_uf": str(c.precio_base_uf or ""),
            "precio_sugerido_uf": str(c.precio_sugerido_uf or ""),
            "origen_precio": c.origen_precio,
        })
