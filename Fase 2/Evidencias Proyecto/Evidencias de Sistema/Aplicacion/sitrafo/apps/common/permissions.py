"""
Permisos de la API REST.

El acceso se deniega por defecto y se concede contra la matriz rol_permiso
(RN-18, RF-SEG-10). La aplicacion de escritorio y la web usan estos mismos
permisos, porque ambas consumen la misma API.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class CuentaOperativa(BasePermission):
    """Exige una cuenta autenticada, activa y no suspendida (RF-ADM-03)."""

    message = "La cuenta no se encuentra habilitada para operar."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario and usuario.is_authenticated and usuario.puede_ingresar
        )


class TienePermisoDeModulo(BasePermission):
    """
    Resuelve el permiso contra la matriz rol_permiso.

    La vista declara el atributo modulo_permiso; la operacion se deduce del
    metodo HTTP. Ejemplo: modulo_permiso = "cotizacion" exige el permiso
    cotizacion.leer para GET y cotizacion.crear para POST.
    """

    OPERACION_POR_METODO = {
        "GET": "leer",
        "HEAD": "leer",
        "OPTIONS": "leer",
        "POST": "crear",
        "PUT": "actualizar",
        "PATCH": "actualizar",
        "DELETE": "anular",
    }

    message = "El rol asignado no autoriza esta operacion."

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if usuario.is_superuser:
            return True

        modulo = getattr(view, "modulo_permiso", None)
        if modulo is None:
            return False

        operacion = self.OPERACION_POR_METODO.get(request.method, "leer")
        return usuario.has_perm(f"{modulo}.{operacion}")


class EsUsuarioInterno(BasePermission):
    """Restringe la vista a funcionarios; excluye cuentas web de cliente."""

    message = "Esta operacion es exclusiva de usuarios internos."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.es_interno)


class SoloLecturaParaCliente(BasePermission):
    """El cliente web puede consultar, pero no modificar."""

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        if usuario.es_interno:
            return True
        return request.method in SAFE_METHODS
