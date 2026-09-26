"""
Cliente HTTP base para los servicios externos.

Concentra el comportamiento exigido por los requerimientos de integracion:

- RF-INT-01: cada llamada queda registrada en log_integracion con endpoint,
  codigo de respuesta, latencia y resultado.
- RF-INT-02: reintentos con espera incremental ante fallos transitorios.
- RF-INT-03: degradacion controlada. El cliente nunca propaga la excepcion
  de red hacia el proceso de negocio: devuelve un resultado que indica el
  fallo, y quien llama decide como seguir operando.
"""
import logging
import time
from dataclasses import dataclass
from typing import Any

import requests
from requests.exceptions import RequestException

from apps.configuracion.models import LogIntegracion

logger = logging.getLogger(__name__)


@dataclass
class RespuestaServicio:
    """Resultado de una llamada a un servicio externo."""

    exitoso: bool
    datos: Any = None
    codigo: int = 0
    mensaje_error: str = ""
    latencia_ms: int = 0
    intentos: int = 1

    def __bool__(self) -> bool:
        return self.exitoso


class ClienteServicioExterno:
    """
    Base de los clientes de servicios externos.

    Las subclases definen el nombre del servicio y la URL base.
    """

    nombre_servicio: str = "generico"
    url_base: str = ""
    tiempo_espera: int = 10
    max_intentos: int = 3
    espera_inicial: float = 1.0

    def __init__(self, url_base: str | None = None):
        if url_base:
            self.url_base = url_base

    def _registrar(self, endpoint, metodo, codigo, latencia_ms, exitoso, error=""):
        """Deja constancia de la llamada (RF-INT-01)."""
        try:
            LogIntegracion.objects.create(
                servicio=self.nombre_servicio,
                endpoint=endpoint[:255],
                metodo=metodo,
                codigo_respuesta=codigo,
                latencia_ms=latencia_ms,
                exitoso=exitoso,
                mensaje_error=error[:500],
            )
        except Exception:  # noqa: BLE001
            # El registro del log nunca debe romper el proceso de negocio
            logger.exception("No se pudo registrar la llamada a %s", self.nombre_servicio)

    def obtener(self, ruta: str = "", params: dict | None = None) -> RespuestaServicio:
        """Ejecuta un GET con reintentos y espera incremental (RF-INT-02)."""
        return self.solicitar("GET", ruta, params=params)

    def solicitar(
        self,
        metodo: str,
        ruta: str = "",
        *,
        params: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        auth: tuple | None = None,
    ) -> RespuestaServicio:
        """
        Ejecuta una peticion HTTP con reintentos y espera incremental (RF-INT-02).

        Un codigo 4xx no se reintenta: el problema esta en la peticion, no en
        la disponibilidad del servicio. En ese caso se conserva el cuerpo de
        la respuesta, porque suele explicar el rechazo.

        Reintentar un POST solo es seguro si el servicio es idempotente para
        esa peticion; las subclases que lo usan deben enviar una clave de
        idempotencia (por ejemplo, PayPal-Request-Id).
        """
        metodo = metodo.upper()
        url = f"{self.url_base.rstrip('/')}/{ruta.lstrip('/')}" if ruta else self.url_base
        funcion = getattr(requests, metodo.lower())
        espera = self.espera_inicial
        ultimo_error = ""
        codigo = 0
        cuerpo_error = None

        for intento in range(1, self.max_intentos + 1):
            inicio = time.monotonic()
            try:
                opciones = {"params": params, "timeout": self.tiempo_espera}
                if json is not None:
                    opciones["json"] = json
                if data is not None:
                    opciones["data"] = data
                if headers:
                    opciones["headers"] = headers
                if auth:
                    opciones["auth"] = auth

                respuesta = funcion(url, **opciones)
                latencia = int((time.monotonic() - inicio) * 1000)
                codigo = respuesta.status_code

                if respuesta.ok:
                    self._registrar(url, metodo, codigo, latencia, True)
                    return RespuestaServicio(
                        exitoso=True,
                        datos=respuesta.json(),
                        codigo=codigo,
                        latencia_ms=latencia,
                        intentos=intento,
                    )

                ultimo_error = f"HTTP {codigo}"
                self._registrar(url, metodo, codigo, latencia, False, ultimo_error)

                if 400 <= codigo < 500:
                    try:
                        cuerpo_error = respuesta.json()
                    except ValueError:
                        cuerpo_error = None
                    break

            except RequestException as exc:
                latencia = int((time.monotonic() - inicio) * 1000)
                ultimo_error = f"{type(exc).__name__}: {exc}"
                self._registrar(url, metodo, 0, latencia, False, ultimo_error)
            except ValueError as exc:
                latencia = int((time.monotonic() - inicio) * 1000)
                ultimo_error = f"Respuesta no es JSON valido: {exc}"
                self._registrar(url, metodo, codigo, latencia, False, ultimo_error)
                break

            if intento < self.max_intentos:
                time.sleep(espera)
                espera *= 2

        logger.warning(
            "Servicio %s no disponible tras %d intento(s): %s",
            self.nombre_servicio, self.max_intentos, ultimo_error,
        )
        return RespuestaServicio(
            exitoso=False,
            datos=cuerpo_error,
            codigo=codigo,
            mensaje_error=ultimo_error,
            intentos=self.max_intentos,
        )
