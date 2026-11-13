"""
Cabeceras de seguridad del portal (RNF-03).

Pruebas de regresion de las correcciones de las alertas de OWASP ZAP
(H-01 a H-04 del PPR-01, tarea S3-13): politica de seguridad de contenido,
recursos de terceros, cookie CSRF con HttpOnly y plantillas sin JavaScript
ni estilos en linea.
"""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

PLANTILLAS = Path(settings.BASE_DIR) / "templates"


def _directivas(cabecera):
    return dict(
        (partes[0], partes[1:])
        for partes in (d.strip().split() for d in cabecera.split(";")) if partes
    )


@pytest.mark.django_db
def test_el_portal_envia_una_csp_que_solo_admite_el_propio_sitio(client):
    respuesta = client.get(reverse("web:login"))
    csp = _directivas(respuesta["Content-Security-Policy"])
    assert csp["script-src"] == ["'self'"]
    assert csp["style-src"] == ["'self'"]
    assert csp["font-src"] == ["'self'"]
    assert csp["frame-ancestors"] == ["'none'"]
    assert csp["object-src"] == ["'none'"]
    assert "'unsafe-inline'" not in respuesta["Content-Security-Policy"]
    assert "'unsafe-eval'" not in respuesta["Content-Security-Policy"]


@pytest.mark.django_db
def test_la_csp_permite_enviar_el_pago_a_paypal(client):
    respuesta = client.get(reverse("web:login"))
    destinos = _directivas(respuesta["Content-Security-Policy"])["form-action"]
    assert "'self'" in destinos
    assert "https://www.sandbox.paypal.com" in destinos
    assert "https://www.paypal.com" in destinos


@pytest.mark.django_db
def test_solo_el_admin_admite_estilos_en_linea(client):
    respuesta = client.get("/admin/login/")
    csp = _directivas(respuesta["Content-Security-Policy"])
    assert "'unsafe-inline'" in csp["style-src"]
    assert csp["script-src"] == ["'self'"]


@pytest.mark.django_db
def test_la_cookie_csrf_es_httponly(client):
    respuesta = client.get(reverse("web:login"))
    assert respuesta.cookies["csrftoken"]["httponly"]


@pytest.mark.django_db
def test_el_portal_no_carga_hojas_ni_scripts_de_otros_dominios(client):
    html = client.get(reverse("web:login")).content.decode()
    externos = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', html)
    assert externos == []
    assert "css/fuentes" in html


def _plantillas_del_portal():
    # Los correos no son paginas web: su estilo en linea es necesario para los
    # clientes de correo y la CSP no se les aplica
    return [p for p in PLANTILLAS.rglob("*.html") if "correo" not in p.parts]


def test_las_plantillas_no_tienen_javascript_en_linea():
    hallazgos = []
    for plantilla in _plantillas_del_portal():
        texto = plantilla.read_text(encoding="utf-8")
        for etiqueta in re.findall(r"<script\b[^>]*>", texto):
            if "src=" not in etiqueta and "application/json" not in etiqueta:
                hallazgos.append(f"{plantilla.name}: {etiqueta}")
        hallazgos += [f"{plantilla.name}: {m}" for m in re.findall(r"\son[a-z]+=\"", texto)]
    assert hallazgos == []


def test_las_plantillas_no_tienen_estilos_en_linea():
    hallazgos = []
    for plantilla in _plantillas_del_portal():
        texto = plantilla.read_text(encoding="utf-8")
        if re.search(r"\sstyle=\"", texto) or "<style" in texto:
            hallazgos.append(plantilla.name)
    assert hallazgos == []


@pytest.mark.django_db
def test_swagger_sirve_su_javascript_aparte(client):
    url = reverse("api_publica:docs")
    html = client.get(url).content.decode()
    assert "?script=" in html
    assert "<style" not in html
    script = client.get(url, {"script": ""})
    assert script["Content-Type"].startswith("application/javascript")
