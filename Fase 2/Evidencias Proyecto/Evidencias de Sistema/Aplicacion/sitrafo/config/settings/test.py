"""
Configuracion para la ejecucion de pruebas.

Usa una base en memoria para que la suite sea rapida y no dependa del
contenedor de PostgreSQL. Las llamadas a servicios externos se simulan con
dobles de prueba, de modo que la suite no dependa de la disponibilidad real
de los servicios.
"""
from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["*", "testserver"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Hash rapido: las pruebas no evaluan la robustez del algoritmo
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = []

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
