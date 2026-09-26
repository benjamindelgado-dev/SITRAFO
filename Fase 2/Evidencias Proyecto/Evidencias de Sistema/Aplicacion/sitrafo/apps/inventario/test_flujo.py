"""
Pruebas del inventario (HU-10): recepcion, ajuste por conteo fisico, kardex
con saldo acumulado, alertas de stock minimo y segregacion por rol.
"""
import datetime
from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.inventario.models import (
    Bodega,
    CategoriaMaterial,
    Material,
    MovimientoInventario,
    PrecioMaterial,
    Proveedor,
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
def bodega(db):
    call_command("cargar_roles", verbosity=0)
    cobre = Material.objects.create(
        categoria=CategoriaMaterial.objects.create(nombre="Conductores"),
        codigo="CU-01", nombre="Cobre esmaltado", unidad_medida="kg",
        stock_minimo=Decimal("50"),
    )
    PrecioMaterial.objects.create(material=cobre, costo_uf=Decimal("0.35"),
                                  vigente_desde=datetime.date(2026, 1, 1))
    return {"bodeguero": _api("bodega", matriz.BODEGA),
            "operario": _api("operario", matriz.OPERARIO),
            "produccion": _api("produccion", matriz.PRODUCCION),
            "cobre": cobre, "central": Bodega.objects.create(codigo="B1", nombre="Central"),
            "proveedor": Proveedor.objects.create(rut="76086428-5",
                                                  razon_social="Cobres del Sur")}


def _url(bodega, accion):
    return f"/api/v1/materiales/{bodega['cobre'].pk}/{accion}/"


def _recibir(bodega, cantidad, **extra):
    return bodega["bodeguero"].post(_url(bodega, "recepcion"), {
        "bodega": bodega["central"].pk, "cantidad": str(cantidad), **extra}, format="json")


def test_recepcion_sube_el_stock_con_el_costo_de_la_compra(bodega):
    respuesta = _recibir(bodega, 100, proveedor=bodega["proveedor"].pk,
                         documento="Factura 1234")
    assert respuesta.status_code == 200, respuesta.data
    assert Decimal(respuesta.data["stock_total"]) == Decimal("100")
    movimiento = MovimientoInventario.objects.get()
    assert movimiento.costo_unitario_uf == Decimal("0.35")      # precio vigente
    assert movimiento.proveedor == bodega["proveedor"]


def test_recepcion_con_otro_costo_puede_abrir_nueva_vigencia(bodega):
    _recibir(bodega, 10, costo_unitario_uf="0.40", actualizar_precio=True)
    cobre = Material.objects.get()
    assert cobre.costo_vigente == Decimal("0.40")
    assert cobre.precios.count() == 2                        # el precio anterior se conserva


def test_ajuste_registra_la_diferencia_del_conteo_y_queda_auditado(bodega):
    _recibir(bodega, 100)
    respuesta = bodega["bodeguero"].post(_url(bodega, "ajuste"), {
        "bodega": bodega["central"].pk, "conteo_fisico": "97",
        "motivo": "Merma detectada en inventario ciclico"}, format="json")

    assert respuesta.status_code == 200
    ajuste = MovimientoInventario.objects.get(tipo="ajuste")
    assert ajuste.cantidad == Decimal("-3")
    assert Auditoria.objects.filter(entidad="inventario").exists()


def test_ajuste_exige_motivo_y_no_admite_conteo_negativo(bodega):
    base = {"bodega": bodega["central"].pk}
    assert bodega["bodeguero"].post(_url(bodega, "ajuste"),
                                    {**base, "conteo_fisico": "5", "motivo": ""},
                                    format="json").status_code in (400, 409)
    assert bodega["bodeguero"].post(_url(bodega, "ajuste"),
                                    {**base, "conteo_fisico": "-1", "motivo": "Error"},
                                    format="json").status_code == 409


def test_kardex_muestra_saldo_acumulado(bodega):
    _recibir(bodega, 100)
    bodega["bodeguero"].post(_url(bodega, "ajuste"), {
        "bodega": bodega["central"].pk, "conteo_fisico": "90",
        "motivo": "Conteo de cierre de mes"}, format="json")
    datos = bodega["bodeguero"].get(_url(bodega, "kardex")).data

    saldos = [Decimal(m["saldo"]) for m in datos["movimientos"]]
    assert saldos == [Decimal("100"), Decimal("90")]
    assert Decimal(datos["saldo"]) == Decimal("90")


def test_alerta_de_stock_bajo_el_minimo(bodega):
    _recibir(bodega, 30)                                      # minimo: 50
    alertas = bodega["bodeguero"].get("/api/v1/materiales/?bajo_minimo=1").data
    assert [m["codigo"] for m in alertas] == ["CU-01"]
    _recibir(bodega, 30)
    assert bodega["bodeguero"].get("/api/v1/materiales/?bajo_minimo=1").data == []


def test_solo_bodega_mueve_inventario(bodega):
    datos = {"bodega": bodega["central"].pk, "cantidad": "5"}
    assert bodega["operario"].post(_url(bodega, "recepcion"), datos,
                                   format="json").status_code == 403
    assert bodega["produccion"].post(_url(bodega, "recepcion"), datos,
                                     format="json").status_code == 403
    # Produccion si consulta el kardex; el operario ve materiales para consumir
    assert bodega["produccion"].get(_url(bodega, "kardex")).status_code == 200
    assert bodega["operario"].get("/api/v1/materiales/").status_code == 200


def test_bodega_crea_materiales_y_proveedores(bodega):
    material = bodega["bodeguero"].post("/api/v1/materiales/", {
        "categoria": bodega["cobre"].categoria_id, "codigo": "AIS-01",
        "nombre": "Papel aislante", "unidad_medida": "kg", "stock_minimo": "20",
        "costo_uf": "0.05"}, format="json")
    assert material.status_code == 201, material.data
    assert Material.objects.get(codigo="AIS-01").costo_vigente == Decimal("0.05")

    proveedor = bodega["bodeguero"].post("/api/v1/proveedores/", {
        "rut": "77111222-6", "razon_social": "Aislantes SpA"}, format="json")
    assert proveedor.status_code == 201, proveedor.data
