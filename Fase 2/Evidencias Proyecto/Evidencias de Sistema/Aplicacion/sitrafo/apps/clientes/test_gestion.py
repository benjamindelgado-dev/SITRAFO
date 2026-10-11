"""
Pruebas de gestion de clientes desde la API interna (RF-CLI-01, 03, 07),
cuentas web (RF-ADM-03) y descargas PDF del portal (RF-CAT-09, RF-CAL-05).
"""
import pytest
from django.core.management import call_command
from django.test import Client
from rest_framework.test import APIClient

from apps.catalogo.models import FamiliaProducto, ModeloProducto
from apps.clientes.models import Cliente, Comuna, Region
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


def test_direccion_se_geocodifica_y_sin_servicio_queda_sin_validar(base):
    from unittest.mock import patch

    from apps.clientes.models import Comuna, DireccionCliente, Region
    from apps.configuracion.models import LogIntegracion

    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    comuna = Comuna.objects.create(nombre="Puente Alto",
                                   region=Region.objects.create(nombre="Metropolitana",
                                                                codigo="RM"))
    datos = {"cliente": cliente.pk, "tipo": "despacho", "comuna": comuna.pk,
             "calle": "Av. Concha y Toro", "numero": "1820"}

    class Respuesta:
        ok, status_code = True, 200

        def json(self):
            return [{"lat": "-33.6117", "lon": "-70.5756"}]

    with patch("requests.get", return_value=Respuesta()):
        creada = base["api"].post("/api/v1/direcciones/", datos, format="json")
    assert creada.status_code == 201
    direccion = DireccionCliente.objects.get()
    assert direccion.validada and str(direccion.latitud) == "-33.611700"
    assert LogIntegracion.objects.filter(servicio="geocodificacion", exitoso=True).exists()

    # Sin red: se guarda igual, sin validar (RF-INT-03)
    sin_red = base["api"].post("/api/v1/direcciones/", {**datos, "numero": "99"},
                               format="json")
    assert sin_red.status_code == 201
    assert DireccionCliente.objects.filter(validada=False).count() == 1


@pytest.mark.django_db
def test_catalogo_de_regiones_y_comunas_completo():
    """RF-CLI-04: la migracion deja las 16 regiones y las 346 comunas de Chile."""
    assert Region.objects.count() == 16
    assert Comuna.objects.count() == 346
    rm = Region.objects.get(nombre="Metropolitana de Santiago")
    assert rm.comunas.filter(nombre="Puente Alto").exists()
    assert rm.comunas.count() == 52


# ---------------------------------------------------------------------------
# Contactos y direcciones: edicion y eliminacion (RF-CLI-03, RF-CLI-04)
# ---------------------------------------------------------------------------
def _cliente_con_direccion(base):
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    region = Region.objects.create(nombre="Metropolitana", codigo="RM")
    comuna = Comuna.objects.create(region=region, nombre="Puente Alto")
    return cliente, comuna


def test_un_solo_contacto_principal_por_cliente(base):
    cliente, _ = _cliente_con_direccion(base)
    api = base["api"]
    uno = api.post("/api/v1/contactos/", {"cliente": cliente.pk, "nombre": "Ana",
                                          "email": "ana@x.cl", "principal": True}).data
    dos = api.post("/api/v1/contactos/", {"cliente": cliente.pk, "nombre": "Luis",
                                          "email": "luis@x.cl"}).data
    api.patch(f"/api/v1/contactos/{dos['id_contacto']}/", {"principal": True}, format="json")
    principales = list(cliente.contactos.filter(principal=True).values_list("nombre", flat=True))
    assert principales == ["Luis"]
    assert api.delete(f"/api/v1/contactos/{uno['id_contacto']}/").status_code == 204


def test_direccion_usada_en_una_solicitud_no_se_elimina(base, monkeypatch):
    from apps.clientes import geocodificacion
    from apps.comercial.models import EstadoDocumento, SolicitudPresupuesto

    monkeypatch.setattr(geocodificacion, "geocodificar", lambda d: False)
    cliente, comuna = _cliente_con_direccion(base)
    api = base["api"]
    datos = {"cliente": cliente.pk, "comuna": comuna.pk, "tipo": "instalacion",
             "calle": "Concha y Toro", "numero": "100"}
    usada = api.post("/api/v1/direcciones/", datos).data
    libre = api.post("/api/v1/direcciones/", {**datos, "numero": "200"}).data
    SolicitudPresupuesto.objects.create(
        numero="SP-2026-0001", cliente=cliente, cantidad=1, direccion_id=usada["id_direccion"],
        estado=EstadoDocumento.objects.create(tipo_documento="solicitud", codigo="recibida",
                                              nombre="Recibida"))

    editada = api.patch(f"/api/v1/direcciones/{usada['id_direccion']}/", {"numero": "150"},
                        format="json")
    assert editada.status_code == 200 and editada.data["numero"] == "150"
    respuesta = api.delete(f"/api/v1/direcciones/{usada['id_direccion']}/")
    assert respuesta.status_code == 409 and "solicitud" in respuesta.data["detalle"]
    assert api.delete(f"/api/v1/direcciones/{libre['id_direccion']}/").status_code == 204


# ---------------------------------------------------------------------------
# Mi cuenta en la web (CU-CLI-07)
# ---------------------------------------------------------------------------
def test_cliente_edita_su_empresa_y_cambia_su_clave(db, django_user_model):
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    usuario = django_user_model.objects.create_user("maipo", "m@maipo.cl", "ClaveSegura2026",
                                                    cliente=cliente)
    django_user_model.objects.create_user("otro", "otro@x.cl", "ClaveSegura2026")
    web = Client()
    web.force_login(usuario)

    usado = web.post("/perfil/empresa/", {"razon_social": "Maipo SpA", "giro": "Energia",
                                         "email": "otro@x.cl"})
    assert "ya esta en uso" in usado.content.decode()
    web.post("/perfil/empresa/", {"razon_social": "Electrica del Maipo SpA",
                                  "nombre_fantasia": "Maipo", "giro": "Energia",
                                  "email": "compras@maipo.cl"})
    cliente.refresh_from_db()
    usuario.refresh_from_db()
    assert cliente.razon_social == "Electrica del Maipo SpA" and cliente.giro == "Energia"
    assert cliente.rut == "76543210-3" and usuario.email == "compras@maipo.cl"
    assert Auditoria.objects.filter(entidad="cliente", origen="web").exists()

    mala = web.post("/perfil/clave/", {"old_password": "incorrecta",
                                       "new_password1": "NuevaClave2026",
                                       "new_password2": "NuevaClave2026"})
    assert mala.status_code == 200
    web.post("/perfil/clave/", {"old_password": "ClaveSegura2026",
                                "new_password1": "NuevaClave2026",
                                "new_password2": "NuevaClave2026"})
    usuario.refresh_from_db()
    assert usuario.check_password("NuevaClave2026")
    assert web.get("/perfil/").status_code == 200        # la sesion sigue abierta
