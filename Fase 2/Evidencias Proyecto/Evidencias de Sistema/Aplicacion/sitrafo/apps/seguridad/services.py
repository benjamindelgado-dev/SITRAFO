"""
Administracion de usuarios internos (CU-SEG-02, CU-SEG-03).

Reglas:
- Un usuario interno opera solo con al menos un rol (RN-18).
- El administrador no puede suspenderse a si mismo ni quitarse el rol de
  administrador: evitaria quedar el sistema sin quien lo administre.
- Una cuenta de superusuario solo la modifica otro superusuario.
- Un empleado del taller se asocia a un solo usuario.
- La clave cumple la politica de validadores de Django; si no se indica, se
  genera una temporal que se muestra una sola vez.
- Todo cambio queda en la bitacora de auditoria.
"""
import secrets
import string

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .matriz import ADMIN
from .models import Auditoria, Rol, Usuario, UsuarioRol


class ErrorUsuario(Exception):
    """Regla que impide la operacion sobre la cuenta."""


def generar_clave_temporal(largo: int = 12) -> str:
    alfabeto = string.ascii_letters + string.digits
    while True:
        clave = "".join(secrets.choice(alfabeto) for _ in range(largo))
        if any(c.isdigit() for c in clave) and any(c.isalpha() for c in clave):
            return clave


def _validar_clave(clave: str, usuario: Usuario | None = None):
    try:
        validate_password(clave, usuario)
    except ValidationError as error:
        raise ErrorUsuario(" ".join(error.messages)) from None


def _auditar(actor, usuario, accion, anterior, nuevo):
    Auditoria.objects.create(
        usuario=actor, entidad="usuario", id_registro=str(usuario.pk), accion=accion,
        valor_anterior=anterior, valor_nuevo=nuevo, origen=Auditoria.Origen.ESCRITORIO,
    )


def _roles_de(usuario) -> list[str]:
    return sorted(usuario.roles.values_list("nombre", flat=True))


def _proteger(actor, usuario):
    if usuario.is_superuser and not actor.is_superuser:
        raise ErrorUsuario("Una cuenta de superusuario solo la modifica otro superusuario.")
    if not usuario.es_interno:
        raise ErrorUsuario("Las cuentas de cliente web se administran aparte.")


def _asignar_roles(usuario, roles: list[Rol]):
    if not roles:
        raise ErrorUsuario("Asigne al menos un rol: sin rol el usuario no puede operar.")
    inactivos = [r.nombre for r in roles if not r.activo]
    if inactivos:
        raise ErrorUsuario(f"Rol inactivo: {', '.join(inactivos)}.")
    UsuarioRol.objects.filter(usuario=usuario).exclude(rol__in=roles).delete()
    for rol in roles:
        UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol)


def _asociar_empleado(usuario, empleado):
    from apps.produccion.models import Empleado

    actual = getattr(usuario, "empleado", None)
    if empleado is None:
        if actual:
            actual.usuario = None
            actual.save(update_fields=["usuario"])
        return
    if empleado.usuario_id and empleado.usuario_id != usuario.pk:
        raise ErrorUsuario(
            f"{empleado.nombre} ya esta asociado al usuario {empleado.usuario.username}."
        )
    if actual and actual.pk != empleado.pk:
        actual.usuario = None
        actual.save(update_fields=["usuario"])
    Empleado.objects.filter(pk=empleado.pk).update(usuario=usuario)


@transaction.atomic
def crear_usuario(actor, *, username, email, roles, empleado=None, clave=None
                  ) -> tuple[Usuario, str]:
    """Crea un usuario interno. Devuelve el usuario y la clave asignada."""
    clave = clave or generar_clave_temporal()
    _validar_clave(clave)
    usuario = Usuario.objects.create_user(username, email, clave, es_interno=True)
    _asignar_roles(usuario, roles)
    _asociar_empleado(usuario, empleado)
    _auditar(actor, usuario, Auditoria.Accion.CREACION, None,
             {"username": username, "roles": _roles_de(usuario),
              "empleado": empleado.nombre if empleado else None})
    return usuario, clave


@transaction.atomic
def actualizar_usuario(actor, usuario, *, email=None, roles=None, empleado="sin_cambio"):
    _proteger(actor, usuario)
    anterior = {"email": usuario.email, "roles": _roles_de(usuario),
                "empleado": getattr(getattr(usuario, "empleado", None), "nombre", None)}

    if roles is not None:
        if (usuario.pk == actor.pk and any(r == ADMIN for r in anterior["roles"])
                and not any(r.nombre == ADMIN for r in roles)):
            raise ErrorUsuario("No puede quitarse a si mismo el rol de Administrador.")
        _asignar_roles(usuario, roles)
    if email is not None and email != usuario.email:
        usuario.email = email
        usuario.save(update_fields=["email"])
    if empleado != "sin_cambio":
        _asociar_empleado(usuario, empleado)

    usuario.refresh_from_db()
    nuevo = {"email": usuario.email, "roles": _roles_de(usuario),
             "empleado": getattr(getattr(usuario, "empleado", None), "nombre", None)}
    cambios = {k: v for k, v in nuevo.items() if anterior[k] != v}
    if cambios:
        _auditar(actor, usuario, Auditoria.Accion.MODIFICACION,
                 {k: anterior[k] for k in cambios}, cambios)
    return usuario


def cambiar_estado(actor, usuario, estado: str) -> Usuario:
    """Suspende o reactiva la cuenta. Reactivar tambien levanta un bloqueo."""
    _proteger(actor, usuario)
    if usuario.pk == actor.pk:
        raise ErrorUsuario("No puede cambiar el estado de su propia cuenta.")
    anterior = usuario.estado
    usuario.estado = estado
    usuario.intentos_fallidos = 0
    usuario.save(update_fields=["estado", "intentos_fallidos"])
    _auditar(actor, usuario, Auditoria.Accion.MODIFICACION,
             {"estado": anterior}, {"estado": estado})
    return usuario


def restablecer_clave(actor, usuario, clave: str | None = None) -> str:
    _proteger(actor, usuario)
    clave = clave or generar_clave_temporal()
    _validar_clave(clave, usuario)
    usuario.set_password(clave)
    usuario.intentos_fallidos = 0
    if usuario.estado == Usuario.Estado.BLOQUEADO:
        usuario.estado = Usuario.Estado.ACTIVO
    usuario.save(update_fields=["password", "intentos_fallidos", "estado"])
    _auditar(actor, usuario, Auditoria.Accion.MODIFICACION,
             None, {"clave": "restablecida"})
    return clave
