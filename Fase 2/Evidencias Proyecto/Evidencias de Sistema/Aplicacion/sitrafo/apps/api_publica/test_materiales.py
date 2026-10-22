"""
Pruebas de la API publica de disponibilidad de materiales (HU-17): materiales
bajo el minimo con la cantidad sugerida, lista vacia, alcance de las claves,
datos que no se exponen y registro de uso.
"""
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.configuracion.models import LogIntegracion
from apps.inventario.models import Bodega, CategoriaMaterial, Material, MovimientoInventario
from apps.seguridad.models import Usuario

from .seguridad import ENCABEZADO

CLAVE_PROVEEDORES = "clave-proveedores-1234567890abcd"
CLAVE_CLIENTES = "clave-clientes-1234567890abcdef"
CLAVE_PUBLICA = "clave-publica-1234567890abcdef"
CLAVE_EXTERNA = "clave-externa-1234567890abcdef"
URL = "/api/publica/v1/materiales/reposicion/"


@pytest.fixture(autouse=True)
def _claves():
    cache.clear()
    claves = {"portal-web": CLAVE_PUBLICA, "portal-clientes": CLAVE_CLIENTES,
              "proveedores": CLAVE_PROVEEDORES, "distribuidor": CLAVE_EXTERNA}
    alcances = {"portal-web": ["seguimiento"],
                "portal-clientes": ["seguimiento", "cotizador"],
                "proveedores": ["materiales"]}
    with override_settings(API_PUBLICA_CLAVES=claves, API_PUBLICA_ALCANCES=alcances,
                           API_PUBLICA_LIMITE="60/min"):
        yield
    cache.clear()


@pytest.fixture
def inventario(db):
    usuario = Usuario.objects.create_user("bodega", "bodega@sitrafo.cl", "Clave123456",
                                          es_interno=True)
    categoria = CategoriaMaterial.objects.create(nombre="Conductores")
    central = Bodega.objects.create(codigo="B1", nombre="Central")
    taller = Bodega.objects.create(codigo="B2", nombre="Taller")

    def material(codigo, minimo, unidad="kg", activo=True):
        return Material.objects.create(categoria=categoria, codigo=codigo, nombre=f"Material {codigo}",
                                       unidad_medida=unidad, stock_minimo=minimo, activo=activo)

    def mover(mat, cantidad, bodega=central):
        MovimientoInventario.objects.create(
            material=mat, bodega=bodega, tipo=MovimientoInventario.Tipo.RECEPCION,
            cantidad=Decimal(cantidad), costo_unitario_uf=Decimal("0.2"), usuario=usuario)

    cobre = material("CU-01", Decimal("100"))          # 30 + 20 = 50 < 100
    mover(cobre, "30")
    mover(cobre, "20", taller)
    aislador = material("AI-01", Decimal("10"), unidad="un")   # 3,5 < 10
    mover(aislador, "3.5")
    aceite = material("AC-01", Decimal("40"), unidad="l")      # 80 >= 40
    mover(aceite, "80")
    material("NU-01", Decimal("5"))                    # sin movimientos: stock 0
    material("SM-01", None)                            # sin minimo definido
    material("IN-01", Decimal("50"), activo=False)     # inactivo
    return {"cobre": cobre, "aceite": aceite, "mover": mover}


def _consultar(clave=CLAVE_PROVEEDORES):
    api = APIClient()
    if clave:
        api.credentials(**{f"HTTP_{ENCABEZADO.upper().replace('-', '_')}": clave})
    return api.get(URL)


# --------------------------------------------------------------------------
# Criterio 1: materiales bajo el minimo con la cantidad sugerida
# --------------------------------------------------------------------------
def test_devuelve_los_materiales_bajo_el_minimo(inventario):
    datos = _consultar().json()
    assert [m["codigo"] for m in datos["materiales"]] == ["AI-01", "CU-01", "NU-01"]
    assert datos["total"] == 3


def test_cantidad_sugerida_lleva_el_stock_al_doble_del_minimo(inventario):
    por_codigo = {m["codigo"]: m for m in _consultar().json()["materiales"]}
    # Cobre: 2 x 100 - 50 (suma de las dos bodegas en el kardex)
    assert Decimal(por_codigo["CU-01"]["cantidad_sugerida"]) == Decimal("150")
    assert Decimal(por_codigo["CU-01"]["stock_minimo"]) == Decimal("100")
    assert por_codigo["CU-01"]["unidad"] == "kg"
    # Unidades enteras se redondean hacia arriba: 2 x 10 - 3,5 = 16,5 -> 17
    assert Decimal(por_codigo["AI-01"]["cantidad_sugerida"]) == Decimal("17")
    # Sin movimientos: 2 x 5 - 0
    assert Decimal(por_codigo["NU-01"]["cantidad_sugerida"]) == Decimal("10")


def test_no_expone_costos_bodegas_ni_stock(inventario):
    material = _consultar().json()["materiales"][0]
    assert set(material) == {"codigo", "nombre", "categoria", "unidad", "stock_minimo",
                             "cantidad_sugerida"}


def test_un_consumo_que_baja_del_minimo_aparece_en_la_consulta(inventario):
    assert "AC-01" not in [m["codigo"] for m in _consultar().json()["materiales"]]
    inventario["mover"](inventario["aceite"], "-50")   # 80 - 50 = 30 < 40
    por_codigo = {m["codigo"]: m for m in _consultar().json()["materiales"]}
    assert Decimal(por_codigo["AC-01"]["cantidad_sugerida"]) == Decimal("50")


# --------------------------------------------------------------------------
# Criterio 2: sin materiales bajo el minimo
# --------------------------------------------------------------------------
def test_sin_materiales_bajo_el_minimo_devuelve_lista_vacia(db):
    datos = _consultar().json()
    assert datos["materiales"] == [] and datos["total"] == 0
    assert datos["calculado_en"]


# --------------------------------------------------------------------------
# Criterio 3: alcance de las claves
# --------------------------------------------------------------------------
def test_sin_clave_responde_401(inventario):
    assert _consultar(clave=None).status_code == 401


@pytest.mark.parametrize("clave", [CLAVE_PUBLICA, CLAVE_CLIENTES])
def test_las_claves_del_portal_no_ven_el_inventario(inventario, clave):
    respuesta = _consultar(clave)
    assert respuesta.status_code == 403
    assert "materiales" not in respuesta.json()


def test_la_clave_de_proveedores_no_puede_cotizar_ni_seguir_pedidos(inventario):
    api = APIClient()
    api.credentials(**{f"HTTP_{ENCABEZADO.upper().replace('-', '_')}": CLAVE_PROVEEDORES})
    assert api.get("/api/publica/v1/cotizador/modelos/").status_code == 403
    assert api.get("/api/publica/v1/seguimiento/OC-2026-0001/?codigo=X").status_code == 403


def test_un_consumidor_externo_sin_restriccion_puede_consultar(inventario):
    assert _consultar(CLAVE_EXTERNA).status_code == 200


# --------------------------------------------------------------------------
# Criterio 4: registro de uso y documentacion
# --------------------------------------------------------------------------
def test_cada_consulta_queda_registrada(inventario):
    _consultar()
    _consultar(CLAVE_PUBLICA)
    registros = LogIntegracion.objects.filter(servicio="api_materiales").order_by("id_log")
    assert [r.codigo_respuesta for r in registros] == [200, 403]
    assert "[proveedores]" in registros[0].endpoint
    assert registros[0].latencia_ms is not None


def test_swagger_documenta_la_disponibilidad_de_materiales(db):
    esquema = APIClient().get("/api/publica/v1/esquema/", {"format": "json"}).json()
    assert "get" in esquema["paths"][URL]
    assert esquema["info"]["version"] == "1.2.0"
