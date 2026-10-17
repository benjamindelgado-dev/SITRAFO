"""
Vistas de la API publica de SITRAFO.

A diferencia de la API interna (/api/v1/, con usuario y token JWT), esta API
la consumen sistemas externos y el portal web con una clave de API. Cada
llamada queda registrada en el log de integraciones, visible desde la
aplicacion de escritorio.
"""
import time

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comercial.models import OrdenCompra
from apps.configuracion.models import LogIntegracion

from .codigos import codigo_valido
from .seguimiento import estado_pedido
from .seguridad import ClaveApiAutenticacion, LimitePorClave, TieneClaveApi
from .serializers import ErrorSerializer, SeguimientoSerializer

NO_ENCONTRADO = "No existe un pedido con ese numero y codigo de seguimiento."


class VistaApiPublica(APIView):
    """Base comun: clave de API, limite de solicitudes y registro de uso."""

    authentication_classes = [ClaveApiAutenticacion]
    permission_classes = [TieneClaveApi]
    throttle_classes = [LimitePorClave]
    servicio = "api_publica"

    def dispatch(self, request, *args, **kwargs):
        inicio = time.monotonic()
        respuesta = super().dispatch(request, *args, **kwargs)
        self._registrar(request, respuesta, inicio)
        return respuesta

    def _registrar(self, request, respuesta, inicio):
        consumidor = getattr(getattr(self, "request", None), "auth", None) or "sin clave"
        exitoso = respuesta.status_code < 400
        detalle = ""
        if not exitoso and isinstance(getattr(respuesta, "data", None), dict):
            detalle = str(respuesta.data.get("detail", ""))[:500]
        LogIntegracion.objects.create(
            servicio=self.servicio,
            # Solo la ruta: el codigo de seguimiento no se guarda en el registro
            endpoint=f"{request.path} [{consumidor}]"[:255],
            metodo=request.method,
            codigo_respuesta=respuesta.status_code,
            latencia_ms=int((time.monotonic() - inicio) * 1000),
            exitoso=exitoso,
            mensaje_error=detalle,
        )


class SeguimientoView(VistaApiPublica):
    servicio = "api_seguimiento"

    @extend_schema(
        operation_id="consultar_seguimiento",
        summary="Consultar el estado de un pedido",
        description=(
            "Devuelve la etapa actual del pedido, su porcentaje de avance, la fecha "
            "estimada de entrega en dias habiles y el historial de estados. Requiere el "
            "numero de la orden de compra y el codigo de seguimiento que recibe el cliente."
        ),
        tags=["Seguimiento de pedidos"],
        parameters=[
            OpenApiParameter("numero", str, OpenApiParameter.PATH,
                             description="Numero de la orden de compra (ej.: OC-2026-0001)."),
            OpenApiParameter("codigo", str, OpenApiParameter.QUERY, required=True,
                             description="Codigo de seguimiento (ej.: ABCDE-FGHIJ)."),
        ],
        responses={
            200: SeguimientoSerializer,
            401: OpenApiResponse(ErrorSerializer, description="Falta la clave de API o no es valida."),
            404: OpenApiResponse(ErrorSerializer, description="Numero o codigo incorrectos."),
            429: OpenApiResponse(ErrorSerializer, description="Se supero el limite de solicitudes."),
        },
    )
    def get(self, request, numero):
        orden = (OrdenCompra.objects.select_related("estado", "cotizacion")
                 .filter(numero=numero.strip().upper()).first())
        # Mismo error para numero inexistente y codigo incorrecto: no revela
        # que pedidos existen
        if orden is None or not codigo_valido(orden, request.query_params.get("codigo", "")):
            raise NotFound(NO_ENCONTRADO)
        return Response(SeguimientoSerializer(estado_pedido(orden)).data)
