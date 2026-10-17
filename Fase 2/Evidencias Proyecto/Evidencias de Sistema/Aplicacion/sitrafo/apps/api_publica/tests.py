"""
Pruebas de la API publica de seguimiento de pedidos: clave de API, codigo de
seguimiento, etapas y avance, fecha estimada de entrega, limite de
solicitudes, registro de uso y documentacion.
"""
import datetime
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from apps.catalogo.models import FamiliaProducto, ModeloProducto
from apps.clientes.models import Cliente
from apps.comercial.models import (
    Cotizacion,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraHistorial,
    SolicitudPresupuesto,
)
from apps.configuracion.models import Feriado, LogIntegracion
from apps.produccion.models import OrdenTrabajo, OrdenTrabajoHistorial
from apps.seguridad.models import Usuario

from .codigos import codigo_seguimiento, codigo_valido
from .seguridad import ENCABEZADO

HOY = datetime.date.today()
CLAVE = "clave-de-prueba-1234567890abcdef"
URL = "/api/publica/v1/seguimiento/{}/"


def _estado(tipo, codigo):
    return EstadoDocumento.objects.get(tipo_documento=tipo, codigo=codigo)


@pytest.fixture(autouse=True)
def _claves():
    cache.clear()  # el limite de solicitudes usa la cache
    with override_settings(API_PUBLICA_CLAVES={"portal-web": CLAVE},
                           API_PUBLICA_LIMITE="60/min"):
        yield
    cache.clear()


@pytest.fixture
def pedido(db):
    call_command("cargar_estados", verbosity=0)
    usuario = Usuario.objects.create_user("comercial", "comercial@sitrafo.cl",
                                          "Clave123456", es_interno=True)
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    modelo = ModeloProducto.objects.create(familia=familia, codigo="TD-100",
                                           nombre="Transformador 100 kVA")
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    solicitud = SolicitudPresupuesto.objects.create(
        numero="SP-2026-0001", cliente=cliente, modelo=modelo, cantidad=2,
        estado=_estado("solicitud", "cotizada"),
    )
    cotizacion = Cotizacion.objects.create(
        numero="COT-2026-0001", solicitud=solicitud, cliente=cliente,
        estado=_estado("cotizacion", "aceptada"), ejecutivo=usuario,
        valor_uf=Decimal("40000"), fecha_valor_uf=HOY, vence_el=HOY + datetime.timedelta(30),
        total_uf=Decimal("50"), plazo_dias_habiles=20,
    )
    orden = OrdenCompra.objects.create(
        numero="OC-2026-0001", cotizacion=cotizacion, cliente=cliente,
        estado=_estado("orden_compra", "pendiente"), total_uf=Decimal("50"),
    )
    return {"orden": orden, "modelo": modelo, "usuario": usuario, "cotizacion": cotizacion}


def _api(clave=CLAVE):
    api = APIClient()
    if clave:
        api.credentials(**{f"HTTP_{ENCABEZADO.upper().replace('-', '_')}": clave})
    return api


def _consultar(orden, api=None, codigo=None):
    api = api or _api()
    return api.get(URL.format(orden.numero), {"codigo": codigo or codigo_seguimiento(orden)})


def _cambiar_oc(pedido, codigo):
    orden = pedido["orden"]
    anterior = orden.estado
    orden.estado = _estado("orden_compra", codigo)
    orden.save()
    OrdenCompraHistorial.objects.create(orden_compra=orden, estado_anterior=anterior,
                                        estado_nuevo=orden.estado, usuario=pedido["usuario"])


def _crear_ot(pedido, numero, codigo, avance=None):
    ot = OrdenTrabajo.objects.create(
        numero=numero, orden_compra=pedido["orden"], modelo=pedido["modelo"], cantidad=1,
        estado=_estado("orden_trabajo", codigo), costo_estimado_uf=Decimal("10"),
        avance_pct=avance,
    )
    OrdenTrabajoHistorial.objects.create(orden_trabajo=ot, estado_nuevo=ot.estado,
                                         usuario=pedido["usuario"])
    return ot


# --------------------------------------------------------------------------
# Codigo de seguimiento
# --------------------------------------------------------------------------
def test_codigo_tiene_formato_y_acepta_variantes(pedido):
    orden = pedido["orden"]
    codigo = codigo_seguimiento(orden)
    assert len(codigo) == 11 and codigo[5] == "-"
    assert codigo_valido(orden, codigo.lower())
    assert codigo_valido(orden, codigo.replace("-", ""))
    assert not codigo_valido(orden, "AAAAA-BBBBB")


@override_settings(SEGUIMIENTO_CLAVE="otra-clave")
def test_codigo_depende_de_la_clave_secreta(pedido):
    codigo_otra_clave = codigo_seguimiento(pedido["orden"])
    with override_settings(SEGUIMIENTO_CLAVE="clave-original"):
        assert codigo_seguimiento(pedido["orden"]) != codigo_otra_clave


# --------------------------------------------------------------------------
# Acceso
# --------------------------------------------------------------------------
def test_sin_clave_responde_401(pedido):
    respuesta = _consultar(pedido["orden"], api=_api(clave=None))
    assert respuesta.status_code == 401


def test_clave_invalida_responde_401(pedido):
    respuesta = _consultar(pedido["orden"], api=_api(clave="clave-falsa"))
    assert respuesta.status_code == 401


def test_codigo_incorrecto_y_numero_inexistente_dan_el_mismo_404(pedido):
    malo = _consultar(pedido["orden"], codigo="AAAAA-BBBBB")
    inexistente = _api().get(URL.format("OC-2099-9999"), {"codigo": "AAAAA-BBBBB"})
    assert malo.status_code == inexistente.status_code == 404
    assert malo.data["detail"] == inexistente.data["detail"]


def test_limite_de_solicitudes_por_clave(pedido):
    with override_settings(API_PUBLICA_LIMITE="2/min"):
        api = _api()
        assert _consultar(pedido["orden"], api).status_code == 200
        assert _consultar(pedido["orden"], api).status_code == 200
        assert _consultar(pedido["orden"], api).status_code == 429


def test_la_api_interna_sigue_exigiendo_usuario(pedido):
    assert _api().get("/api/v1/ordenes-compra/").status_code == 401


# --------------------------------------------------------------------------
# Contenido de la respuesta
# --------------------------------------------------------------------------
def test_pedido_recien_recibido(pedido):
    datos = _consultar(pedido["orden"]).json()
    assert datos["numero"] == "OC-2026-0001"
    assert datos["etapa_actual"] == "recibido"
    assert datos["avance_pct"] == 5
    assert [e["actual"] for e in datos["etapas"]] == [True, False, False, False, False, False]
    # No expone montos ni datos del cliente
    texto = str(datos)
    assert "total_uf" not in texto and "Maipo" not in texto


def test_avance_durante_la_fabricacion(pedido):
    _cambiar_oc(pedido, "confirmada")
    _cambiar_oc(pedido, "en_produccion")
    _crear_ot(pedido, "OT-2026-0001", "en_ejecucion", avance=Decimal("50"))
    _crear_ot(pedido, "OT-2026-0002", "en_ejecucion", avance=Decimal("100"))
    datos = _consultar(pedido["orden"]).json()
    assert datos["etapa_actual"] == "fabricacion"
    assert datos["avance_pct"] == 15 + round(60 * 75 / 100)
    assert [e["completada"] for e in datos["etapas"][:3]] == [True, True, False]
    assert datos["etapas"][1]["fecha"] is not None
    assert len(datos["productos"]) == 2
    assert [h["documento"] for h in datos["historial"]].count("OC-2026-0001") == 2


def test_la_etapa_la_marca_la_ot_mas_atrasada(pedido):
    _cambiar_oc(pedido, "confirmada")
    _crear_ot(pedido, "OT-2026-0001", "liberada")
    _crear_ot(pedido, "OT-2026-0002", "en_calidad")
    _crear_ot(pedido, "OT-2026-0003", "anulada")  # no cuenta
    datos = _consultar(pedido["orden"]).json()
    assert datos["etapa_actual"] == "calidad"
    assert datos["avance_pct"] == 85


def test_pedido_entregado(pedido):
    _cambiar_oc(pedido, "confirmada")
    _crear_ot(pedido, "OT-2026-0001", "cerrada")
    _cambiar_oc(pedido, "entregada")
    datos = _consultar(pedido["orden"]).json()
    assert datos["etapa_actual"] == "entregado"
    assert datos["avance_pct"] == 100
    assert all(e["completada"] for e in datos["etapas"])
    assert datos["entrega"]["dias_habiles_restantes"] == 0
    assert datos["entrega"]["atrasado"] is False


def test_pedido_anulado(pedido):
    _cambiar_oc(pedido, "anulada")
    datos = _consultar(pedido["orden"]).json()
    assert datos["anulado"] is True
    assert datos["etapa_actual"] == "anulado"
    assert datos["avance_pct"] == 0
    assert not any(e["actual"] or e["completada"] for e in datos["etapas"])


# --------------------------------------------------------------------------
# Fecha estimada de entrega
# --------------------------------------------------------------------------
def test_fecha_calculada_en_dias_habiles(pedido):
    datos = _consultar(pedido["orden"]).json()["entrega"]
    assert datos["origen"] == "calculada"
    assert datos["fecha_estimada"] is not None
    assert datos["considera_feriados"] is False  # no hay feriados cargados
    assert 0 < datos["dias_habiles_restantes"] <= 20


def test_feriado_desplaza_la_fecha(pedido):
    sin_feriado = _consultar(pedido["orden"]).json()["entrega"]["fecha_estimada"]
    habil = HOY + datetime.timedelta(days=1)
    while habil.weekday() >= 5:
        habil += datetime.timedelta(days=1)
    Feriado.objects.create(fecha=habil, nombre="Feriado de prueba")
    con_feriado = _consultar(pedido["orden"]).json()["entrega"]["fecha_estimada"]
    assert con_feriado > sin_feriado


def test_fecha_comprometida_atrasada(pedido):
    cotizacion = pedido["cotizacion"]
    cotizacion.fecha_entrega = HOY - datetime.timedelta(days=3)
    cotizacion.save()
    datos = _consultar(pedido["orden"]).json()["entrega"]
    assert datos["origen"] == "comprometida"
    assert datos["atrasado"] is True
    assert datos["dias_habiles_restantes"] == 0


# --------------------------------------------------------------------------
# Registro de uso y documentacion
# --------------------------------------------------------------------------
def test_cada_consulta_queda_registrada_sin_el_codigo(pedido):
    codigo = codigo_seguimiento(pedido["orden"])
    _consultar(pedido["orden"])
    _consultar(pedido["orden"], codigo="AAAAA-BBBBB")
    registros = LogIntegracion.objects.filter(servicio="api_seguimiento").order_by("id_log")
    assert [r.codigo_respuesta for r in registros] == [200, 404]
    assert registros[0].exitoso and not registros[1].exitoso
    assert "[portal-web]" in registros[0].endpoint
    assert all(codigo not in r.endpoint for r in registros)


def test_documentacion_swagger_solo_muestra_la_api_publica(db):
    esquema = APIClient().get("/api/publica/v1/esquema/", {"format": "json"})
    assert esquema.status_code == 200
    rutas = esquema.json()["paths"]
    assert "/api/publica/v1/seguimiento/{numero}/" in rutas
    assert not any(r.startswith("/api/v1/") for r in rutas)
    assert "ClaveApi" in esquema.json()["components"]["securitySchemes"]
    assert APIClient().get("/api/publica/v1/docs/").status_code == 200


# --------------------------------------------------------------------------
# Consumo desde el portal web
# --------------------------------------------------------------------------
def test_pagina_publica_no_exige_sesion_y_usa_la_clave_del_portal(pedido):
    with override_settings(API_PUBLICA_CLAVE_PORTAL=CLAVE):
        respuesta = APIClient().get("/seguimiento-pedido/", {"numero": "OC-2026-0001"})
    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert CLAVE in contenido and "/api/publica/v1/seguimiento/" in contenido


def test_mis_pedidos_muestra_el_codigo_de_seguimiento(pedido):
    cuenta = Usuario.objects.create_user("maipo", "maipo@cliente.cl", "Clave123456",
                                         es_interno=False, cliente=pedido["orden"].cliente)
    web = APIClient()
    web.force_login(cuenta)
    contenido = web.get("/mis-pedidos/").content.decode()
    assert codigo_seguimiento(pedido["orden"]) in contenido
    assert "/seguimiento-pedido/?numero=OC-2026-0001" in contenido
