"""
Pruebas del alta y edicion de modelos del catalogo desde la API.

Verifican la segregacion entre catalogo y precios en la matriz de acceso, la
validacion de los parametros tecnicos y el versionado del precio (RN-17).
"""
import datetime
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalogo.models import (
    FamiliaProducto,
    ModeloProducto,
    ParametroTecnico,
    PrecioBaseModelo,
    ValorParametro,
)
from apps.seguridad import matriz
from apps.seguridad.models import Auditoria, Rol, Usuario, UsuarioRol


def _api(nombre, rol):
    usuario = Usuario.objects.create_user(nombre, f"{nombre}@sitrafo.cl", "Clave123456",
                                          es_interno=True)
    UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    api = APIClient()
    api.force_authenticate(usuario)
    return api


@pytest.fixture
def catalogo(db):
    call_command("cargar_roles", verbosity=0)
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    potencia = ParametroTecnico.objects.create(codigo="potencia_kva", nombre="Potencia",
                                               unidad="kVA", tipo_dato="lista")
    for i, valor in enumerate(["100", "250"]):
        ValorParametro.objects.create(parametro=potencia, valor=valor, orden=i)
    tension = ParametroTecnico.objects.create(codigo="tension", nombre="Tension",
                                              unidad="kV", tipo_dato="numerico")
    return {"admin": _api("administrador", matriz.ADMIN),
            "comercial": _api("comercial", matriz.COMERCIAL),
            "familia": familia, "potencia": potencia, "tension": tension}


def _nuevo(catalogo, **extra):
    datos = {
        "familia": catalogo["familia"].pk, "codigo": "TD-500",
        "nombre": "Transformador 500 kVA", "descripcion": "Distribucion trifasico",
        "parametros": [
            {"parametro": catalogo["potencia"].pk, "valor_defecto": "250",
             "obligatorio": True},
            {"parametro": catalogo["tension"].pk, "valor_defecto": "23"},
        ],
        "precio_base_uf": "480",
        **extra,
    }
    return catalogo["admin"].post("/api/v1/modelos/", datos, format="json")


def test_el_administrador_crea_un_modelo_con_parametros_y_precio(catalogo):
    respuesta = _nuevo(catalogo)

    assert respuesta.status_code == 201, respuesta.data
    modelo = ModeloProducto.objects.get(codigo="TD-500")
    assert modelo.publicado is False              # se publica aparte
    assert modelo.precio_vigente == Decimal("480")
    assert modelo.parametros_asignados.count() == 2
    assert Auditoria.objects.filter(entidad="modelo_producto", accion="creacion").exists()


def test_valor_fuera_de_la_lista_se_rechaza(catalogo):
    respuesta = _nuevo(catalogo, parametros=[
        {"parametro": catalogo["potencia"].pk, "valor_defecto": "999"}
    ])
    assert respuesta.status_code == 409
    assert not ModeloProducto.objects.filter(codigo="TD-500").exists()


def test_el_comercial_no_crea_modelos(catalogo):
    datos = {"familia": catalogo["familia"].pk, "codigo": "X", "nombre": "X"}
    assert catalogo["comercial"].post("/api/v1/modelos/", datos,
                                      format="json").status_code == 403


def test_cambio_de_precio_versiona_la_vigencia(catalogo):
    _nuevo(catalogo)
    modelo = ModeloProducto.objects.get(codigo="TD-500")
    # Simula que el precio se fijo hace un mes
    PrecioBaseModelo.objects.filter(modelo=modelo).update(
        vigente_desde=timezone.localdate() - datetime.timedelta(days=30)
    )

    respuesta = catalogo["admin"].patch(f"/api/v1/modelos/{modelo.pk}/",
                                        {"precio_base_uf": "520", "codigo": "OTRO"},
                                        format="json")

    assert respuesta.status_code == 200
    precios = list(modelo.precios.order_by("vigente_desde"))
    assert [p.monto_uf for p in precios] == [Decimal("480"), Decimal("520")]
    assert precios[0].vigente_hasta == timezone.localdate() - datetime.timedelta(days=1)
    modelo.refresh_from_db()
    assert modelo.codigo == "TD-500"              # el codigo no cambia


def test_no_se_borran_modelos(catalogo):
    _nuevo(catalogo)
    modelo = ModeloProducto.objects.get(codigo="TD-500")
    assert catalogo["admin"].delete(f"/api/v1/modelos/{modelo.pk}/").status_code == 403
