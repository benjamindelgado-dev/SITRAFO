"""
Control de acceso de la API publica.

Cada consumidor (el portal web u otro sistema) se identifica con una clave
de API en el encabezado X-API-Key. Las claves se definen en la configuracion
(variable de entorno API_PUBLICA_CLAVES) y nunca en el repositorio. Ademas,
cada clave tiene un limite de solicitudes por minuto.
"""
import hmac

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework.throttling import SimpleRateThrottle

ENCABEZADO = "X-API-Key"


def consumidor_de_clave(clave: str) -> str | None:
    """Nombre del consumidor dueño de la clave, o None si no existe."""
    for nombre, valida in settings.API_PUBLICA_CLAVES.items():
        if valida and hmac.compare_digest(valida, clave):
            return nombre
    return None


class ClaveApiAutenticacion(BaseAuthentication):
    """Identifica al consumidor por su clave de API."""

    def authenticate(self, request):
        clave = request.headers.get(ENCABEZADO)
        if not clave:
            return None
        consumidor = consumidor_de_clave(clave)
        if consumidor is None:
            raise AuthenticationFailed("Clave de API invalida.")
        return AnonymousUser(), consumidor

    def authenticate_header(self, request):
        # Hace que la falta de clave responda 401 en lugar de 403
        return 'ApiKey realm="SITRAFO"'


class TieneClaveApi(BasePermission):
    message = f"Debe enviar una clave de API valida en el encabezado {ENCABEZADO}."

    def has_permission(self, request, view):
        return bool(request.auth)


class LimitePorClave(SimpleRateThrottle):
    """Limite de solicitudes por consumidor (por defecto, 60 por minuto)."""

    scope = "api_publica"

    def get_rate(self):
        return settings.API_PUBLICA_LIMITE

    def get_cache_key(self, request, view):
        identidad = request.auth or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": identidad}
