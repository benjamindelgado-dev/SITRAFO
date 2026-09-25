"""Rutas de la aplicacion web del cliente."""
from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    # Acceso
    path("acceso/", views.LoginClienteView.as_view(), name="login"),
    path("salir/", views.LogoutClienteView.as_view(), name="logout"),
    path("registro/", views.RegistroView.as_view(), name="registro"),

    # Inicio
    path("", views.inicio, name="inicio"),

    # Catalogo
    path("catalogo/", views.catalogo, name="catalogo"),
    path("catalogo/<int:pk>/", views.ficha_modelo, name="ficha_modelo"),

    # Solicitudes
    path("solicitar/", views.solicitar_presupuesto, name="solicitar"),
    path("mis-solicitudes/", views.mis_solicitudes, name="mis_solicitudes"),

    # Cotizaciones
    path("mis-cotizaciones/", views.mis_cotizaciones, name="mis_cotizaciones"),
    path("cotizacion/<int:pk>/", views.detalle_cotizacion, name="detalle_cotizacion"),
    path("cotizacion/<int:pk>/aceptar/", views.aceptar_cotizacion, name="aceptar_cotizacion"),
    path("cotizacion/<int:pk>/rechazar/", views.rechazar_cotizacion, name="rechazar_cotizacion"),

    # Pedidos
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),
    path("seguimiento/<int:pk>/", views.seguimiento, name="seguimiento"),

    # Pago en linea
    path("cobro/<int:pk>/", views.documento_cobro, name="documento_cobro"),
    path("cobro/<int:pk>/pagar/", views.pagar_documento, name="pagar_documento"),
    path("pago/retorno/", views.pago_retorno, name="pago_retorno"),
    path("pago/cancelado/", views.pago_cancelado, name="pago_cancelado"),

    # Cuenta
    path("perfil/", views.perfil, name="perfil"),
]
