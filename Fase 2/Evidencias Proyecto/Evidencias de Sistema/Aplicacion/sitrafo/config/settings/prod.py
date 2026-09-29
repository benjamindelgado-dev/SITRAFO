"""Configuracion de produccion."""
from .base import *  # noqa: F403

DEBUG = False

# --------------------------------------------------------------------------
# Detras del proxy de Render
# --------------------------------------------------------------------------
# Render termina el HTTPS en su proxy y reenvia la peticion por HTTP. Esta
# cabecera le indica a Django que la peticion original fue segura, para que
# request.is_secure() sea verdadero, no haya bucles de redireccion y las URL
# absolutas (retorno de PayPal, enlaces de correo) se generen con https.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Render define RENDER_EXTERNAL_HOSTNAME (p. ej. sitrafo.onrender.com) en los
# web services. Se agrega a DJANGO_ALLOWED_HOSTS para no depender solo de la
# variable manual.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")  # noqa: F405
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RENDER_EXTERNAL_HOSTNAME]  # noqa: F405

# Origenes confiables para CSRF (formularios web por https). Se arman desde
# DJANGO_CSRF_TRUSTED_ORIGINS (opcional), SITIO_URL y el dominio de Render.
_origenes = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
if SITIO_URL.startswith("https://"):  # noqa: F405
    _origenes.append(SITIO_URL.rstrip("/"))  # noqa: F405
if RENDER_EXTERNAL_HOSTNAME:
    _origenes.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(_origenes))

# --------------------------------------------------------------------------
# Seguridad HTTPS
# --------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# --------------------------------------------------------------------------
# Archivos estaticos (WhiteNoise)
# --------------------------------------------------------------------------
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

EMAIL_BACKEND = "apps.configuracion.services.correo.BrevoEmailBackend"

# --------------------------------------------------------------------------
# Registro en consola
# --------------------------------------------------------------------------
# Con DEBUG=False, Django no muestra los errores 500 en consola por defecto.
# Render solo muestra lo que sale por stdout/stderr, asi que se envia ahi.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", default="INFO"),  # noqa: F405
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
