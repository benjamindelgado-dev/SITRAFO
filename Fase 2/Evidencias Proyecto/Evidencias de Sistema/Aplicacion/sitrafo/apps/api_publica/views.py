"""
Vistas de la API publica de SITRAFO.

A diferencia de la API interna (/api/v1/, con usuario y token JWT), esta API
la consumen sistemas externos y el portal web con una clave de API. Cada
llamada queda registrada en el log de integraciones, visible desde la
aplicacion de escritorio.
"""
import time

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comercial.models import OrdenCompra
from apps.configuracion.models import LogIntegracion

from .codigos import codigo_valido
from .cotizador import estimar, modelos_cotizables
from .materiales import materiales_a_reponer
from .seguimiento import estado_pedido
from .seguridad import ClaveApiAutenticacion, LimitePorClave, TieneAlcance, TieneClaveApi
from .serializers import (
    ErrorSerializer,
    EstimacionEntradaSerializer,
    EstimacionSerializer,
    ModeloCatalogoSerializer,
    ReposicionSerializer,
    SeguimientoSerializer,
)

NO_ENCONTRADO = "No existe un pedido con ese numero y codigo de seguimiento."
RESPUESTAS_ACCESO = {
    401: OpenApiResponse(ErrorSerializer, description="Falta la clave de API o no es valida."),
    403: OpenApiResponse(ErrorSerializer, description="La clave no tiene acceso a este servicio."),
    429: OpenApiResponse(ErrorSerializer, description="Se supero el limite de solicitudes."),
}


class VistaApiPublica(APIView):
    """Base comun: clave de API, alcance, limite de solicitudes y registro de uso."""

    authentication_classes = [ClaveApiAutenticacion]
    permission_classes = [TieneClaveApi, TieneAlcance]
    throttle_classes = [LimitePorClave]
    servicio = "api_publica"
    alcance = None

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
    alcance = "seguimiento"

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
            404: OpenApiResponse(ErrorSerializer, description="Numero o codigo incorrectos."),
            **RESPUESTAS_ACCESO,
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


class ModelosCotizadorView(VistaApiPublica):
    servicio = "api_cotizador"
    alcance = "cotizador"

    @extend_schema(
        operation_id="listar_modelos",
        summary="Listar los modelos que se pueden cotizar",
        description="Modelos publicados en el catalogo, con el codigo que se usa en la estimacion.",
        tags=["Cotizador"],
        responses={200: ModeloCatalogoSerializer(many=True), **RESPUESTAS_ACCESO},
    )
    def get(self, request):
        return Response(ModeloCatalogoSerializer(modelos_cotizables(), many=True).data)


class EstimacionView(VistaApiPublica):
    servicio = "api_cotizador"
    alcance = "cotizador"

    @extend_schema(
        operation_id="estimar_precio",
        summary="Estimar el precio referencial de uno o mas modelos",
        description=(
            "Calcula el precio referencial de hasta 10 modelos con su cantidad, en UF, pesos "
            "y dolares con los indicadores del dia, junto con la fecha estimada de entrega en "
            "dias habiles y la validez de la estimacion. Usa el mismo costeo que el area "
            "comercial aplica en las cotizaciones, pero no expone costos internos ni margen. "
            "No crea ningun documento: para cotizar formalmente se usa el enlace "
            "solicitar_presupuesto de cada item."
        ),
        tags=["Cotizador"],
        request=EstimacionEntradaSerializer,
        examples=[OpenApiExample(
            "Dos modelos",
            value={"items": [{"modelo": "TD-100", "cantidad": 2},
                             {"modelo": "TD-250", "cantidad": 1}]},
            request_only=True,
        )],
        responses={
            200: EstimacionSerializer,
            400: OpenApiResponse(description="Modelo inexistente, cantidad o items invalidos."),
            **RESPUESTAS_ACCESO,
        },
    )
    def post(self, request):
        entrada = EstimacionEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return Response(EstimacionSerializer(estimar(entrada.validated_data["items"])).data)


class ReposicionMaterialesView(VistaApiPublica):
    servicio = "api_materiales"
    alcance = "materiales"

    @extend_schema(
        operation_id="materiales_a_reponer",
        summary="Consultar los materiales bajo su stock minimo",
        description=(
            "Devuelve los materiales cuyo stock actual, calculado desde el kardex, esta bajo "
            "su stock minimo, con la cantidad sugerida de reposicion (la que deja el stock en "
            "el doble del minimo). Pensado para que un proveedor autorizado prepare el "
            "despacho a tiempo. No expone costos, precios, bodegas ni movimientos."
        ),
        tags=["Disponibilidad de materiales"],
        responses={200: ReposicionSerializer, **RESPUESTAS_ACCESO},
    )
    def get(self, request):
        return Response(ReposicionSerializer(materiales_a_reponer()).data)
