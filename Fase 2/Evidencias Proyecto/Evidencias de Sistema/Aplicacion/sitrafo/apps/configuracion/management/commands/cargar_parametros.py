"""
Carga los parametros de configuracion iniciales del sistema.

Uso:
    python manage.py cargar_parametros
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.configuracion.models import ParametroSistema

PARAMETROS = [
    ("web.modo_mantencion", "false", "booleano", "canal_web",
     "Suspende la operacion de la aplicacion web (RF-ADM-01)."),
    ("web.mensaje_mantencion", "Sitio en mantencion. Volvemos pronto.", "texto",
     "canal_web", "Aviso mostrado durante la mantencion."),
    ("web.pago_en_linea_habilitado", "true", "booleano", "canal_web",
     "Habilita el pago en linea en la web (RF-ADM-02)."),
    ("web.autorregistro_habilitado", "true", "booleano", "canal_web",
     "Permite que nuevos clientes se registren solos (RF-CLI-06)."),
    ("comercial.vigencia_cotizacion_dias", "30", "numerico", "comercial",
     "Dias de vigencia de una cotizacion (RN-04)."),
    ("comercial.umbral_descuento_pct", "10", "numerico", "comercial",
     "Descuento sobre el cual se exige aprobacion interna (RN-05)."),
    ("comercial.anticipo_pct", "50", "numerico", "comercial",
     "Porcentaje de anticipo por defecto (RN-15)."),
    ("comercial.margen_defecto_pct", "25", "numerico", "comercial",
     "Margen aplicado por defecto al costo estimado."),
    ("produccion.max_horas_diarias", "12", "numerico", "produccion",
     "Maximo de horas hombre registrables por empleado y dia."),
    ("produccion.umbral_desviacion_costo_pct", "15", "numerico", "produccion",
     "Desviacion sobre la cual se exige justificacion al cerrar (RN-11)."),
    ("sistema.intentos_fallidos_max", "5", "numerico", "sistema",
     "Intentos fallidos antes de bloquear la cuenta (RF-SEG-04)."),
    ("sistema.minutos_inactividad", "30", "numerico", "sistema",
     "Minutos de inactividad antes de cerrar sesion (RF-SEG-07)."),
]


class Command(BaseCommand):
    help = "Carga los parametros de configuracion iniciales."

    def handle(self, *args, **options):
        Usuario = get_user_model()
        usuario = Usuario.objects.filter(is_superuser=True).order_by("pk").first()
        if usuario is None:
            self.stdout.write(
                self.style.ERROR(
                    "No existe un superusuario. Ejecuta primero createsuperuser."
                )
            )
            return

        creados = 0
        for clave, valor, tipo, ambito, descripcion in PARAMETROS:
            _, nuevo = ParametroSistema.objects.get_or_create(
                clave=clave,
                defaults={
                    "valor": valor,
                    "tipo_dato": tipo,
                    "ambito": ambito,
                    "descripcion": descripcion,
                    "usuario": usuario,
                },
            )
            creados += int(nuevo)

        total = ParametroSistema.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Parametros creados: {creados}. Total en el sistema: {total}."
            )
        )
