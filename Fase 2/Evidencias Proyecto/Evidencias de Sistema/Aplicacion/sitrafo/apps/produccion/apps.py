from django.apps import AppConfig


class ProduccionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.produccion"
    verbose_name = "Empleados, ordenes de trabajo, tareas, consumos y horas hombre."
