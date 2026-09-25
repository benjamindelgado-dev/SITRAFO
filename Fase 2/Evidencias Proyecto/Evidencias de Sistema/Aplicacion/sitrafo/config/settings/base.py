"""
Configuracion base de SITRAFO.
Compartida por todos los entornos. Lo especifico va en dev.py y prod.py.
"""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="clave-insegura-solo-desarrollo")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# --------------------------------------------------------------------------
# Aplicaciones
# --------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
]

LOCAL_APPS = [
    "apps.common",
    "apps.seguridad",
    "apps.clientes",
    "apps.catalogo",
    "apps.comercial",
    "apps.produccion",
    "apps.inventario",
    "apps.calidad",
    "apps.pagos",
    "apps.configuracion",
    "apps.web",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.web.middleware.ModoMantencionMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------
# Base de datos
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="sitrafo"),
        "USER": env("POSTGRES_USER", default="sitrafo"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="sitrafo"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env.int("POSTGRES_PORT", default=5432),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Modelo de usuario propio: soporta usuarios internos y cuentas web de cliente
AUTH_USER_MODEL = "seguridad.Usuario"

LOGIN_URL = "web:login"
LOGIN_REDIRECT_URL = "web:inicio"
LOGOUT_REDIRECT_URL = "web:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------
# Localizacion: Chile
# --------------------------------------------------------------------------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# Formato chileno: punto como separador de miles, coma como decimal
USE_THOUSAND_SEPARATOR = True

# --------------------------------------------------------------------------
# Archivos estaticos y media
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------------------------------
# API REST
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

# --------------------------------------------------------------------------
# Servicios externos
# --------------------------------------------------------------------------
MINDICADOR_URL = env("MINDICADOR_URL", default="https://mindicador.cl/api")
# feriadito.cl aun no publica su API y apis.digital.gob.cl fue descontinuada
FERIADOS_URL = env("FERIADOS_URL", default="https://date.nager.at/api/v3/PublicHolidays")

# Pasarela de pago. Por defecto apunta al entorno de pruebas (Sandbox).
PAYPAL_API_URL = env("PAYPAL_API_URL", default="https://api-m.sandbox.paypal.com")
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID", default="")
PAYPAL_SECRET = env("PAYPAL_SECRET", default="")

# --------------------------------------------------------------------------
# Autenticacion por token (JWT)
# --------------------------------------------------------------------------
SIMPLE_JWT = {
    # La clave primaria del modelo Usuario es id_usuario, no id
    "USER_ID_FIELD": "id_usuario",
    "USER_ID_CLAIM": "id_usuario",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --------------------------------------------------------------------------
# Parametros de negocio con valor por defecto.
# En ejecucion se leen desde la tabla parametro_sistema.
# --------------------------------------------------------------------------
SITRAFO = {
    "VIGENCIA_COTIZACION_DIAS": 30,
    "ANTICIPO_PORCENTAJE": 50,
    "UMBRAL_DESCUENTO_PCT": 10,
    "MAX_HORAS_DIARIAS": 12,
    "UMBRAL_DESVIACION_COSTO_PCT": 15,
    "INTENTOS_FALLIDOS_MAX": 5,
}
