"""
Pruebas del formato de montos y del icono del sitio.

Los montos en UF se guardan con 4 decimales, pero al cliente se le muestran
con 2 y con el formato chileno (punto de miles, coma decimal).
"""
from decimal import Decimal

import pytest
from django.template import Context, Template
from django.test import override_settings
from django.utils import translation

from apps.comercial.pdf import numero


def _render(texto: str, **contexto) -> str:
    with translation.override("es-cl"):
        return Template(texto).render(Context(contexto))


def test_uf_con_dos_decimales_y_formato_chileno():
    assert _render("{{ v|floatformat:2 }}", v=Decimal("40.5463")) == "40,55"
    assert _render("{{ v|floatformat:2 }}", v=Decimal("1234.5000")) == "1.234,50"


def test_pesos_con_punto_de_miles():
    assert _render("{{ v|floatformat:0 }}", v=Decimal("1667042.4")) == "1.667.042"


def test_pdf_de_cotizacion_usa_formato_chileno():
    assert numero(Decimal("48.2694"), 2) == "48,27"


@pytest.mark.django_db
def test_plantilla_base_declara_el_icono(client):
    respuesta = client.get("/acceso/")
    assert respuesta.status_code == 200
    assert b'rel="icon"' in respuesta.content
    assert b"img/favicon.ico" in respuesta.content


@pytest.mark.django_db
@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
def test_favicon_en_la_raiz_redirige_al_estatico(client):
    respuesta = client.get("/favicon.ico")
    assert respuesta.status_code == 302
    assert respuesta["Location"].endswith("img/favicon.ico")
