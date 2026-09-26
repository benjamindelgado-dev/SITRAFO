"""
Pruebas de la administracion de usuarios internos (CU-SEG-02, CU-SEG-03).
"""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.produccion.models import Empleado
from apps.seguridad import matriz
from apps.seguridad.models import Auditoria, Rol, Usuario, UsuarioRol


def _api(usuario):
    api = APIClient()
    api.force_authenticate(usuario)
    return api


def _interno(nombre, rol):
    usuario = Usuario.objects.create_user(nombre, f"{nombre}@sitrafo.cl", "Clave123456",
                                          es_interno=True)
    UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    return usuario


@pytest.fixture
def base(db):
    call_command("cargar_roles", verbosity=0)
    admin = _interno("administrador", matriz.ADMIN)
    maria = Empleado.objects.create(rut="17234568-9", nombre="Maria Diaz", cargo="Tecnica")
    return {"admin": admin, "api": _api(admin), "maria": maria,
            "operario": Rol.objects.get(nombre=matriz.OPERARIO)}


def test_el_administrador_crea_un_operario_asociado_a_su_empleado(base):
    respuesta = base["api"].post("/api/v1/usuarios/", {
        "username": "mdiaz", "email": "mdiaz@sitrafo.cl",
        "roles": [base["operario"].pk], "empleado": base["maria"].pk,
    }, format="json")

    assert respuesta.status_code == 201, respuesta.data
    clave = respuesta.data["clave_temporal"]
    usuario = Usuario.objects.get(username="mdiaz")
    assert usuario.es_interno and usuario.check_password(clave)
    assert usuario.has_perm("taller.crear")
    base["maria"].refresh_from_db()
    assert base["maria"].usuario == usuario
    assert Auditoria.objects.filter(entidad="usuario", accion="creacion").exists()


def test_sin_rol_no_se_crea(base):
    respuesta = base["api"].post("/api/v1/usuarios/", {
        "username": "sinrol", "email": "s@sitrafo.cl", "roles": []}, format="json")
    assert respuesta.status_code == 409
    assert not Usuario.objects.filter(username="sinrol").exists()


def test_un_empleado_no_se_asocia_a_dos_usuarios(base):
    datos = {"email": "a@sitrafo.cl", "roles": [base["operario"].pk],
             "empleado": base["maria"].pk}
    base["api"].post("/api/v1/usuarios/", {**datos, "username": "uno"}, format="json")
    respuesta = base["api"].post("/api/v1/usuarios/",
                                 {**datos, "username": "dos", "email": "b@sitrafo.cl"},
                                 format="json")
    assert respuesta.status_code == 409


def test_el_administrador_no_se_quita_su_rol_ni_se_suspende(base):
    url = f"/api/v1/usuarios/{base['admin'].pk}/"
    quitar = base["api"].patch(url, {"roles": [base["operario"].pk]}, format="json")
    assert quitar.status_code == 409
    assert base["api"].post(f"{url}suspender/").status_code == 409


def test_suspender_impide_operar_y_reactivar_lo_devuelve(base):
    operario = _interno("operario", matriz.OPERARIO)
    url = f"/api/v1/usuarios/{operario.pk}"

    assert base["api"].post(f"{url}/suspender/").status_code == 200
    assert _api(Usuario.objects.get(pk=operario.pk)).get("/api/v1/auth/yo/").status_code == 403
    assert base["api"].post(f"{url}/reactivar/").status_code == 200
    assert _api(Usuario.objects.get(pk=operario.pk)).get("/api/v1/auth/yo/").status_code == 200


def test_restablecer_clave_genera_una_temporal(base):
    operario = _interno("operario", matriz.OPERARIO)
    respuesta = base["api"].post(f"/api/v1/usuarios/{operario.pk}/restablecer_clave/")
    operario.refresh_from_db()
    assert operario.check_password(respuesta.data["clave_temporal"])


def test_solo_el_administrador_gestiona_usuarios(base):
    comercial = _api(_interno("comercial", matriz.COMERCIAL))
    assert comercial.get("/api/v1/usuarios/").status_code == 403
    assert comercial.post("/api/v1/usuarios/", {}, format="json").status_code == 403


def test_nadie_sin_ser_superusuario_modifica_un_superusuario(base):
    root = Usuario.objects.create_superuser("root", "root@sitrafo.cl", "Clave123456")
    root.es_interno = True
    root.save()
    respuesta = base["api"].post(f"/api/v1/usuarios/{root.pk}/suspender/")
    assert respuesta.status_code == 409


def test_clave_debil_se_rechaza(base, settings):
    settings.AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
         "OPTIONS": {"min_length": 10}},
    ]
    respuesta = base["api"].post("/api/v1/usuarios/", {
        "username": "debil", "email": "d@sitrafo.cl", "roles": [base["operario"].pk],
        "clave": "123"}, format="json")
    assert respuesta.status_code == 409


# ---------------------------------------------------------------------------
# Ingreso con token (RF-SEG-04)
# ---------------------------------------------------------------------------
def test_ingreso_registra_acceso_y_bloquea_por_intentos(base):
    operario = _interno("operario", matriz.OPERARIO)
    api = APIClient()

    for _ in range(4):
        assert api.post("/api/v1/auth/token/", {"username": "operario", "password": "mala"},
                        format="json").status_code == 401
    quinto = api.post("/api/v1/auth/token/", {"username": "operario", "password": "mala"},
                      format="json")
    assert quinto.status_code == 403
    operario.refresh_from_db()
    assert operario.estado == Usuario.Estado.BLOQUEADO

    # Bloqueado, ni la clave correcta entra; el administrador lo reactiva
    correcta = {"username": "operario", "password": "Clave123456"}
    assert api.post("/api/v1/auth/token/", correcta, format="json").status_code == 403
    base["api"].post(f"/api/v1/usuarios/{operario.pk}/reactivar/")
    assert api.post("/api/v1/auth/token/", correcta, format="json").status_code == 200
    operario.refresh_from_db()
    assert operario.ultimo_acceso is not None and operario.intentos_fallidos == 0
