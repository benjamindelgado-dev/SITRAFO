from django.apps import AppConfig


class ConfiguracionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.configuracion"
    verbose_name = "Parametros del sistema, avisos del sitio, feriados y log de integraciones."
