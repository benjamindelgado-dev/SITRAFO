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


def _auditar(usuario, entidad, pk, accion, anterior, nuevo):
    Auditoria.objects.create(usuario=usuario, entidad=entidad, id_registro=str(pk),
                             accion=accion, valor_anterior=anterior, valor_nuevo=nuevo,
                             origen=Auditoria.Origen.ESCRITORIO)


class FamiliaProductoViewSet(viewsets.ModelViewSet):
    """
    Familias de producto (RF-CAT-01). No se eliminan: se desactivan (RN-13), y
    solo si no tienen modelos vigentes. ?todas=1 incluye las inactivas.
    """

    serializer_class = FamiliaProductoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "catalogo"
    acciones_cliente = ("list", "retrieve")
    permisos_accion = {"reactivar": "catalogo.actualizar"}
    search_fields = ["nombre"]

    def get_queryset(self):
        consulta = FamiliaProducto.objects.all()
        todas = self.request.query_params.get("todas") == "1" and self.request.user.es_interno
        if self.action == "list" and not todas:
            consulta = consulta.filter(activo=True)
        return consulta

    def perform_update(self, serializer):
        anterior = {"nombre": serializer.instance.nombre,
                    "descripcion": serializer.instance.descripcion}
        familia = serializer.save()
        _auditar(self.request.user, "familia_producto", familia.pk,
                 Auditoria.Accion.MODIFICACION, anterior,
                 {"nombre": familia.nombre, "descripcion": familia.descripcion})

    def destroy(self, request, *args, **kwargs):
        familia = self.get_object()
        vigentes = familia.modelos.filter(activo=True).count()
        if vigentes:
            return Response(
                {"detalle": f"La familia tiene {vigentes} modelo(s) vigente(s). Cambielos "
                            "de familia antes de desactivarla."},
                status=status.HTTP_409_CONFLICT)
        familia.activo = False
        familia.save(update_fields=["activo"])
        _auditar(request.user, "familia_producto", familia.pk, Auditoria.Accion.ANULACION,
                 {"activo": True}, {"activo": False, "nombre": familia.nombre})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def reactivar(self, request, pk=None):
        familia = self.get_object()
        familia.activo = True
        familia.save(update_fields=["activo"])
        _auditar(request.user, "familia_producto", familia.pk, Auditoria.Accion.MODIFICACION,
                 {"activo": False}, {"activo": True, "nombre": familia.nombre})
        return Response(self.get_serializer(familia).data)


class ParametroTecnicoViewSet(viewsets.ModelViewSet):
    """
    Parametros tecnicos y sus valores admisibles (RF-CAT-03). Con ellos se arma
    el formulario de solicitud de la web (RF-ADM-04): nombre, unidad, tipo,
    obligatoriedad, rango aceptable y lista de valores.
    """

    queryset = ParametroTecnico.objects.prefetch_related("valores")
    serializer_class = ParametroTecnicoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "catalogo"
    acciones_cliente = ("list", "retrieve")
    permisos_accion = {"agregar_valor": "catalogo.actualizar",
                       "estado_valor": "catalogo.actualizar"}
    search_fields = ["codigo", "nombre"]

    def perform_create(self, serializer):
        parametro = serializer.save()
        _auditar(self.request.user, "parametro_tecnico", parametro.codigo,
                 Auditoria.Accion.CREACION, None, serializer.data)

    def perform_update(self, serializer):
        anterior = ParametroTecnicoSerializer(serializer.instance).data
        anterior.pop("valores", None)
        parametro = serializer.save()
        nuevo = dict(serializer.data)
        nuevo.pop("valores", None)
        _auditar(self.request.user, "parametro_tecnico", parametro.codigo,
                 Auditoria.Accion.MODIFICACION, anterior, nuevo)

    def destroy(self, request, *args, **kwargs):
        parametro = self.get_object()
        if ParametroTecnicoSerializer().get_en_uso(parametro):
            return Response(
                {"detalle": "El parametro ya se usa en modelos o solicitudes y no puede "
                            "eliminarse. Puede dejarlo como no obligatorio."},
                status=status.HTTP_409_CONFLICT)
        codigo = parametro.codigo
        parametro.delete()
        _auditar(request.user, "parametro_tecnico", codigo, Auditoria.Accion.ANULACION,
                 {"codigo": codigo}, None)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def agregar_valor(self, request, pk=None):
        """Agrega un valor admisible a un parametro de tipo lista."""
        from .models import ValorParametro

        parametro = self.get_object()
        if parametro.tipo_dato != ParametroTecnico.TipoDato.LISTA:
            return Response({"detalle": "Solo los parametros de tipo lista tienen valores."},
                            status=status.HTTP_409_CONFLICT)
        valor = str(request.data.get("valor", "")).strip()
        if not valor:
            return Response({"valor": "Indique el valor."}, status=status.HTTP_400_BAD_REQUEST)
        existente = parametro.valores.filter(valor=valor).first()
        if existente:
            existente.activo = True
            existente.save(update_fields=["activo"])
        else:
            orden = (parametro.valores.order_by("-orden").values_list("orden", flat=True)
                     .first() or 0) + 1
            ValorParametro.objects.create(parametro=parametro, valor=valor, orden=orden)
        _auditar(request.user, "parametro_tecnico", parametro.codigo,
                 Auditoria.Accion.MODIFICACION, None, {"valor_agregado": valor})
        return Response(self.get_serializer(self.get_queryset().get(pk=parametro.pk)).data)

    @action(detail=True, methods=["post"])
    def estado_valor(self, request, pk=None):
        """Retira o restituye un valor de la lista (no se borra: hay solicitudes con el)."""
        parametro = self.get_object()
        valor = parametro.valores.filter(pk=request.data.get("id_valor")).first()
        if valor is None:
            return Response({"detalle": "Valor no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)
        valor.activo = bool(request.data.get("activo"))
        valor.save(update_fields=["activo"])
        _auditar(request.user, "parametro_tecnico", parametro.codigo,
                 Auditoria.Accion.MODIFICACION, None,
                 {"valor": valor.valor, "activo": valor.activo})
        return Response(self.get_serializer(self.get_queryset().get(pk=parametro.pk)).data)


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
        # Un modelo sin tareas estandar no puede fabricarse: no se ofrece al cliente
        if not anterior and not modelo.tareas_estandar.exists():
            return Response(
                {"detalle": "El modelo no tiene tareas estandar. Defina sus materiales y "
                            "tareas (Catalogo > Materiales y tareas) antes de publicarlo."},
                status=status.HTTP_409_CONFLICT)
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
                 "horas_estimadas": str(t.horas_estimadas),
                 "empleado_sugerido": t.empleado_sugerido_id,
                 "empleado_sugerido_nombre": getattr(t.empleado_sugerido, "nombre", None)}
                for t in modelo.tareas_estandar.select_related("empleado_sugerido")
                .order_by("secuencia")
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
