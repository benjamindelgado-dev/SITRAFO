"""
Pruebas del flujo comercial operado desde la API (lo que usa la aplicacion de
escritorio): costeo, elaboracion de la cotizacion, aprobacion por descuento,
emision, aceptacion y generacion de la orden de compra con su anticipo.
"""
import datetime
from decimal import Decimal

import pytest
from django.core import mail
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.catalogo.models import (
    BomModelo,
    FamiliaProducto,
    ModeloProducto,
    PrecioBaseModelo,
    TareaEstandarModelo,
)
from apps.clientes.models import Cliente
from apps.comercial.models import Cotizacion, EstadoDocumento, SolicitudPresupuesto
from apps.inventario.models import CategoriaMaterial, Material, PrecioMaterial
from apps.pagos.models import DocumentoCobro, IndicadorEconomico
from apps.produccion.models import Empleado, TarifaHoraHombre

HOY = datetime.date.today()


@pytest.fixture
def flujo(db, django_user_model):
    call_command("cargar_estados", verbosity=0)
    IndicadorEconomico.objects.create(codigo="UF", fecha=HOY, valor=Decimal("40000"))

    ejecutivo = django_user_model.objects.create_user(
        "ejecutivo", "e@sitrafo.cl", "Clave123456", es_interno=True
    )
    cliente = Cliente.objects.create(
        rut="76543210-3", razon_social="Electrica del Maipo SpA", tipo_persona="juridica"
    )
    cuenta = django_user_model.objects.create_user(
        "maipo", "compras@maipo.cl", "ClaveSegura2026", cliente=cliente
    )
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    modelo = ModeloProducto.objects.create(
        familia=familia, codigo="TD-100", nombre="Transformador 100 kVA", publicado=True
    )
    PrecioBaseModelo.objects.create(
        modelo=modelo, monto_uf=Decimal("180"), vigente_desde=datetime.date(2026, 1, 1),
        usuario=ejecutivo,
    )
    solicitud = SolicitudPresupuesto.objects.create(
        numero=SolicitudPresupuesto.generar_numero(), cliente=cliente, modelo=modelo,
        cantidad=2,
        estado=EstadoDocumento.objects.get(tipo_documento="solicitud", codigo="recibida"),
    )

    interno = APIClient()
    interno.force_authenticate(ejecutivo)
    externo = APIClient()
    externo.force_authenticate(cuenta)
    return {"interno": interno, "externo": externo, "modelo": modelo,
            "solicitud": solicitud, "ejecutivo": ejecutivo}


def _url_solicitud(flujo, accion):
    return f"/api/v1/solicitudes/{flujo['solicitud'].pk}/{accion}/"


def _cotizar(flujo, **datos):
    respuesta = flujo["interno"].post(_url_solicitud(flujo, "cotizar"), datos, format="json")
    assert respuesta.status_code == 201, respuesta.data
    return respuesta.data


# ---------------------------------------------------------------------------
# Costeo (RF-COM-04)
# ---------------------------------------------------------------------------
def test_costeo_sin_bom_sugiere_el_precio_base(flujo):
    datos = flujo["interno"].get(_url_solicitud(flujo, "costeo")).data
    assert datos["origen_precio"] == "precio_base"
    assert Decimal(datos["precio_sugerido_uf"]) == Decimal("180")
    assert datos["cantidad"] == 2


def test_costeo_con_bom_y_tarifa_aplica_el_margen(flujo):
    categoria = CategoriaMaterial.objects.create(nombre="Conductores")
    cobre = Material.objects.create(categoria=categoria, codigo="CU-01",
                                    nombre="Alambre de cobre", unidad_medida="kg")
    PrecioMaterial.objects.create(material=cobre, costo_uf=Decimal("0.5"),
                                  vigente_desde=datetime.date(2026, 1, 1))
    BomModelo.objects.create(modelo=flujo["modelo"], material=cobre, cantidad=Decimal("100"))
    TareaEstandarModelo.objects.create(modelo=flujo["modelo"], nombre="Bobinado",
                                       secuencia=1, horas_estimadas=Decimal("20"))
    empleado = Empleado.objects.create(rut="12345678-5", nombre="Juan Perez",
                                       cargo="Bobinador")
    TarifaHoraHombre.objects.create(empleado=empleado, valor_hora_uf=Decimal("0.5"),
                                    vigente_desde=datetime.date(2026, 1, 1))

    datos = flujo["interno"].get(_url_solicitud(flujo, "costeo")).data

    assert datos["origen_precio"] == "costeo"
    assert Decimal(datos["costo_material_uf"]) == Decimal("50")    # 100 kg x 0,5
    assert Decimal(datos["costo_hh_uf"]) == Decimal("10")          # 20 h x 0,5
    assert Decimal(datos["precio_sugerido_uf"]) == Decimal("75")   # 60 + 25 %


# ---------------------------------------------------------------------------
# Elaboracion y emision
# ---------------------------------------------------------------------------
def test_cotizar_crea_borrador_y_marca_la_solicitud(flujo):
    datos = _cotizar(flujo, plazo_dias_habiles=20)

    assert datos["estado_nombre"] == "Borrador"
    assert Decimal(datos["total_uf"]) == Decimal("360")   # 2 x 180
    assert Decimal(datos["valor_uf"]) == Decimal("40000")
    assert datos["plazo_dias_habiles"] == 20
    flujo["solicitud"].refresh_from_db()
    assert flujo["solicitud"].estado.codigo == "cotizada"
    assert flujo["solicitud"].ejecutivo == flujo["ejecutivo"]


def test_una_solicitud_cotizada_no_se_cotiza_dos_veces(flujo):
    _cotizar(flujo)
    respuesta = flujo["interno"].post(_url_solicitud(flujo, "cotizar"), {}, format="json")
    assert respuesta.status_code == 409


def test_cliente_no_puede_cotizar(flujo):
    respuesta = flujo["externo"].post(_url_solicitud(flujo, "cotizar"), {}, format="json")
    assert respuesta.status_code == 403


def test_emitir_solo_desde_borrador_y_envia_correo(flujo):
    cotizacion = _cotizar(flujo, precio_uf="200")
    url = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/emitir/"

    assert flujo["interno"].post(url).status_code == 200
    assert len(mail.outbox) == 1
    assert flujo["interno"].post(url).status_code == 409   # ya emitida


def test_descuento_sobre_el_umbral_exige_aprobacion(flujo):
    cotizacion = _cotizar(flujo, descuento_pct="15")
    base = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}"

    assert flujo["interno"].post(f"{base}/emitir/").status_code == 409
    assert flujo["interno"].post(f"{base}/solicitar_aprobacion/").status_code == 200
    respuesta = flujo["interno"].post(f"{base}/emitir/")
    assert respuesta.status_code == 200
    assert Decimal(respuesta.data["total_uf"]) == Decimal("306")   # 360 - 15 %


# ---------------------------------------------------------------------------
# Cadena completa hasta el anticipo
# ---------------------------------------------------------------------------
def test_cadena_completa_hasta_el_anticipo(flujo):
    cotizacion = _cotizar(flujo)
    base = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}"

    flujo["interno"].post(f"{base}/emitir/")
    assert flujo["externo"].post(f"{base}/aceptar/").status_code == 200
    respuesta = flujo["interno"].post(f"{base}/generar_orden_compra/")

    assert respuesta.status_code == 201
    documento = DocumentoCobro.objects.get()
    assert documento.orden_compra.numero == respuesta.data["numero"]
    assert documento.monto_uf == Decimal("180.0000")   # 50 % de 360
    historial = Cotizacion.objects.get().historial.values_list("estado_nuevo__codigo",
                                                                 flat=True)
    assert set(historial) == {"borrador", "emitida", "aceptada"}
