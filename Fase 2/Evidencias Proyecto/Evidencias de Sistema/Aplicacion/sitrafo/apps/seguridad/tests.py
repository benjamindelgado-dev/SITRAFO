"""
Pruebas de la matriz de acceso por rol (ERS-01, seccion 8.2).

Verifican la denegacion por defecto (RN-18), la segregacion de funciones
entre roles, el aislamiento del cliente web (RN-16) y el registro de los
accesos denegados en la bitacora (CU-SEG-07).
"""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.clientes.models import Cliente
from apps.configuracion.models import ParametroSistema
from apps.seguridad import matriz
from apps.seguridad.models import Auditoria, Rol, RolPermiso, Usuario, UsuarioRol


@pytest.fixture
def roles(db):
    call_command("cargar_roles", verbosity=0)
    call_command("cargar_estados", verbosity=0)


def _api(usuario):
    cliente = APIClient()
    cliente.force_authenticate(usuario)
    return cliente


def _interno(nombre, rol=None):
    usuario = Usuario.objects.create_user(nombre, f"{nombre}@sitrafo.cl", "Clave123456",
                                          es_interno=True)
    if rol:
        UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    return usuario


# ---------------------------------------------------------------------------
# Carga de la matriz
# ---------------------------------------------------------------------------
def test_cargar_roles_crea_los_seis_roles_y_es_idempotente(roles):
    assert Rol.objects.count() == 6
    asignaciones = RolPermiso.objects.count()
    call_command("cargar_roles", verbosity=0)
    assert RolPermiso.objects.count() == asignaciones


def test_la_matriz_respeta_la_segregacion_de_funciones(roles):
    comercial = matriz.permisos_de_rol(matriz.COMERCIAL)
    produccion = matriz.permisos_de_rol(matriz.PRODUCCION)
    operario = matriz.permisos_de_rol(matriz.OPERARIO)
    calidad = matriz.permisos_de_rol(matriz.CALIDAD)
    bodega = matriz.permisos_de_rol(matriz.BODEGA)

    assert "cotizacion.aprobar" in comercial
    assert "cotizacion.leer" in produccion and "cotizacion.crear" not in produccion
    assert operario == {"orden_trabajo.leer", "taller.leer", "taller.crear",
                        "taller.actualizar", "taller.anular"}
    # RN-12: calidad controla, produccion no puede operar sobre no conformidades
    assert "no_conformidad.actualizar" in calidad
    assert "no_conformidad.actualizar" not in produccion
    # Bodega ajusta inventario; el operario no
    assert "bodega.actualizar" in bodega and "bodega.actualizar" not in operario


def test_usuarios_demo_uno_por_rol(roles):
    call_command("cargar_roles", "--usuarios-demo", verbosity=0)
    comercial = Usuario.objects.get(username="comercial")
    assert comercial.es_interno and comercial.check_password("Clave123456")
    assert comercial.has_perm("cotizacion.crear")
    assert not Usuario.objects.get(username="operario").has_perm("cotizacion.leer")


# ---------------------------------------------------------------------------
# Aplicacion en la API
# ---------------------------------------------------------------------------
def test_usuario_sin_rol_es_denegado_y_auditado(roles):
    """RN-18: sin rol no se opera."""
    usuario = _interno("sinrol")
    respuesta = _api(usuario).get("/api/v1/solicitudes/")

    assert respuesta.status_code == 403
    registro = Auditoria.objects.get(usuario=usuario)
    assert registro.accion == Auditoria.Accion.ACCESO_DENEGADO
    assert registro.valor_nuevo["permiso_requerido"] == ["solicitud.leer"]


def test_solo_lectura_permite_ver_pero_no_operar(roles):
    produccion = _api(_interno("produccion", matriz.PRODUCCION))
    assert produccion.get("/api/v1/cotizaciones/").status_code == 200
    assert produccion.post("/api/v1/solicitudes/1/cotizar/", {}, format="json").status_code == 403


def test_el_administrador_no_cotiza(roles):
    admin = _api(_interno("administrador", matriz.ADMIN))
    assert admin.get("/api/v1/solicitudes/").status_code == 200      # lectura
    assert admin.get("/api/v1/cotizaciones/").status_code == 403     # sin acceso


def test_canal_web_lo_opera_el_administrador_y_lo_lee_el_comercial(roles):
    admin = _interno("administrador", matriz.ADMIN)
    ParametroSistema.objects.create(
        clave="web.modo_mantencion", valor="false", tipo_dato="booleano",
        ambito="canal_web", usuario=admin,
    )
    url = "/api/v1/parametros/web.modo_mantencion/alternar/"
    comercial = _api(_interno("comercial", matriz.COMERCIAL))

    assert comercial.get("/api/v1/parametros/").status_code == 200
    assert comercial.post(url).status_code == 403
    assert _api(admin).post(url).status_code == 200


def test_parametro_de_sistema_exige_permiso_de_sistema(roles):
    """El permiso de canal web no alcanza para cambiar parametros de sistema."""
    admin = _interno("administrador", matriz.ADMIN)
    ParametroSistema.objects.create(
        clave="seguridad.intentos_fallidos_max", valor="5", tipo_dato="entero",
        ambito="sistema", usuario=admin,
    )
    rol = Rol.objects.create(nombre="Solo canal web")
    for codigo in ("canal_web.leer", "canal_web.actualizar"):
        RolPermiso.objects.create(rol=rol, permiso_id=matriz_permiso(codigo))
    usuario = _interno("webmaster")
    UsuarioRol.objects.create(usuario=usuario, rol=rol)

    respuesta = _api(usuario).patch("/api/v1/parametros/seguridad.intentos_fallidos_max/",
                                    {"valor": "10"}, format="json")
    assert respuesta.status_code == 403


def matriz_permiso(codigo):
    from apps.seguridad.models import Permiso

    return Permiso.objects.get(codigo=codigo).pk


def test_ni_el_superusuario_salta_el_flujo_documental(roles):
    """La cotizacion nace desde una solicitud; no se crea ni edita a mano."""
    root = Usuario.objects.create_superuser("root", "root@sitrafo.cl", "Clave123456")
    api = _api(root)
    assert api.post("/api/v1/cotizaciones/", {}, format="json").status_code == 403
    assert api.patch("/api/v1/cotizaciones/1/", {}, format="json").status_code == 403
    assert api.post("/api/v1/ordenes-compra/", {}, format="json").status_code == 403


# ---------------------------------------------------------------------------
# Cliente web (RN-16)
# ---------------------------------------------------------------------------
def test_cliente_web_solo_usa_sus_acciones(roles):
    empresa = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    cuenta = Usuario.objects.create_user("maipo", "m@maipo.cl", "Clave123456", cliente=empresa)
    api = _api(cuenta)

    assert api.get("/api/v1/cotizaciones/").status_code == 200
    assert api.post("/api/v1/cotizaciones/1/emitir/").status_code == 403
    assert api.get("/api/v1/parametros/").status_code == 403
    assert api.patch("/api/v1/clientes/1/", {"razon_social": "X"}, format="json").status_code == 403
    assert Auditoria.objects.filter(usuario=cuenta, origen="web").count() == 3


# ---------------------------------------------------------------------------
# Endpoint de identidad para el escritorio
# ---------------------------------------------------------------------------
def test_yo_informa_roles_y_permisos(roles):
    usuario = _interno("comercial", matriz.COMERCIAL)
    datos = _api(usuario).get("/api/v1/auth/yo/").data

    assert datos["roles"] == [matriz.COMERCIAL]
    assert "cotizacion.aprobar" in datos["permisos"]
    assert "canal_web.actualizar" not in datos["permisos"]
    assert datos["es_superusuario"] is False
