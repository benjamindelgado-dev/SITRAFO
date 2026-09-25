from django.apps import AppConfig


class SeguridadConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.seguridad"
    verbose_name = "Usuarios, roles, permisos y auditoria."
