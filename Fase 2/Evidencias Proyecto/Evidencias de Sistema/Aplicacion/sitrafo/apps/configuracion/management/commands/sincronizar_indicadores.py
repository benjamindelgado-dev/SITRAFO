"""
Descarga los indicadores economicos del dia desde mindicador.cl.

Uso:
    python manage.py sincronizar_indicadores

Pensado para ejecutarse una vez al dia de forma automatica.
"""
from django.core.management.base import BaseCommand

from apps.configuracion.services.indicadores import ClienteIndicadores


class Command(BaseCommand):
    help = "Sincroniza UF, UTM y dolar desde mindicador.cl"

    def handle(self, *args, **options):
        resultado = ClienteIndicadores().sincronizar_dia()

        if not resultado["exitoso"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Servicio no disponible: {resultado['error']}. "
                    "El sistema seguira operando con el ultimo valor almacenado."
                )
            )
            return

        for codigo, fecha, valor in resultado["almacenados"]:
            self.stdout.write(f"  {codigo} {fecha}: {valor}")
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(resultado['almacenados'])} indicador(es) actualizado(s)."
            )
        )
