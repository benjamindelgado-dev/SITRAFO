"""
Vistas de la API para el dominio de configuracion.

Estos endpoints son los que permiten que la aplicacion de escritorio
administre el comportamiento de la aplicacion web (RF-ADM-01 a RF-ADM-07).
Son exclusivos de usuarios internos.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa, PermisoPorRol, registrar_acceso_denegado
from apps.seguridad.models import Auditoria

from .models import AvisoSitio, Feriado, LogIntegracion, ParametroSistema
from .serializers import (
    AvisoSitioSerializer,
    FeriadoSerializer,
    LogIntegracionSerializer,
    ParametroSistemaSerializer,
)


def registrar_cambio(usuario, entidad, id_registro, anterior, nuevo, origen="escritorio"):
    """Deja el cambio de configuracion en la bitacora (RF-ADM-07)."""
    Auditoria.objects.create(
        usuario=usuario,
        entidad=entidad,
        id_registro=str(id_registro),
        accion=Auditoria.Accion.MODIFICACION,
        valor_anterior=anterior,
        valor_nuevo=nuevo,
        origen=origen,
    )


class ParametroSistemaViewSet(viewsets.ModelViewSet):
    """
    Parametros del sistema y del canal web.

    Toda modificacion queda auditada: no puede cambiarse el comportamiento
    del sitio sin dejar responsable registrado.
    """

    queryset = ParametroSistema.objects.select_related("usuario")
    serializer_class = ParametroSistemaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    # Un mismo endpoint sirve dos modulos de la matriz: el canal web
    # (Administrador opera, Ejecutivo comercial lee) y los parametros del
    # sistema (solo Administrador). La lectura exige cualquiera de los dos y
    # la modificacion se verifica contra el ambito de cada parametro.
    permisos_alternativos = {
        "list": ["canal_web.leer", "parametro.leer"],
        "retrieve": ["canal_web.leer", "parametro.leer"],
        "update": ["canal_web.actualizar", "parametro.actualizar"],
        "partial_update": ["canal_web.actualizar", "parametro.actualizar"],
        "alternar": ["canal_web.actualizar", "parametro.actualizar"],
    }
    permisos_accion = {"create": None, "destroy": None}
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["ambito", "tipo_dato"]
    search_fields = ["clave", "descripcion"]
    lookup_field = "clave"
    lookup_value_regex = "[^/]+"
    pagination_class = None

    def get_object(self):
        parametro = super().get_object()
        if self.action in ("update", "partial_update", "alternar"):
            self._verificar_ambito(parametro)
        return parametro

    def _verificar_ambito(self, parametro):
        """El ambito canal_web exige canal_web; el resto, parametro."""
        usuario = self.request.user
        if usuario.is_superuser:
            return
        requerido = ("canal_web.actualizar" if parametro.ambito == "canal_web"
                     else "parametro.actualizar")
        if not usuario.has_perm(requerido):
            registrar_acceso_denegado(self.request, self, self.action, [requerido])
            raise PermissionDenied("Su rol no autoriza modificar este parametro.")

    def perform_update(self, serializer):
        anterior = serializer.instance.valor
        parametro = serializer.save(usuario=self.request.user)
        registrar_cambio(
            self.request.user, "parametro_sistema", parametro.clave,
            {"valor": anterior}, {"valor": parametro.valor},
        )

    @action(detail=True, methods=["post"])
    def alternar(self, request, clave=None):
        """Invierte un parametro booleano. Usado por los interruptores."""
        parametro = self.get_object()

        if parametro.tipo_dato != ParametroSistema.TipoDato.BOOLEANO:
            return Response(
                {"detalle": "Solo puede alternarse un parametro booleano."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        anterior = parametro.valor
        parametro.valor = "false" if parametro.valor_tipado else "true"
        parametro.usuario = request.user
        parametro.save(update_fields=["valor", "usuario", "modificado_en"])

        registrar_cambio(
            request.user, "parametro_sistema", parametro.clave,
            {"valor": anterior}, {"valor": parametro.valor},
        )
        return Response(self.get_serializer(parametro).data)


class AvisoSitioViewSet(viewsets.ModelViewSet):
    queryset = AvisoSitio.objects.select_related("usuario")
    serializer_class = AvisoSitioSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "canal_web"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "activo"]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class FeriadoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Feriado.objects.all()
    serializer_class = FeriadoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    lectura_libre = True
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo"]


class LogIntegracionViewSet(viewsets.ReadOnlyModelViewSet):
    """Log de llamadas a servicios externos (RF-INT-01). Solo lectura."""

    queryset = LogIntegracion.objects.all()
    serializer_class = LogIntegracionSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "parametro"
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["servicio", "exitoso"]
    search_fields = ["endpoint", "mensaje_error"]
