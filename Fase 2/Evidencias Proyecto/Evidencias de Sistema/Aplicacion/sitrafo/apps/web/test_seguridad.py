"""
Pruebas de seguridad del portal y de la API: consentimiento (RNF-17),
recuperacion de clave (RF-SEG-05), bloqueo temporal (RF-SEG-04),
revocacion de tokens (RNF-04) y cierre por inactividad (RF-SEG-07).
"""
import datetime
import re

import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.seguridad.models import Auditoria, Usuario

REGISTRO = {
    "rut": "76543210-3", "razon_social": "Maipo SpA", "tipo_persona": "juridica",
    "username": "maipo", "email": "compras@maipo.cl",
    "password1": "ClaveSegura2026", "password2": "ClaveSegura2026",
}


@pytest.mark.django_db
def test_registro_exige_consentimiento_y_lo_deja_registrado(client):
    sin = client.post(reverse("web:registro"), REGISTRO)
    assert not Usuario.objects.exists()
    assert "politica de privacidad" in sin.content.decode()

    client.post(reverse("web:registro"), {**REGISTRO, "acepta_privacidad": "on"})
    usuario = Usuario.objects.get(username="maipo")
    consentimiento = Auditoria.objects.get(entidad="consentimiento")
    assert consentimiento.usuario == usuario and consentimiento.valor_nuevo["aceptada"]
    assert client.get(reverse("web:privacidad")).status_code == 200


@pytest.mark.django_db
def test_recuperar_clave_con_enlace_de_un_solo_uso(client):
    Usuario.objects.create_user("maipo", "compras@maipo.cl", "ClaveVieja2026")
    client.post(reverse("web:clave_recuperar"), {"email": "compras@maipo.cl"})

    assert len(mail.outbox) == 1
    enlace = re.search(r"http://\S+/clave/nueva/\S+/", mail.outbox[0].body).group(0)
    ruta = enlace.split("localhost:8000")[1]
    formulario = client.get(ruta, follow=True)
    destino = formulario.redirect_chain[-1][0] if formulario.redirect_chain else ruta
    client.post(destino, {"new_password1": "ClaveNueva2026!", "new_password2": "ClaveNueva2026!"})

    assert Usuario.objects.get().check_password("ClaveNueva2026!")
    segundo_uso = client.get(ruta, follow=True)
    assert "vencio" in segundo_uso.content.decode()


@pytest.mark.django_db
def test_correo_desconocido_no_revela_nada(client):
    respuesta = client.post(reverse("web:clave_recuperar"), {"email": "nadie@x.cl"})
    assert respuesta.status_code == 302 and mail.outbox == []


@pytest.mark.django_db
def test_bloqueo_temporal_se_levanta_solo(client):
    usuario = Usuario.objects.create_user("maipo", "m@m.cl", "ClaveSegura2026")
    for _ in range(5):
        client.post(reverse("web:login"), {"username": "maipo", "password": "mala"})
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.Estado.BLOQUEADO and usuario.bloqueado_hasta

    bloqueado = client.post(reverse("web:login"),
                            {"username": "maipo", "password": "ClaveSegura2026"})
    assert "bloqueada hasta" in bloqueado.content.decode()

    Usuario.objects.filter(pk=usuario.pk).update(
        bloqueado_hasta=timezone.now() - datetime.timedelta(minutes=1))
    ingreso = client.post(reverse("web:login"),
                          {"username": "maipo", "password": "ClaveSegura2026"})
    assert ingreso.status_code == 302
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.Estado.ACTIVO and usuario.ultimo_acceso


@pytest.mark.django_db
def test_cerrar_sesion_revoca_el_token_de_renovacion():
    Usuario.objects.create_user("ejecutivo", "e@s.cl", "Clave123456", es_interno=True)
    api = APIClient()
    tokens = api.post("/api/v1/auth/token/", {"username": "ejecutivo",
                                             "password": "Clave123456"}, format="json").data
    assert api.post("/api/v1/auth/salir/", {"refresh": tokens["refresh"]},
                    format="json").status_code == 200
    renovar = api.post("/api/v1/auth/token/refresh/", {"refresh": tokens["refresh"]},
                       format="json")
    assert renovar.status_code == 401


def test_la_sesion_web_expira_por_inactividad():
    assert settings.SESSION_SAVE_EVERY_REQUEST is True
    assert settings.SESSION_COOKIE_AGE == 30 * 60


@pytest.mark.django_db
def test_catalogo_filtra_por_especificacion(client):
    from apps.catalogo.models import (
        FamiliaProducto,
        ModeloParametro,
        ModeloProducto,
        ParametroTecnico,
    )

    Usuario.objects.create_user("maipo", "m@m.cl", "ClaveSegura2026")
    client.login(username="maipo", password="ClaveSegura2026")
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    potencia = ParametroTecnico.objects.create(codigo="potencia_kva", nombre="Potencia",
                                               unidad="kVA", tipo_dato="lista")
    for codigo, kva in (("TD-100", "100"), ("TD-250", "250")):
        modelo = ModeloProducto.objects.create(familia=familia, codigo=codigo,
                                               nombre=f"Transformador {kva}", publicado=True)
        ModeloParametro.objects.create(modelo=modelo, parametro=potencia, valor_defecto=kva)

    todos = client.get(reverse("web:catalogo")).content.decode()
    filtrado = client.get(reverse("web:catalogo") + "?p_potencia_kva=250").content.decode()
    assert "TD-100" in todos and "TD-250" in todos
    assert "TD-250" in filtrado and "TD-100" not in filtrado


@pytest.mark.django_db
def test_cliente_agrega_edita_y_elimina_sus_direcciones(client):
    from apps.clientes.models import Cliente, Comuna, DireccionCliente, Region

    empresa = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    Usuario.objects.create_user("maipo", "m@m.cl", "ClaveSegura2026", cliente=empresa)
    otro = Cliente.objects.create(rut="77111222-6", razon_social="Otra", tipo_persona="juridica")
    comuna = Comuna.objects.create(nombre="Puente Alto",
                                   region=Region.objects.create(nombre="Metropolitana",
                                                                codigo="RM"))
    ajena = DireccionCliente.objects.create(cliente=otro, comuna=comuna, tipo="despacho",
                                            calle="Ajena", numero="1")
    client.login(username="maipo", password="ClaveSegura2026")

    client.post(reverse("web:direccion_nueva"), {"tipo": "despacho", "comuna": comuna.pk,
                                                 "calle": "Av. Concha y Toro", "numero": "100"})
    propia = DireccionCliente.objects.get(cliente=empresa)
    assert propia.validada is False            # sin red: se guarda igual

    client.post(reverse("web:direccion_editar", args=[propia.pk]),
                {"tipo": "instalacion", "comuna": comuna.pk, "calle": "Av. Nueva",
                 "numero": "200"})
    propia.refresh_from_db()
    assert propia.calle == "Av. Nueva" and propia.tipo == "instalacion"

    assert client.get(reverse("web:direccion_editar", args=[ajena.pk])).status_code == 404
    client.post(reverse("web:direccion_eliminar", args=[propia.pk]))
    assert not DireccionCliente.objects.filter(cliente=empresa).exists()
