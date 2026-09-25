"""
Carga los roles y la matriz de permisos de la ERS-01, seccion 8.2.

Es idempotente: agrega lo que falta y no quita permisos que un
administrador haya otorgado despues desde la administracion.

Uso:
    python manage.py cargar_roles
    python manage.py cargar_roles --usuarios-demo   # un usuario por rol
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.seguridad import matriz
from apps.seguridad.models import Permiso, Rol, RolPermiso, Usuario, UsuarioRol

CLAVE_DEMO = "Clave123456"

# usuario, correo, rol
USUARIOS_DEMO = [
    ("administrador", "administrador@sitrafo.cl", matriz.ADMIN),
    ("comercial", "comercial@sitrafo.cl", matriz.COMERCIAL),
    ("comercial2", "comercial2@sitrafo.cl", matriz.COMERCIAL),
    ("produccion", "produccion@sitrafo.cl", matriz.PRODUCCION),
    ("operario", "operario@sitrafo.cl", matriz.OPERARIO),
    ("calidad", "calidad@sitrafo.cl", matriz.CALIDAD),
    ("bodega", "bodega@sitrafo.cl", matriz.BODEGA),
]


class Command(BaseCommand):
    help = "Carga los roles y la matriz de permisos por rol."

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuarios-demo", action="store_true",
            help=f"Crea un usuario interno por rol, con clave {CLAVE_DEMO}.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        permisos = {}
        for codigo, modulo, operacion in matriz.todos_los_permisos():
            permisos[codigo], _ = Permiso.objects.get_or_create(
                codigo=codigo, defaults={"modulo": modulo, "operacion": operacion}
            )

        otorgados = 0
        for nombre, descripcion in matriz.ROLES.items():
            rol, _ = Rol.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": descripcion}
            )
            for codigo in matriz.permisos_de_rol(nombre):
                _, nuevo = RolPermiso.objects.get_or_create(rol=rol, permiso=permisos[codigo])
                otorgados += int(nuevo)

        self.stdout.write(self.style.SUCCESS(
            f"Roles: {Rol.objects.count()}. Permisos: {Permiso.objects.count()}. "
            f"Asignaciones nuevas: {otorgados}."
        ))

        if options["usuarios_demo"]:
            self._usuarios_demo()

    def _usuarios_demo(self):
        self.stdout.write("")
        self.stdout.write(f"  Usuarios de demostracion (clave {CLAVE_DEMO}):")
        for username, correo, nombre_rol in USUARIOS_DEMO:
            usuario, creado = Usuario.objects.get_or_create(
                username=username, defaults={"email": correo, "es_interno": True},
            )
            if creado:
                usuario.set_password(CLAVE_DEMO)
                usuario.save()
            UsuarioRol.objects.get_or_create(
                usuario=usuario, rol=Rol.objects.get(nombre=nombre_rol)
            )
            self.stdout.write(f"    {username:<14} {nombre_rol}")
