"""
Configuracion para la ejecucion de pruebas.

Usa una base en memoria para que la suite sea rapida y no dependa del
contenedor de PostgreSQL. Las llamadas a servicios externos se simulan con
dobles de prueba, de modo que la suite no dependa de la disponibilidad real
de los servicios.
"""
from .base import *  # noqa: F403

DEBUG = False
# Clave propia de las pruebas, con el largo que exige la firma de los JWT
SECRET_KEY = "clave-de-pruebas-sitrafo-no-usar-fuera-de-la-suite-0123456789"
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

# Las pruebas no dependen del .env de quien las ejecuta: dentro de Docker las
# variables del .env llegan al proceso, y un desvio de correo o una clave real
# cambiaria el comportamiento que se esta verificando.
CORREO_REDIRIGIR_A = ""
CORREO_COPIA_A = ""
BREVO_API_KEY = ""
PAYPAL_CLIENT_ID = ""
PAYPAL_SECRET = ""
DEFAULT_FROM_EMAIL = "SITRAFO <no-responder@sitrafo.cl>"
SITIO_URL = "http://localhost:8000"
