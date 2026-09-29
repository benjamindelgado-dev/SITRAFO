"""Vistas de la API para el dominio de seguridad."""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import CuentaOperativa, PermisoPorRol
from apps.configuracion.models import ParametroSistema

from . import services
from .models import Auditoria, Permiso, Rol, Usuario
from .serializers import (
    AuditoriaSerializer,
    RolSerializer,
    UsuarioEntradaSerializer,
    UsuarioInternoSerializer,
)


@api_view(["GET"])
@permission_classes([CuentaOperativa])
def yo(request):
    """
    Identidad, roles y permisos efectivos del usuario autenticado.

    La aplicacion de escritorio lo consulta al iniciar sesion para mostrar
    solo los paneles y acciones que el rol autoriza. Es una ayuda de
    interfaz: la autorizacion real la aplica la API en cada operacion.
    """
    usuario = request.user
    if usuario.is_superuser:
        permisos = sorted(Permiso.objects.values_list("codigo", flat=True))
    else:
        permisos = sorted(usuario.codigos_permiso())
    return Response({
        "id_usuario": usuario.pk,
        "username": usuario.username,
        "es_interno": usuario.es_interno,
        "es_superusuario": usuario.is_superuser,
        "roles": [r.nombre for r in usuario.roles.filter(activo=True)],
        "permisos": permisos,
    })


# ---------------------------------------------------------------------------
# Administracion de usuarios internos (CU-SEG-02, CU-SEG-03)
# ---------------------------------------------------------------------------

def _empleado(id_empleado):
    if id_empleado is None:
        return None
    from apps.produccion.models import Empleado

    return get_object_or_404(Empleado, pk=id_empleado, activo=True)


def _conflicto(error):
    return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)


class RolViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Roles y matriz de permisos (RF-SEG-02). El Administrador consulta y
    modifica que operaciones otorga cada rol; el cambio rige desde la
    peticion siguiente de cada usuario.
    """

    queryset = Rol.objects.filter(activo=True).prefetch_related("permisos_asignados")
    serializer_class = RolSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    permisos_alternativos = {"list": ["usuario.leer", "rol.leer"],
                             "retrieve": ["usuario.leer", "rol.leer"]}
    permisos_accion = {"matriz": "rol.leer", "permiso": "rol.actualizar"}
    pagination_class = None

    # Sin estos permisos nadie podria volver a administrar usuarios ni roles
    PROTEGIDOS_ADMIN = {"usuario.leer", "usuario.actualizar", "rol.leer", "rol.actualizar"}

    @action(detail=True, methods=["get"])
    def matriz(self, request, pk=None):
        from .matriz import MATRIZ

        rol = self.get_object()
        otorgados = set(rol.permisos_asignados.values_list("permiso__codigo", flat=True))
        modulos = {}
        for permiso in Permiso.objects.order_by("modulo", "codigo"):
            fila = modulos.setdefault(permiso.modulo, {
                "modulo": permiso.modulo,
                "descripcion": MATRIZ.get(permiso.modulo, (permiso.modulo,))[0],
                "operaciones": {},
            })
            fila["operaciones"][permiso.codigo.split(".", 1)[1]] = permiso.codigo in otorgados
        return Response({"rol": rol.nombre, "modulos": list(modulos.values())})

    @action(detail=True, methods=["post"])
    def permiso(self, request, pk=None):
        from .matriz import ADMIN
        from .models import RolPermiso

        rol = self.get_object()
        codigo = request.data.get("codigo", "")
        otorgar = bool(request.data.get("otorgar"))
        permiso = Permiso.objects.filter(codigo=codigo).first()
        if permiso is None:
            return Response({"detalle": "Permiso desconocido."},
                            status=status.HTTP_404_NOT_FOUND)
        if rol.nombre == ADMIN and not otorgar and codigo in self.PROTEGIDOS_ADMIN:
            return Response({"detalle": "El Administrador no puede perder la gestion de "
                                        "usuarios y roles."},
                            status=status.HTTP_409_CONFLICT)
        if otorgar:
            RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)
        else:
            RolPermiso.objects.filter(rol=rol, permiso=permiso).delete()
        Auditoria.objects.create(
            usuario=request.user, entidad="rol", id_registro=str(rol.pk),
            accion=Auditoria.Accion.MODIFICACION,
            valor_anterior={"permiso": codigo, "otorgado": not otorgar},
            valor_nuevo={"permiso": codigo, "otorgado": otorgar, "rol": rol.nombre},
            origen=Auditoria.Origen.ESCRITORIO,
        )
        return self.matriz(request, pk)


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Usuarios internos. Las altas y cambios pasan por las reglas de
    apps/seguridad/services.py; la respuesta de alta y de restablecimiento
    incluye la clave temporal, que no vuelve a mostrarse.
    """

    queryset = (Usuario.objects.filter(es_interno=True)
                .prefetch_related("roles").select_related("empleado").order_by("username"))
    serializer_class = UsuarioInternoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "usuario"
    permisos_accion = {
        "create": "usuario.crear",
        "partial_update": "usuario.actualizar",
        "suspender": "usuario.actualizar",
        "reactivar": "usuario.actualizar",
        "restablecer_clave": "usuario.actualizar",
    }
    pagination_class = None

    def create(self, request):
        entrada = UsuarioEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        faltan = [c for c in ("username", "email") if not datos.get(c)]
        if faltan:
            return Response({c: "Este campo es obligatorio." for c in faltan},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            usuario, clave = services.crear_usuario(
                request.user, username=datos["username"], email=datos["email"],
                roles=datos.get("roles", []), empleado=_empleado(datos.get("empleado")),
                clave=datos.get("clave") or None,
            )
        except services.ErrorUsuario as error:
            return _conflicto(error)
        respuesta = dict(self.get_serializer(self.get_queryset().get(pk=usuario.pk)).data)
        respuesta["clave_temporal"] = clave
        return Response(respuesta, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        usuario = self.get_object()
        entrada = UsuarioEntradaSerializer(instance=usuario, data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            services.actualizar_usuario(
                request.user, usuario, email=datos.get("email"), roles=datos.get("roles"),
                empleado=(_empleado(datos["empleado"]) if "empleado" in datos
                          else "sin_cambio"),
            )
        except services.ErrorUsuario as error:
            return _conflicto(error)
        return Response(self.get_serializer(self.get_queryset().get(pk=usuario.pk)).data)

    def _estado(self, estado):
        usuario = self.get_object()
        try:
            services.cambiar_estado(self.request.user, usuario, estado)
        except services.ErrorUsuario as error:
            return _conflicto(error)
        return Response(self.get_serializer(self.get_queryset().get(pk=usuario.pk)).data)

    @action(detail=True, methods=["post"])
    def suspender(self, request, pk=None):
        return self._estado(Usuario.Estado.SUSPENDIDO)

    @action(detail=True, methods=["post"])
    def reactivar(self, request, pk=None):
        return self._estado(Usuario.Estado.ACTIVO)

    @action(detail=True, methods=["post"])
    def restablecer_clave(self, request, pk=None):
        usuario = self.get_object()
        try:
            clave = services.restablecer_clave(request.user, usuario,
                                               request.data.get("clave") or None)
        except services.ErrorUsuario as error:
            return _conflicto(error)
        return Response({"clave_temporal": clave})


# ---------------------------------------------------------------------------
# Ingreso con token (escritorio): bloqueo por intentos y ultimo acceso
# ---------------------------------------------------------------------------
def registrar_intento(usuario):
    usuario.registrar_intento_fallido(
        int(ParametroSistema.obtener("sistema.intentos_fallidos_max", 5)),
        int(ParametroSistema.obtener("sistema.minutos_bloqueo", 15)),
    )


def mensaje_cuenta_no_disponible(usuario) -> str:
    if usuario.estado == Usuario.Estado.BLOQUEADO and usuario.bloqueado_hasta:
        hora = timezone.localtime(usuario.bloqueado_hasta).strftime("%H:%M")
        return (f"Demasiados intentos fallidos: la cuenta esta bloqueada hasta las {hora}. "
                "Puede esperar o pedir al administrador que la reactive.")
    return (f"La cuenta esta {usuario.get_estado_display().lower()}. "
            "Contacte al administrador.")


class IngresoConControl(TokenObtainPairView):
    """
    Emite el token JWT aplicando las reglas de la cuenta (RF-SEG-04):

    - Una cuenta suspendida o bloqueada no recibe token.
    - Cada clave incorrecta suma un intento; al llegar al maximo configurado
      la cuenta se bloquea y solo el administrador puede reactivarla.
    - Un ingreso exitoso reinicia los intentos y registra el ultimo acceso.
    """

    def post(self, request, *args, **kwargs):
        usuario = Usuario.objects.filter(
            username=(request.data.get("username") or "").strip()
        ).first()
        if usuario:
            usuario.levantar_bloqueo_vencido()
        if usuario and not usuario.puede_ingresar:
            return Response({"detail": mensaje_cuenta_no_disponible(usuario)},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            respuesta = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            if usuario:
                registrar_intento(usuario)
                if usuario.estado == Usuario.Estado.BLOQUEADO:
                    return Response({"detail": mensaje_cuenta_no_disponible(usuario)},
                                    status=status.HTTP_403_FORBIDDEN)
            raise
        if usuario:
            usuario.registrar_acceso_exitoso()
        return respuesta


# ---------------------------------------------------------------------------
# Bitacora de auditoria (HU-12, RF-SEG-06)
# ---------------------------------------------------------------------------
class AuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consulta de la bitacora. Es de solo lectura por diseno: la API no ofrece
    ninguna via para modificar o borrar un registro de auditoria.

    Filtros: usuario (nombre), accion, entidad, origen, desde y hasta
    (AAAA-MM-DD) y buscar (texto en entidad o id del registro).
    """

    serializer_class = AuditoriaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "auditoria"
    permisos_accion = {"entidades": "auditoria.leer"}

    def get_queryset(self):
        consulta = Auditoria.objects.select_related("usuario").order_by("-fecha_hora")
        p = self.request.query_params
        if p.get("usuario"):
            consulta = consulta.filter(usuario__username__iexact=p["usuario"])
        for campo in ("accion", "entidad", "origen"):
            if p.get(campo):
                consulta = consulta.filter(**{campo: p[campo]})
        if p.get("desde"):
            consulta = consulta.filter(fecha_hora__date__gte=p["desde"])
        if p.get("hasta"):
            consulta = consulta.filter(fecha_hora__date__lte=p["hasta"])
        if p.get("buscar"):
            consulta = consulta.filter(
                Q(entidad__icontains=p["buscar"]) | Q(id_registro__icontains=p["buscar"])
            )
        return consulta

    @action(detail=False, methods=["get"])
    def entidades(self, request):
        """Entidades presentes en la bitacora, para el filtro de la interfaz."""
        return Response(sorted(Auditoria.objects.values_list("entidad", flat=True).distinct()))
