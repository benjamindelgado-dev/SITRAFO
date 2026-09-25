"""
Integracion con la pasarela de pago PayPal (entorno Sandbox).

Sustenta RF-PAG-02 y el caso de uso CU-PAG-02 (pagar en linea).

Flujo de PayPal Checkout (Orders API v2):

1. SITRAFO obtiene un token de acceso con sus credenciales (OAuth 2.0,
   client credentials).
2. SITRAFO crea una orden de pago con el monto a cobrar y recibe un enlace
   de aprobacion.
3. El cliente es redirigido a PayPal, inicia sesion y aprueba el pago.
4. PayPal devuelve al cliente a SITRAFO con el identificador de la orden.
5. SITRAFO captura la orden: recien ahi se mueve el dinero.

Consideraciones de diseno:

- Moneda: PayPal no opera en pesos chilenos. El cobro se hace en USD,
  convirtiendo el monto en pesos del documento con el dolar observado que
  entrega mindicador.cl. La conversion queda registrada en la transaccion.
- Idempotencia: toda llamada que crea o captura envia PayPal-Request-Id, de
  modo que los reintentos del cliente base (RF-INT-02) no generen cobros
  duplicados.
- Secretos: las credenciales se leen del entorno (.env) y nunca se escriben
  en el log de integraciones ni en la base de datos.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache

from apps.configuracion.services.base import ClienteServicioExterno, RespuestaServicio

CLAVE_CACHE_TOKEN = "paypal_token_acceso"
URL_SANDBOX = "https://api-m.sandbox.paypal.com"


@dataclass
class OrdenPayPal:
    """Resultado de crear una orden de pago."""

    exitoso: bool
    id_orden: str = ""
    estado: str = ""
    url_aprobacion: str = ""
    error: str = ""


@dataclass
class CapturaPayPal:
    """Resultado de capturar (cobrar) una orden aprobada."""

    exitoso: bool
    estado: str = ""            # COMPLETED, DECLINED, PENDING, ...
    id_captura: str = ""
    monto: Decimal | None = None
    moneda: str = ""
    motivo: str = ""            # codigo de error de PayPal (INSTRUMENT_DECLINED, ...)
    sin_respuesta: bool = False  # True si PayPal no respondio: requiere conciliacion
    error: str = ""


class ClientePayPal(ClienteServicioExterno):
    nombre_servicio = "paypal"
    tiempo_espera = 20

    def __init__(self, url_base: str | None = None,
                 client_id: str | None = None, secreto: str | None = None):
        super().__init__(url_base or getattr(settings, "PAYPAL_API_URL", URL_SANDBOX))
        self.client_id = client_id if client_id is not None else settings.PAYPAL_CLIENT_ID
        self.secreto = secreto if secreto is not None else settings.PAYPAL_SECRET

    # ------------------------------------------------------------------
    # Autenticacion
    # ------------------------------------------------------------------
    @property
    def configurado(self) -> bool:
        return bool(self.client_id and self.secreto)

    def _token(self) -> str | None:
        """Token de acceso OAuth 2.0, reutilizado mientras este vigente."""
        token = cache.get(CLAVE_CACHE_TOKEN)
        if token:
            return token

        respuesta = self.solicitar(
            "POST", "/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.secreto),
            headers={"Accept": "application/json"},
        )
        if not respuesta:
            return None

        token = respuesta.datos.get("access_token")
        vigencia = int(respuesta.datos.get("expires_in", 300))
        if token:
            # Se descarta un minuto antes de que expire
            cache.set(CLAVE_CACHE_TOKEN, token, max(vigencia - 60, 30))
        return token

    def _cabeceras(self, token: str, clave_idempotencia: str | None = None) -> dict:
        cabeceras = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if clave_idempotencia:
            cabeceras["PayPal-Request-Id"] = clave_idempotencia
        return cabeceras

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------
    def crear_orden(
        self,
        *,
        monto: Decimal,
        moneda: str,
        referencia: str,
        descripcion: str,
        url_retorno: str,
        url_cancelacion: str,
        clave_idempotencia: str,
    ) -> OrdenPayPal:
        """Crea la orden de pago y devuelve el enlace donde el cliente la aprueba."""
        if not self.configurado:
            return OrdenPayPal(False, error="Credenciales de PayPal no configuradas.")

        token = self._token()
        if not token:
            return OrdenPayPal(False, error="No se pudo autenticar con PayPal.")

        cuerpo = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": referencia,
                "custom_id": referencia,
                "description": descripcion[:127],
                "amount": {"currency_code": moneda, "value": f"{monto:.2f}"},
            }],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "brand_name": "SITRAFO",
                        "locale": "es-CL",
                        "shipping_preference": "NO_SHIPPING",
                        "user_action": "PAY_NOW",
                        "return_url": url_retorno,
                        "cancel_url": url_cancelacion,
                    }
                }
            },
        }
        respuesta = self.solicitar(
            "POST", "/v2/checkout/orders",
            json=cuerpo, headers=self._cabeceras(token, clave_idempotencia),
        )
        if not respuesta:
            return OrdenPayPal(False, error=_detalle_error(respuesta))

        datos = respuesta.datos or {}
        enlace = next(
            (e.get("href") for e in datos.get("links", [])
             if e.get("rel") in ("payer-action", "approve")),
            "",
        )
        if not datos.get("id") or not enlace:
            return OrdenPayPal(False, error="PayPal no devolvio el enlace de aprobacion.")

        return OrdenPayPal(
            True, id_orden=datos["id"], estado=datos.get("status", ""), url_aprobacion=enlace
        )

    def capturar_orden(self, id_orden: str) -> CapturaPayPal:
        """Cobra una orden que el cliente ya aprobo."""
        token = self._token()
        if not token:
            return CapturaPayPal(False, sin_respuesta=True,
                                 error="No se pudo autenticar con PayPal.")

        respuesta = self.solicitar(
            "POST", f"/v2/checkout/orders/{id_orden}/capture",
            json={}, headers=self._cabeceras(token, f"captura-{id_orden}"),
        )
        return _interpretar_captura(respuesta)

    def consultar_orden(self, id_orden: str) -> RespuestaServicio:
        """Estado actual de una orden (usado para conciliar pagos sin respuesta)."""
        token = self._token()
        if not token:
            return RespuestaServicio(False, mensaje_error="No se pudo autenticar con PayPal.")
        return self.solicitar(
            "GET", f"/v2/checkout/orders/{id_orden}", headers=self._cabeceras(token)
        )


# ----------------------------------------------------------------------
# Interpretacion de respuestas
# ----------------------------------------------------------------------
def _detalle_error(respuesta: RespuestaServicio) -> str:
    """Extrae el codigo de error de PayPal (details[0].issue) si viene."""
    datos = respuesta.datos if isinstance(respuesta.datos, dict) else {}
    detalles = datos.get("details") or []
    if detalles and isinstance(detalles[0], dict) and detalles[0].get("issue"):
        return detalles[0]["issue"]
    return datos.get("name") or respuesta.mensaje_error or "Error desconocido"


def extraer_captura(datos: dict) -> dict:
    """Primera captura de una orden de PayPal, o un diccionario vacio."""
    try:
        return datos["purchase_units"][0]["payments"]["captures"][0]
    except (KeyError, IndexError, TypeError):
        return {}


def _interpretar_captura(respuesta: RespuestaServicio) -> CapturaPayPal:
    if not respuesta:
        # Sin codigo HTTP: PayPal no respondio. No se sabe si cobro o no.
        if respuesta.codigo == 0 or respuesta.codigo >= 500:
            return CapturaPayPal(False, sin_respuesta=True, error=respuesta.mensaje_error)
        return CapturaPayPal(False, motivo=_detalle_error(respuesta),
                             error=respuesta.mensaje_error)

    captura = extraer_captura(respuesta.datos or {})
    monto = captura.get("amount") or {}
    return CapturaPayPal(
        exitoso=captura.get("status") == "COMPLETED",
        estado=captura.get("status") or (respuesta.datos or {}).get("status", ""),
        id_captura=captura.get("id", ""),
        monto=Decimal(str(monto["value"])) if monto.get("value") else None,
        moneda=monto.get("currency_code", ""),
    )
