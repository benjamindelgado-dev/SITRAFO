"""Configuracion de desarrollo."""
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_extensions"]  # noqa: F405

# Con clave de Brevo los correos salen de verdad; sin ella, se muestran en la
# consola del contenedor (docker compose logs web)
EMAIL_BACKEND = (
    "apps.configuracion.services.correo.BrevoEmailBackend"
    if BREVO_API_KEY  # noqa: F405
    else "django.core.mail.backends.console.EmailBackend"
)

# En desarrollo se relaja la politica de contrasenas para agilizar pruebas
AUTH_PASSWORD_VALIDATORS = []
