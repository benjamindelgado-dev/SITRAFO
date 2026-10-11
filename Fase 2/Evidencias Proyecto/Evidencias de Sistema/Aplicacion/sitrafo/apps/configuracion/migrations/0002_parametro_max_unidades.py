"""
Crea el parametro comercial.max_unidades_solicitud (hallazgo H-02 del EVI-01)
en las bases que ya tienen los parametros sembrados, para que el
Administrador pueda editarlo desde el escritorio.

Si la base aun no tiene usuarios (instalacion nueva), no hace nada: el
parametro lo crea cargar_parametros y mientras tanto rige el valor de
settings.SITRAFO.
"""
from django.db import migrations


def crear(apps, schema_editor):
    ParametroSistema = apps.get_model("configuracion", "ParametroSistema")
    Usuario = apps.get_model("seguridad", "Usuario")
    usuario = Usuario.objects.filter(is_superuser=True).order_by("pk").first()
    if usuario is None or not ParametroSistema.objects.exists():
        return
    ParametroSistema.objects.get_or_create(
        clave="comercial.max_unidades_solicitud",
        defaults={
            "valor": "500", "tipo_dato": "numerico", "ambito": "comercial",
            "descripcion": "Maximo de unidades por solicitud de presupuesto y por "
                           "linea de cotizacion.",
            "usuario": usuario,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("configuracion", "0001_initial"),
        ("seguridad", "0001_initial"),
    ]

    operations = [migrations.RunPython(crear, migrations.RunPython.noop)]
