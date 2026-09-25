"""Configuracion de desarrollo."""
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_extensions"]  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# En desarrollo se relaja la politica de contrasenas para agilizar pruebas
AUTH_PASSWORD_VALIDATORS = []
