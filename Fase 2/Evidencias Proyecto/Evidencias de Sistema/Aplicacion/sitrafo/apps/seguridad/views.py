"""Vistas de la API para el dominio de seguridad."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.common.permissions import CuentaOperativa

from .models import Permiso


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
