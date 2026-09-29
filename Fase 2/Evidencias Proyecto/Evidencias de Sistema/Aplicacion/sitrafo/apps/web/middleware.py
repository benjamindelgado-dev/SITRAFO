"""
Middleware de la aplicacion web.

Implementa el modo mantencion administrado desde la aplicacion de escritorio
(RF-ADM-01): un parametro del sistema suspende la operacion del sitio sin
necesidad de redesplegar.
"""
from django.shortcuts import render

from apps.configuracion.models import ParametroSistema

RUTAS_EXENTAS = ("/admin", "/api", "/static", "/media")


class ModoMantencionMiddleware:
    """Suspende la web del cliente cuando el parametro esta activo."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ruta = request.path

        if any(ruta.startswith(prefijo) for prefijo in RUTAS_EXENTAS):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.es_interno:
            return self.get_response(request)

        if ParametroSistema.obtener("web.modo_mantencion", False):
            mensaje = ParametroSistema.obtener(
                "web.mensaje_mantencion",
                "El sitio se encuentra en mantencion. Volvemos pronto.",
            )
            return render(
                request, "web/mantencion.html", {"mensaje": mensaje}, status=503
            )

        return self.get_response(request)


class CuentaSuspendidaMiddleware:
    """
    Cierra la sesion web de una cuenta suspendida o bloqueada (RF-ADM-03).

    El ingreso ya rechaza estas cuentas; este middleware cubre el caso de una
    cuenta suspendida mientras tenia una sesion abierta.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = request.user
        if (usuario.is_authenticated and not usuario.puede_ingresar
                and not request.path.startswith(RUTAS_EXENTAS)):
            from django.contrib import messages
            from django.contrib.auth import logout
            from django.shortcuts import redirect

            logout(request)
            messages.error(request, "Su cuenta esta suspendida. Contacte al area comercial.")
            return redirect("web:login")
        return self.get_response(request)
