"""Documentacion OpenAPI (Swagger) de la API publica."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension

PREFIJO = "/api/publica/"


def solo_api_publica(endpoints, **kwargs):
    """La documentacion publica muestra solo la API publica, no la interna."""
    return [e for e in endpoints if e[0].startswith(PREFIJO)]


class ClaveApiExtension(OpenApiAuthenticationExtension):
    target_class = "apps.api_publica.seguridad.ClaveApiAutenticacion"
    name = "ClaveApi"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "header", "name": "X-API-Key"}
