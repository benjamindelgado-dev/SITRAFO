"""
Geocodificacion de direcciones (RF-CLI-05), quinta integracion externa.

Usa Nominatim (OpenStreetMap): publico y sin clave. Su politica de uso exige
identificar la aplicacion con un User-Agent y no superar una consulta por
segundo, lo que se cumple porque se geocodifica una direccion a la vez, al
registrarla.

Si el servicio no responde, la direccion se guarda igual con validada=False
(RF-INT-03) y puede geocodificarse despues.
"""
from decimal import Decimal

from django.conf import settings

from apps.configuracion.services.base import ClienteServicioExterno

URL_NOMINATIM = "https://nominatim.openstreetmap.org"


class ClienteGeocodificacion(ClienteServicioExterno):
    nombre_servicio = "geocodificacion"
    max_intentos = 2

    def __init__(self, url_base: str | None = None):
        super().__init__(url_base or getattr(settings, "GEOCODIFICACION_URL", URL_NOMINATIM))

    def buscar(self, texto: str) -> tuple[Decimal, Decimal] | None:
        respuesta = self.solicitar(
            "GET", "search",
            params={"q": texto, "format": "json", "limit": 1, "countrycodes": "cl"},
            headers={"User-Agent": "SITRAFO/1.0 (proyecto academico Duoc UC)",
                     "Accept-Language": "es"},
        )
        if not respuesta or not respuesta.datos:
            return None
        primero = respuesta.datos[0]
        return (Decimal(str(primero["lat"])).quantize(Decimal("0.000001")),
                Decimal(str(primero["lon"])).quantize(Decimal("0.000001")))


def geocodificar(direccion, cliente: ClienteGeocodificacion | None = None) -> bool:
    """Completa latitud y longitud de la direccion. Devuelve si se valido."""
    comuna = direccion.comuna
    texto = f"{direccion.calle} {direccion.numero}, {comuna.nombre}, {comuna.region.nombre}, Chile"
    resultado = (cliente or ClienteGeocodificacion()).buscar(texto)
    if resultado is None:
        return False
    direccion.latitud, direccion.longitud = resultado
    direccion.validada = True
    direccion.save(update_fields=["latitud", "longitud", "validada"])
    return True
