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


class PermisoPorRol(BasePermission):
    """
    Autorizacion por la matriz de roles (RN-18, RF-SEG-10, CU-SEG-07).

    Cada viewset declara:
    - modulo_permiso: modulo de la matriz. Las acciones estandar se traducen
      a operaciones (list/retrieve -> leer, create -> crear, update ->
      actualizar, destroy -> anular).
    - permisos_accion: permiso de cada accion propia, por ejemplo
      {"emitir": "cotizacion.actualizar"}. Una accion con valor None queda
      deshabilitada para todos, porque debe hacerse por otro camino del flujo.
    - permisos_alternativos: para una accion, lista de permisos de los que
      basta tener uno.
    - acciones_cliente: acciones permitidas a una cuenta web de cliente, que
      no tiene roles; el filtrado por cliente (RN-16) lo hace el queryset.
    - lectura_libre: tablas de referencia que cualquier cuenta puede leer.

    Lo que no esta declarado se deniega. Cada denegacion queda registrada en
    la bitacora de auditoria.
    """

    OPERACION_POR_ACCION = {
        "list": "leer",
        "retrieve": "leer",
        "create": "crear",
        "update": "actualizar",
        "partial_update": "actualizar",
        "destroy": "anular",
    }

    message = "Su rol no autoriza esta operacion."

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False

        accion = getattr(view, "action", None)
        if getattr(view, "lectura_libre", False) and accion in ("list", "retrieve"):
            return True

        permisos_accion = getattr(view, "permisos_accion", {})
        if accion in permisos_accion and permisos_accion[accion] is None:
            self.message = "Esta operacion no esta disponible por esta via."
            return self._denegar(request, view, accion, None)

        if not usuario.es_interno:
            if accion in getattr(view, "acciones_cliente", ()):
                return True
            self.message = "Esta operacion es exclusiva de usuarios internos."
            return self._denegar(request, view, accion, None)

        if usuario.is_superuser:
            return True

        requeridos = self.permisos_requeridos(view, accion)
        if requeridos and any(usuario.has_perm(p) for p in requeridos):
            return True
        return self._denegar(request, view, accion, requeridos)

    def permisos_requeridos(self, view, accion) -> list[str]:
        alternativos = getattr(view, "permisos_alternativos", {})
        if accion in alternativos:
            return list(alternativos[accion])
        codigo = getattr(view, "permisos_accion", {}).get(accion)
        if codigo:
            return [codigo]
        modulo = getattr(view, "modulo_permiso", None)
        operacion = self.OPERACION_POR_ACCION.get(accion)
        if modulo and operacion:
            return [f"{modulo}.{operacion}"]
        return []

    @staticmethod
    def _denegar(request, view, accion, requeridos) -> bool:
        # El navegador de la API evalua permisos de otros metodos para dibujar
        # sus formularios; esas consultas no son intentos reales y no se auditan.
        if request.method != getattr(request, "_request", request).method:
            return False
        registrar_acceso_denegado(request, view, accion, requeridos)
        return False


def registrar_acceso_denegado(request, view, accion, requeridos=None) -> None:
    """Deja el intento denegado en la bitacora (RN-16, CU-SEG-07)."""
    from apps.seguridad.models import Auditoria

    usuario = request.user
    if not (usuario and usuario.is_authenticated):
        return
    try:
        lookup = getattr(view, "lookup_url_kwarg", None) or getattr(view, "lookup_field", "pk")
        Auditoria.objects.create(
            usuario=usuario,
            entidad=getattr(view, "basename", None) or type(view).__name__,
            id_registro=str(view.kwargs.get(lookup, "-"))[:40],
            accion=Auditoria.Accion.ACCESO_DENEGADO,
            valor_nuevo={"accion": accion, "metodo": request.method,
                         "permiso_requerido": requeridos},
            origen=(Auditoria.Origen.ESCRITORIO if usuario.es_interno
                    else Auditoria.Origen.WEB),
        )
    except Exception:  # noqa: BLE001
        # La auditoria nunca debe convertir una denegacion en un error 500
        pass
