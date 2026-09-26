"""
Pruebas del control de calidad operado desde la API: protocolos versionados,
ejecucion de ensayos con conformidad automatica, no conformidades y cierre de
la orden de trabajo (RN-12).
"""
import datetime
from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.calidad.models import NoConformidad, ProtocoloCalidad
from apps.catalogo.models import FamiliaProducto, ModeloProducto
from apps.clientes.models import Cliente
from apps.comercial.models import Cotizacion, EstadoDocumento, OrdenCompra, SolicitudPresupuesto
from apps.produccion.models import OrdenTrabajo
from apps.seguridad import matriz
from apps.seguridad.models import Rol, Usuario, UsuarioRol

HOY = datetime.date.today()

PUNTOS = [
    {"nombre": "Resistencia de aislamiento", "unidad": "MOhm", "tolerancia_inf": "1000"},
    {"nombre": "Relacion de transformacion", "unidad": "%", "tolerancia_inf": "-0.5",
     "tolerancia_sup": "0.5"},
    {"nombre": "Nivel de ruido", "unidad": "dB", "tolerancia_sup": "60",
     "obligatorio": False},
]


def _api(nombre, rol):
    usuario = Usuario.objects.create_user(nombre, f"{nombre}@sitrafo.cl", "Clave123456",
                                          es_interno=True)
    UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    api = APIClient()
    api.force_authenticate(usuario)
    return api


def _estado(tipo, codigo):
    return EstadoDocumento.objects.get(tipo_documento=tipo, codigo=codigo)


@pytest.fixture
def planta(db):
    call_command("cargar_estados", verbosity=0)
    call_command("cargar_roles", verbosity=0)
    calidad = _api("calidad", matriz.CALIDAD)
    produccion = _api("produccion", matriz.PRODUCCION)
    comercial = Usuario.objects.create_user("com", "c@s.cl", "Clave123456", es_interno=True)

    modelo = ModeloProducto.objects.create(
        familia=FamiliaProducto.objects.create(nombre="Distribucion"),
        codigo="TD-100", nombre="Transformador 100 kVA",
    )
    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    solicitud = SolicitudPresupuesto.objects.create(
        numero="SP-2026-0001", cliente=cliente, modelo=modelo, cantidad=1,
        estado=_estado("solicitud", "cotizada"))
    cotizacion = Cotizacion.objects.create(
        numero="COT-2026-0001", solicitud=solicitud, cliente=cliente,
        estado=_estado("cotizacion", "aceptada"), ejecutivo=comercial,
        valor_uf=Decimal("40000"), fecha_valor_uf=HOY,
        vence_el=HOY + datetime.timedelta(days=30), total_uf=Decimal("50"))
    orden = OrdenCompra.objects.create(
        numero="OC-2026-0001", cotizacion=cotizacion, cliente=cliente,
        estado=_estado("orden_compra", "en_produccion"), total_uf=Decimal("50"))
    ot = OrdenTrabajo.objects.create(
        numero="OT-2026-0001", orden_compra=orden, modelo=modelo, cantidad=1,
        estado=_estado("orden_trabajo", "en_calidad"), costo_estimado_uf=Decimal("0"))
    return {"calidad": calidad, "produccion": produccion, "modelo": modelo, "ot": ot}


def _protocolo(planta, puntos=None):
    respuesta = planta["calidad"].post("/api/v1/protocolos/", {
        "modelo": planta["modelo"].pk, "nombre": "Ensayos de rutina",
        "norma_referencia": "IEC 60076-1", "puntos": puntos or PUNTOS,
    }, format="json")
    assert respuesta.status_code == 201, respuesta.data
    return respuesta.data


def _control(planta):
    protocolo = _protocolo(planta)
    respuesta = planta["calidad"].post("/api/v1/controles-calidad/", {
        "orden_trabajo": planta["ot"].pk, "protocolo": protocolo["id_protocolo"]},
        format="json")
    assert respuesta.status_code == 201, respuesta.data
    return respuesta.data


def _medir(planta, control, indice, valor, **extra):
    punto = control["puntos"][indice]["id_punto"]
    return planta["calidad"].post(
        f"/api/v1/controles-calidad/{control['id_control']}/registrar_resultado/",
        {"punto": punto, "valor": str(valor), **extra}, format="json")


# ---------------------------------------------------------------------------
# Protocolos
# ---------------------------------------------------------------------------
def test_protocolo_valida_rangos_y_solo_lo_define_calidad(planta):
    sin_rango = planta["calidad"].post("/api/v1/protocolos/", {
        "modelo": planta["modelo"].pk, "nombre": "X",
        "puntos": [{"nombre": "Sin limites", "unidad": "V"}]}, format="json")
    assert sin_rango.status_code == 409

    datos = {"modelo": planta["modelo"].pk, "nombre": "X", "puntos": PUNTOS}
    assert planta["produccion"].post("/api/v1/protocolos/", datos,
                                     format="json").status_code == 403


def test_modificar_un_protocolo_aplicado_crea_una_version(planta):
    control = _control(planta)
    url = f"/api/v1/protocolos/{control['protocolo']}/"
    respuesta = planta["calidad"].put(url, {
        "modelo": planta["modelo"].pk, "nombre": "Ensayos de rutina",
        "puntos": PUNTOS[:2]}, format="json")

    assert respuesta.status_code == 201
    assert respuesta.data["version"] == 2
    v1 = ProtocoloCalidad.objects.get(version=1)
    assert v1.activo is False and v1.puntos.count() == 3   # el criterio historico queda


# ---------------------------------------------------------------------------
# Ensayos y no conformidades
# ---------------------------------------------------------------------------
def test_la_conformidad_la_calcula_el_sistema_y_abre_la_nc(planta):
    control = _control(planta)

    ok = _medir(planta, control, 0, 2500)
    assert ok.data["puntos"][0]["conforme"] is True

    fuera = _medir(planta, control, 1, "0.8", severidad="critica")
    assert fuera.data["puntos"][1]["conforme"] is False
    assert fuera.data["estado"] == "con_nc"
    nc = NoConformidad.objects.get()
    assert nc.severidad == "critica" and nc.estado == "abierta"
    assert "fuera de rango" in nc.descripcion

    # No se repite el ensayo mientras la NC siga abierta
    assert _medir(planta, control, 1, "0.1").status_code == 409


def test_cerrar_nc_exige_accion_correctiva_y_luego_se_repite(planta):
    control = _control(planta)
    _medir(planta, control, 1, "0.9")
    nc = NoConformidad.objects.get()
    url = f"/api/v1/no-conformidades/{nc.pk}/cerrar/"

    assert planta["calidad"].post(url, {"accion_correctiva": "ok"},
                                  format="json").status_code == 409
    assert planta["produccion"].post(url, {"accion_correctiva": "Se rebobino"},
                                     format="json").status_code == 403
    cierre = planta["calidad"].post(
        url, {"accion_correctiva": "Se corrigio el numero de espiras del devanado AT"},
        format="json")
    assert cierre.status_code == 200

    repetido = _medir(planta, control, 1, "0.2")
    assert repetido.status_code == 200
    assert repetido.data["puntos"][1]["mediciones"] == 2      # la historia se conserva


def test_produccion_ve_los_controles_pero_no_mide(planta):
    control = _control(planta)
    assert planta["produccion"].get("/api/v1/controles-calidad/").status_code == 200
    url = f"/api/v1/controles-calidad/{control['id_control']}/registrar_resultado/"
    assert planta["produccion"].post(url, {}, format="json").status_code == 403


# ---------------------------------------------------------------------------
# Cierre de la orden (RN-12)
# ---------------------------------------------------------------------------
def test_la_orden_se_cierra_solo_con_calidad_completa(planta):
    control = _control(planta)
    cerrar = f"/api/v1/ordenes-trabajo/{planta['ot'].pk}/cerrar/"

    _medir(planta, control, 0, 2500)
    _medir(planta, control, 1, "0.9")
    bloqueo = planta["produccion"].post(cerrar, {}, format="json")
    assert bloqueo.status_code == 409
    assert "no conformidad" in bloqueo.data["detalle"]

    nc = NoConformidad.objects.get()
    planta["calidad"].post(f"/api/v1/no-conformidades/{nc.pk}/cerrar/",
                           {"accion_correctiva": "Ajuste de derivaciones del devanado"},
                           format="json")
    # El ruido no es obligatorio: no impide cerrar
    respuesta = planta["produccion"].post(cerrar, {}, format="json")
    assert respuesta.status_code == 200, respuesta.data
    assert respuesta.data["estado_codigo"] == "cerrada"


# ---------------------------------------------------------------------------
# Saldo y entrega (RN-15)
# ---------------------------------------------------------------------------
def test_cerrar_la_ultima_ot_emite_el_saldo_y_la_entrega_exige_pagarlo(
        planta, django_capture_on_commit_callbacks):
    from django.core import mail

    from apps.clientes.models import ContactoCliente
    from apps.pagos.models import DocumentoCobro, IndicadorEconomico

    IndicadorEconomico.objects.create(codigo="UF", fecha=HOY, valor=Decimal("40000"))
    orden = planta["ot"].orden_compra
    ContactoCliente.objects.create(cliente=orden.cliente, nombre="Compras",
                                   email="compras@maipo.cl", principal=True)
    control = _control(planta)
    for i, valor in enumerate(["2500", "0.1", "50"]):
        _medir(planta, control, i, valor)

    with django_capture_on_commit_callbacks(execute=True):
        cierre = planta["produccion"].post(
            f"/api/v1/ordenes-trabajo/{planta['ot'].pk}/cerrar/", {}, format="json")
    assert cierre.status_code == 200

    saldo = DocumentoCobro.objects.get(tipo="saldo")
    assert saldo.monto_uf == orden.monto_saldo_uf
    assert saldo.monto_clp == saldo.monto_uf * Decimal("40000")
    assert "esta listo" in mail.outbox[-1].subject

    comercial = _api("comercial", matriz.COMERCIAL)
    entrega = f"/api/v1/ordenes-compra/{orden.pk}/registrar_entrega/"
    assert comercial.post(entrega).status_code == 409          # saldo sin pagar
    saldo.estado = DocumentoCobro.Estado.PAGADO
    saldo.save()
    respuesta = comercial.post(entrega)
    assert respuesta.status_code == 200
    assert respuesta.data["estado_codigo"] == "entregada"
