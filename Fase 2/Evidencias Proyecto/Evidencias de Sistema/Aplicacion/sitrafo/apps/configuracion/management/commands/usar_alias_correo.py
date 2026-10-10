"""
Cambia los correos de usuarios y contactos de los datos de demostracion por
alias de una casilla de control (direccion+etiqueta@dominio).

Sirve para la marcha blanca con CORREO_COPIA_A: cada correo sale a su
destinatario "real" (el alias del usuario o del contacto) y llega a la casilla
de control sin escribirle a dominios ficticios o de terceros, como maipo.cl.
Gmail y Outlook entregan todo lo que lleva +etiqueta en la misma casilla.

Por defecto solo muestra los cambios. Para aplicarlos:
    python manage.py usar_alias_correo --aplicar
La casilla se toma de CORREO_COPIA_A, o de --base. --conservar excluye
usuarios (por nombre de acceso) o correos, por ejemplo los reales del equipo.
"""
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.clientes.models import ContactoCliente
from apps.configuracion.services.notificaciones import _casilla
from apps.seguridad.models import Usuario


def _etiqueta(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:30] or "x"


class Command(BaseCommand):
    help = "Reemplaza los correos de la demostracion por alias de la casilla de control."

    def add_arguments(self, parser):
        parser.add_argument("--base", default="", help="Casilla de control (por defecto "
                            "CORREO_COPIA_A).")
        parser.add_argument("--aplicar", action="store_true",
                            help="Guarda los cambios (sin esto solo los muestra).")
        parser.add_argument("--conservar", nargs="*", default=[],
                            help="Usuarios o correos que no se modifican.")

    def handle(self, *args, **opciones):
        base = (opciones["base"] or getattr(settings, "CORREO_COPIA_A", "")).strip().lower()
        if "@" not in base:
            raise CommandError("Indique la casilla con --base o defina CORREO_COPIA_A.")
        local, dominio = _casilla(base).split("@")
        conservar = {c.strip().lower() for c in opciones["conservar"]}

        def alias(etiqueta):
            return f"{local}+{etiqueta}@{dominio}"

        def se_conserva(correo, *nombres):
            return (not correo or _casilla(correo) == _casilla(base)
                    or correo.lower() in conservar
                    or any(n.lower() in conservar for n in nombres))

        cambios = []
        usados = set(Usuario.objects.values_list("email", flat=True))
        for usuario in Usuario.objects.order_by("username"):
            if se_conserva(usuario.email, usuario.username):
                continue
            nuevo = alias(_etiqueta(usuario.username))
            if nuevo in usados:                    # el correo de usuario es unico
                nuevo = alias(f"{_etiqueta(usuario.username)}-{usuario.pk}")
            usados.add(nuevo)
            cambios.append(("usuario", usuario, usuario.username, nuevo))

        for contacto in ContactoCliente.objects.select_related("cliente").order_by("pk"):
            if se_conserva(contacto.email):
                continue
            etiqueta = f"{_etiqueta(contacto.cliente.razon_social)[:20].strip('-')}-c{contacto.pk}"
            cambios.append(("contacto", contacto, contacto.nombre, alias(etiqueta)))

        if not cambios:
            self.stdout.write("No hay correos que cambiar.")
            return
        for tipo, objeto, nombre, nuevo in cambios:
            self.stdout.write(f"  {tipo:<9} {nombre:<22} {objeto.email:<34} -> {nuevo}")

        if not opciones["aplicar"]:
            self.stdout.write(self.style.WARNING(
                f"\n{len(cambios)} correo(s) por cambiar. Nada se guardo: "
                "repita con --aplicar para guardar."))
            return
        with transaction.atomic():
            for _, objeto, _, nuevo in cambios:
                objeto.email = nuevo
                objeto.save(update_fields=["email"])
        self.stdout.write(self.style.SUCCESS(f"\n{len(cambios)} correo(s) actualizados."))
