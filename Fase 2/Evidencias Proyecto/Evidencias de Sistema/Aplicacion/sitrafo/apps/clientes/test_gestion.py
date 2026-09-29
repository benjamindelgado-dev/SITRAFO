"""
Pruebas de gestion de clientes desde la API interna (RF-CLI-01, 03, 07),
cuentas web (RF-ADM-03) y descargas PDF del portal (RF-CAT-09, RF-CAL-05).
"""
import pytest
from django.core.management import call_command
from django.test import Client
from rest_framework.test import APIClient

from apps.catalogo.models import FamiliaProducto, ModeloProducto
from apps.clientes.models import Cliente
from apps.seguridad import matriz
from apps.seguridad.models import Auditoria, Rol, Usuario, UsuarioRol


@pytest.fixture
def base(db):
    call_command("cargar_roles", verbosity=0)
    comercial = Usuario.objects.create_user("comercial", "c@sitrafo.cl", "Clave123456",
                                            es_interno=True)
    UsuarioRol.objects.create(usuario=comercial, rol=Rol.objects.get(nombre=matriz.COMERCIAL))
    api = APIClient()
    api.force_authenticate(comercial)
    return {"api": api}


def test_comercial_crea_cliente_con_contacto_y_ve_su_historial(base):
    creado = base["api"].post("/api/v1/clientes/", {
        "rut": "76.543.210-3", "razon_social": "Electrica Andes SpA",
        "tipo_persona": "juridica", "giro": "Distribucion electrica"}, format="json")
    assert creado.status_code == 201, creado.data
    assert creado.data["rut"] == "76543210-3"

    id_cliente = creado.data["id_cliente"]
    contacto = base["api"].post("/api/v1/contactos/", {
        "cliente": id_cliente, "nombre": "Ana Rojas", "email": "ana@andes.cl",
        "principal": True}, format="json")
    assert contacto.status_code == 201

    historial = base["api"].get(f"/api/v1/clientes/{id_cliente}/documentos/").data
    assert set(historial) == {"solicitudes", "cotizaciones", "ordenes_compra", "cobros"}


def test_rut_duplicado_o_invalido_se_rechaza(base):
    datos = {"rut": "76543210-3", "razon_social": "A", "tipo_persona": "juridica"}
    base["api"].post("/api/v1/clientes/", datos, format="json")
    assert base["api"].post("/api/v1/clientes/", datos, format="json").status_code == 400
    assert base["api"].post("/api/v1/clientes/", {**datos, "rut": "76543210-9"},
                            format="json").status_code == 400


def test_cuenta_web_suspendida_pierde_su_sesion(base):
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    cuenta = Usuario.objects.create_user("maipo", "m@maipo.cl", "ClaveSegura2026",
                                         cliente=cliente)
    navegador = Client()
    navegador.force_login(cuenta)

    url = f"/api/v1/clientes/{cliente.pk}/suspender_cuenta/"
    assert base["api"].post(url, {"cuenta": cuenta.pk}, format="json").status_code == 200
    assert Auditoria.objects.filter(entidad="cuenta_web").exists()

    respuesta = navegador.get("/mis-pedidos/")
    assert respuesta.status_code == 302 and "/acceso/" in respuesta["Location"]


def test_ficha_tecnica_en_pdf(base):
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    navegador = Client()
    navegador.force_login(Usuario.objects.create_user("maipo", "m@m.cl", "x" * 12,
                                                      cliente=cliente))
    modelo = ModeloProducto.objects.create(
        familia=FamiliaProducto.objects.create(nombre="Distribucion"), codigo="TD-1",
        nombre="Transformador", publicado=True)
    respuesta = navegador.get(f"/catalogo/{modelo.pk}/ficha.pdf")
    assert respuesta.status_code == 200
    assert respuesta.content.startswith(b"%PDF")
