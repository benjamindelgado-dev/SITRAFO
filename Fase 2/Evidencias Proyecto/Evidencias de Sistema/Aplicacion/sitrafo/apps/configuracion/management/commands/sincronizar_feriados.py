"""
Descarga los feriados legales de Chile.

Uso:
    python manage.py sincronizar_feriados
    python manage.py sincronizar_feriados --anio 2027
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.configuracion.services.feriados import ClienteFeriados


class Command(BaseCommand):
    help = "Sincroniza los feriados legales de Chile"

    def add_arguments(self, parser):
        parser.add_argument(
            "--anio",
            type=int,
            default=timezone.localdate().year,
            help="Anio a sincronizar. Por defecto, el actual.",
        )

    def handle(self, *args, **options):
        anio = options["anio"]
        resultado = ClienteFeriados().sincronizar_anio(anio)

        if not resultado["exitoso"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Servicio no disponible: {resultado['error']}. "
                    f"Se conservan los {resultado['total']} feriado(s) ya almacenados."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Feriados {anio}: {resultado['creados']} nuevo(s), "
                f"{resultado['total']} en total."
            )
        )
