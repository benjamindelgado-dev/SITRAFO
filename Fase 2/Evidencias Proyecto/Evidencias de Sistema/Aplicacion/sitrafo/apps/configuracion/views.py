"""
Vistas de la API para el dominio de configuracion.

Estos endpoints son los que permiten que la aplicacion de escritorio
administre el comportamiento de la aplicacion web (RF-ADM-01 a RF-ADM-07).
Son exclusivos de usuarios internos.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa, EsUsuarioInterno
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
    permission_classes = [CuentaOperativa, EsUsuarioInterno]
    modulo_permiso = "configuracion"
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["ambito", "tipo_dato"]
    search_fields = ["clave", "descripcion"]
    lookup_field = "clave"
    lookup_value_regex = "[^/]+"
    pagination_class = None

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
    permission_classes = [CuentaOperativa, EsUsuarioInterno]
    modulo_permiso = "configuracion"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "activo"]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class FeriadoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Feriado.objects.all()
    serializer_class = FeriadoSerializer
    permission_classes = [CuentaOperativa]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo"]


class LogIntegracionViewSet(viewsets.ReadOnlyModelViewSet):
    """Log de llamadas a servicios externos (RF-INT-01). Solo lectura."""

    queryset = LogIntegracion.objects.all()
    serializer_class = LogIntegracionSerializer
    permission_classes = [CuentaOperativa, EsUsuarioInterno]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["servicio", "exitoso"]
    search_fields = ["endpoint", "mensaje_error"]
