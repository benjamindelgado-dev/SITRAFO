"""
Pruebas de la API publica del cotizador: alcance de las claves, catalogo de
modelos, precio referencial con el costeo comercial, conversion a pesos y
dolares, plazo, validez, validaciones de entrada, registro de uso y el
estimador de la ficha del modelo en el portal.
"""
import datetime
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient

from apps.catalogo.models import (
    BomModelo,
    FamiliaProducto,
    ModeloProducto,
    PrecioBaseModelo,
    TareaEstandarModelo,
)
from apps.clientes.models import Cliente
from apps.comercial.services import PLAZO_DEFECTO_DIAS_HABILES, costear_modelo
from apps.configuracion.models import LogIntegracion, ParametroSistema
from apps.inventario.models import CategoriaMaterial, Material, PrecioMaterial
from apps.pagos.models import IndicadorEconomico
from apps.produccion.models import Empleado, TarifaHoraHombre
from apps.seguridad.models import Usuario

from .seguridad import ENCABEZADO

HOY = datetime.date.today()
CLAVE_CLIENTES = "clave-clientes-1234567890abcdef"
CLAVE_PUBLICA = "clave-publica-1234567890abcdef"
CLAVE_EXTERNA = "clave-externa-1234567890abcdef"
URL_MODELOS = "/api/publica/v1/cotizador/modelos/"
URL_ESTIMACION = "/api/publica/v1/cotizador/estimacion/"
UF = Decimal("40000")
DOLAR = Decimal("950")


@pytest.fixture(autouse=True)
def _claves():
    cache.clear()
    claves = {"portal-web": CLAVE_PUBLICA, "portal-clientes": CLAVE_CLIENTES,
              "distribuidor": CLAVE_EXTERNA}
    alcances = {"portal-web": ["seguimiento"],
                "portal-clientes": ["seguimiento", "cotizador"]}
    with override_settings(API_PUBLICA_CLAVES=claves, API_PUBLICA_ALCANCES=alcances,
                           API_PUBLICA_CLAVE_CLIENTES=CLAVE_CLIENTES,
                           API_PUBLICA_LIMITE="60/min"):
        yield
    cache.clear()


@pytest.fixture
def catalogo(db):
    usuario = Usuario.objects.create_user("comercial", "comercial@sitrafo.cl",
                                          "Clave123456", es_interno=True)
    familia = FamiliaProducto.objects.create(nombre="Distribucion")

    # Modelo con costeo completo: 30 kg de cobre a 0,2 UF y 12 h a 0,5 UF
    costeado = ModeloProducto.objects.create(familia=familia, codigo="TD-100",
                                             nombre="Transformador 100 kVA", publicado=True)
    cobre = Material.objects.create(categoria=CategoriaMaterial.objects.create(nombre="Cond."),
                                    codigo="CU-01", nombre="Cobre", unidad_medida="kg")
    PrecioMaterial.objects.create(material=cobre, costo_uf=Decimal("0.2"),
                                  vigente_desde=datetime.date(2026, 1, 1))
    BomModelo.objects.create(modelo=costeado, material=cobre, cantidad=Decimal("30"))
    TareaEstandarModelo.objects.create(modelo=costeado, nombre="Bobinado", secuencia=1,
                                       horas_estimadas=Decimal("12"))
    empleado = Empleado.objects.create(rut="12345678-5", nombre="Juan Soto", cargo="Bobinador")
    TarifaHoraHombre.objects.create(empleado=empleado, valor_hora_uf=Decimal("0.5"),
                                    vigente_desde=datetime.date(2026, 1, 1))

    # Modelo sin costeo, con precio base del catalogo
    con_precio_base = ModeloProducto.objects.create(
        familia=familia, codigo="TD-250", nombre="Transformador 250 kVA", publicado=True)
    PrecioBaseModelo.objects.create(modelo=con_precio_base, monto_uf=Decimal("80"),
                                    usuario=usuario, vigente_desde=datetime.date(2026, 1, 1))

    # Modelo publicado sin costeo ni precio, y otro no publicado
    sin_precio = ModeloProducto.objects.create(familia=familia, codigo="TE-ESP",
                                               nombre="Transformador especial", publicado=True)
    ModeloProducto.objects.create(familia=familia, codigo="TD-OCULTO", nombre="Oculto",
                                  publicado=False)

    IndicadorEconomico.objects.create(codigo="UF", fecha=HOY, valor=UF)
    IndicadorEconomico.objects.create(codigo="USD", fecha=HOY, valor=DOLAR)
    return {"costeado": costeado, "con_precio_base": con_precio_base,
            "sin_precio": sin_precio, "usuario": usuario}


def _api(clave=CLAVE_CLIENTES):
    api = APIClient()
    if clave:
        api.credentials(**{f"HTTP_{ENCABEZADO.upper().replace('-', '_')}": clave})
    return api


def _estimar(items, clave=CLAVE_CLIENTES):
    return _api(clave).post(URL_ESTIMACION, {"items": items}, format="json")


# --------------------------------------------------------------------------
# Acceso por clave y alcance
# --------------------------------------------------------------------------
def test_sin_clave_responde_401(catalogo):
    assert _api(clave=None).get(URL_MODELOS).status_code == 401


def test_la_clave_publica_del_seguimiento_no_puede_cotizar(catalogo):
    respuesta = _estimar([{"modelo": "TD-100", "cantidad": 1}], clave=CLAVE_PUBLICA)
    assert respuesta.status_code == 403
    assert _api(CLAVE_PUBLICA).get(URL_MODELOS).status_code == 403


def test_un_consumidor_externo_sin_restriccion_puede_cotizar(catalogo):
    assert _estimar([{"modelo": "TD-100", "cantidad": 1}], clave=CLAVE_EXTERNA).status_code == 200


# --------------------------------------------------------------------------
# Catalogo
# --------------------------------------------------------------------------
def test_lista_solo_modelos_publicados(catalogo):
    datos = _api().get(URL_MODELOS).json()
    assert [m["codigo"] for m in datos] == ["TD-100", "TD-250", "TE-ESP"]
    assert datos[0]["familia"] == "Distribucion"


# --------------------------------------------------------------------------
# Precio referencial
# --------------------------------------------------------------------------
def test_usa_el_mismo_costeo_que_las_cotizaciones(catalogo):
    datos = _estimar([{"modelo": "TD-100", "cantidad": 2}]).json()
    item = datos["items"][0]
    esperado = costear_modelo(catalogo["costeado"]).precio_sugerido_uf.quantize(Decimal("0.01"))
    assert Decimal(item["precio_unitario_uf"]) == esperado
    assert Decimal(item["subtotal_uf"]) == esperado * 2
    assert item["disponible"] is True


def test_no_expone_costos_internos_ni_margen(catalogo):
    texto = str(_estimar([{"modelo": "TD-100", "cantidad": 1}]).json())
    for palabra in ("costo", "margen", "hh", "material"):
        assert palabra not in texto.lower()


def test_modelo_sin_costeo_usa_el_precio_base(catalogo):
    item = _estimar([{"modelo": "td-250", "cantidad": 1}]).json()["items"][0]
    assert Decimal(item["precio_unitario_uf"]) == Decimal("80.00")


def test_conversion_a_pesos_y_dolares(catalogo):
    datos = _estimar([{"modelo": "TD-250", "cantidad": 3}]).json()
    assert Decimal(datos["total_uf"]) == Decimal("240.00")
    assert Decimal(datos["total_clp"]) == Decimal("240") * UF
    assert Decimal(datos["total_usd"]) == (Decimal("240") * UF / DOLAR).quantize(Decimal("0.01"))
    assert Decimal(datos["indicadores"]["uf"]["valor"]) == UF


def test_varios_modelos_y_uno_sin_precio(catalogo):
    datos = _estimar([{"modelo": "TD-250", "cantidad": 1},
                      {"modelo": "TE-ESP", "cantidad": 1}]).json()
    sin_precio = datos["items"][1]
    assert sin_precio["disponible"] is False and sin_precio["precio_unitario_uf"] is None
    assert Decimal(datos["total_uf"]) == Decimal("80.00")  # solo suma los disponibles
    assert any("segun especificacion" in a for a in datos["avisos"])
    assert f"modelo={catalogo['sin_precio'].pk}&cantidad=1" in sin_precio["solicitar_presupuesto"]


def test_sin_ningun_precio_no_hay_total(catalogo):
    datos = _estimar([{"modelo": "TE-ESP", "cantidad": 1}]).json()
    assert datos["total_uf"] is None and datos["total_clp"] is None


def test_sin_uf_omite_pesos_y_dolares(catalogo):
    IndicadorEconomico.objects.filter(codigo="UF").delete()
    datos = _estimar([{"modelo": "TD-250", "cantidad": 1}]).json()
    assert datos["total_uf"] is not None
    assert datos["total_clp"] is None and datos["total_usd"] is None
    assert any("UF" in a for a in datos["avisos"])


def test_plazo_y_validez(catalogo):
    datos = _estimar([{"modelo": "TD-100", "cantidad": 1}]).json()
    assert datos["plazo"]["dias_habiles"] == PLAZO_DEFECTO_DIAS_HABILES
    assert datos["plazo"]["fecha_entrega_estimada"] > HOY.isoformat()
    assert datos["valida_hasta"] == (HOY + datetime.timedelta(days=15)).isoformat()


def test_validez_configurable_desde_parametros(catalogo):
    ParametroSistema.objects.create(clave="comercial.validez_estimacion_dias", valor="7",
                                    tipo_dato="numerico", ambito="comercial",
                                    descripcion="Validez", usuario=catalogo["usuario"])
    datos = _estimar([{"modelo": "TD-100", "cantidad": 1}]).json()
    assert datos["valida_hasta"] == (HOY + datetime.timedelta(days=7)).isoformat()


# --------------------------------------------------------------------------
# Validaciones de entrada
# --------------------------------------------------------------------------
@pytest.mark.parametrize("items", [
    [],
    [{"modelo": "NO-EXISTE", "cantidad": 1}],
    [{"modelo": "TD-OCULTO", "cantidad": 1}],
    [{"modelo": "TD-100", "cantidad": 0}],
    [{"modelo": "TD-100", "cantidad": 100000}],
    [{"modelo": "TD-100", "cantidad": 1}, {"modelo": "td-100", "cantidad": 2}],
    [{"modelo": "TD-100", "cantidad": 1}] * 11,
])
def test_entradas_invalidas_responden_400(catalogo, items):
    assert _estimar(items).status_code == 400


# --------------------------------------------------------------------------
# Registro de uso y documentacion
# --------------------------------------------------------------------------
def test_cada_consulta_queda_registrada(catalogo):
    _api().get(URL_MODELOS)
    _estimar([{"modelo": "NO-EXISTE", "cantidad": 1}])
    registros = LogIntegracion.objects.filter(servicio="api_cotizador").order_by("id_log")
    assert [r.codigo_respuesta for r in registros] == [200, 400]
    assert "[portal-clientes]" in registros[0].endpoint


def test_swagger_documenta_el_cotizador(db):
    rutas = APIClient().get("/api/publica/v1/esquema/", {"format": "json"}).json()["paths"]
    assert "/api/publica/v1/cotizador/modelos/" in rutas
    assert "post" in rutas["/api/publica/v1/cotizador/estimacion/"]


# --------------------------------------------------------------------------
# Consumo desde el portal de clientes
# --------------------------------------------------------------------------
def _sesion_cliente():
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    cuenta = Usuario.objects.create_user("maipo", "maipo@cliente.cl", "Clave123456",
                                         es_interno=False, cliente=cliente)
    web = APIClient()
    web.force_login(cuenta)
    return web


def test_ficha_del_modelo_usa_la_clave_del_portal_de_clientes(catalogo):
    contenido = _sesion_cliente().get(f"/catalogo/{catalogo['costeado'].pk}/").content.decode()
    assert CLAVE_CLIENTES in contenido and URL_ESTIMACION in contenido
    assert CLAVE_PUBLICA not in contenido


def test_la_solicitud_llega_con_la_cantidad_estimada(catalogo):
    web = _sesion_cliente()
    pagina = web.get("/solicitar/", {"modelo": catalogo["costeado"].pk, "cantidad": 3})
    assert pagina.context["form"].initial["cantidad"] == 3
    # Un valor no numerico se ignora
    pagina = web.get("/solicitar/", {"modelo": catalogo["costeado"].pk, "cantidad": "x"})
    assert "cantidad" not in pagina.context["form"].initial
