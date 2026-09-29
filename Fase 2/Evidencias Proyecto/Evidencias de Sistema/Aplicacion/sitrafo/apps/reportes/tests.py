"""Pruebas de los reportes de gestion (RF-REP-01 a RF-REP-06)."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.comercial.test_flujo import _cotizar, flujo  # noqa: F401
from apps.seguridad import matriz
from apps.seguridad.models import Rol, Usuario, UsuarioRol

TIPOS = ["comercial", "costos", "consumos", "horas", "plazos"]


def _api(rol):
    usuario = Usuario.objects.create_user(f"u{rol[:4]}", f"{rol[:4]}@s.cl", "Clave123456",
                                          es_interno=True)
    UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    api = APIClient()
    api.force_authenticate(usuario)
    return api


@pytest.mark.django_db
@pytest.mark.parametrize("tipo", TIPOS)
def test_cada_reporte_responde_y_exporta(tipo):
    call_command("cargar_roles", verbosity=0)
    api = _api(matriz.COMERCIAL)
    datos = api.get(f"/api/v1/reportes/{tipo}/")
    assert datos.status_code == 200, datos.data
    assert datos.data["columnas"] and "periodo" in datos.data

    excel = api.get(f"/api/v1/reportes/{tipo}/?formato=xlsx")
    assert excel.status_code == 200 and excel.content[:2] == b"PK"
    pdf = api.get(f"/api/v1/reportes/{tipo}/?formato=pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_reporte_comercial_cuenta_el_embudo(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    flujo["interno"].post(f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/emitir/")
    flujo["externo"].post(f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/aceptar/")

    datos = flujo["interno"].get("/api/v1/reportes/comercial/").data
    # Total: 1 solicitud, 1 emitida, 1 aceptada, 100 % de conversion
    assert datos["totales"][1:5] == ["1", "1", "1", "100.0"]


@pytest.mark.django_db
def test_reportes_segun_rol_y_validacion_de_fechas():
    call_command("cargar_roles", verbosity=0)
    assert _api(matriz.OPERARIO).get("/api/v1/reportes/costos/").status_code == 403
    bodega = _api(matriz.BODEGA)
    assert bodega.get("/api/v1/reportes/consumos/").status_code == 200
    assert bodega.get("/api/v1/reportes/costos/?desde=2026-12-01&hasta=2026-01-01"
                      ).status_code == 400
    assert bodega.get("/api/v1/reportes/inexistente/").status_code == 404
