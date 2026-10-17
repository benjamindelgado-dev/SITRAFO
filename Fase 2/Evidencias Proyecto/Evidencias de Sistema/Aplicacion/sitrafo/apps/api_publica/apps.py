from django.apps import AppConfig


class ApiPublicaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_publica"
    verbose_name = "API publica de SITRAFO"

    def ready(self):
        # Registra el esquema de seguridad de la clave de API en la documentacion
        from . import esquema  # noqa: F401
