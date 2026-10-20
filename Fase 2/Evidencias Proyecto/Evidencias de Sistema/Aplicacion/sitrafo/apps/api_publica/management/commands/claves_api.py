"""
Muestra las claves de la API publica y, opcionalmente, los codigos de
seguimiento de los pedidos. Pensado para la demostracion y para entregar
una clave a un sistema externo; se ejecuta en la Shell de Render.

    python manage.py claves_api
    python manage.py claves_api --codigos
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.api_publica.codigos import codigo_seguimiento
from apps.api_publica.seguridad import alcances_de
from apps.comercial.models import OrdenCompra


class Command(BaseCommand):
    help = "Lista los consumidores de la API publica con su clave."

    def add_arguments(self, parser):
        parser.add_argument("--codigos", action="store_true",
                            help="Muestra tambien el codigo de seguimiento de cada pedido.")

    def handle(self, *args, **opciones):
        self.stdout.write("Consumidores de la API publica (encabezado X-API-Key):")
        for nombre, clave in settings.API_PUBLICA_CLAVES.items():
            alcances = alcances_de(nombre)
            servicios = "todos los servicios" if alcances is None else ", ".join(sorted(alcances))
            self.stdout.write(f"  {nombre:<16} {clave}  ({servicios})")
        self.stdout.write(f"Limite: {settings.API_PUBLICA_LIMITE} por consumidor")
        self.stdout.write("Documentacion: /api/publica/v1/docs/")

        if opciones["codigos"]:
            self.stdout.write("\nCodigos de seguimiento:")
            for orden in OrdenCompra.objects.select_related("estado").order_by("numero"):
                self.stdout.write(f"  {orden.numero:<14} {codigo_seguimiento(orden)}  "
                                  f"({orden.estado.nombre})")
