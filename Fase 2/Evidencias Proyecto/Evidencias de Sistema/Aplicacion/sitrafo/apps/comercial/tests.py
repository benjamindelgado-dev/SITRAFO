"""
Pruebas del dominio comercial.

Verifican las reglas de negocio que condicionan el flujo: vigencia de la
cotizacion, umbral de descuento, congelamiento del valor de la UF y
generacion de la orden de compra.
"""
import datetime
from decimal import Decimal

import pytest

from apps.catalogo.models import FamiliaProducto, ModeloProducto
from apps.clientes.models import Cliente
from apps.comercial.models import (
    Cotizacion,
    CotizacionLinea,
    EstadoDocumento,
    OrdenCompra,
    SolicitudPresupuesto,
)


@pytest.fixture
def datos_base(db, django_user_model):
    usuario = django_user_model.objects.create_user(
        "ejecutivo", "e@e.cl", "Clave12345", es_interno=True
    )
    cliente = Cliente.objects.create(
        rut="76543210-3", razon_social="Electrica del Maipo SpA",
        tipo_persona="juridica",
    )
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    modelo = ModeloProducto.objects.create(
        familia=familia, codigo="TD-100", nombre="Transformador 100 kVA",
        publicado=True,
    )
    estado_sol = EstadoDocumento.objects.create(
        tipo_documento="solicitud", codigo="recibida", nombre="Recibida"
    )
    estado_cot = EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="emitida", nombre="Emitida"
    )
    solicitud = SolicitudPresupuesto.objects.create(
        numero="SP-2026-0001", cliente=cliente, modelo=modelo,
        cantidad=1, estado=estado_sol,
    )
    return {
        "usuario": usuario, "cliente": cliente, "modelo": modelo,
        "solicitud": solicitud, "estado_cot": estado_cot,
    }


def _cotizacion(datos, vence_el, **extra):
    return Cotizacion.objects.create(
        numero=extra.pop("numero", "COT-2026-0001"),
        solicitud=datos["solicitud"],
        cliente=datos["cliente"],
        estado=datos["estado_cot"],
        ejecutivo=datos["usuario"],
        valor_uf=Decimal("40125.50"),
        fecha_valor_uf=datetime.date(2026, 9, 23),
        vence_el=vence_el,
        **extra,
    )


@pytest.mark.django_db
def test_correlativo_de_solicitud(datos_base):
    numero = SolicitudPresupuesto.generar_numero()
    anio = datetime.date.today().year
    assert numero.startswith(f"SP-{anio}-")


@pytest.mark.django_db
def test_cotizacion_vigente(datos_base):
    futura = datetime.date.today() + datetime.timedelta(days=10)
    assert _cotizacion(datos_base, futura).esta_vigente is True


@pytest.mark.django_db
def test_cotizacion_vencida(datos_base):
    """RN-04: una cotizacion vencida no puede aceptarse."""
    pasada = datetime.date.today() - datetime.timedelta(days=1)
    assert _cotizacion(datos_base, pasada).esta_vigente is False


@pytest.mark.django_db
def test_vencimiento_por_defecto_treinta_dias(datos_base):
    hoy = datetime.date(2026, 9, 23)
    assert Cotizacion.calcular_vencimiento(hoy) == datetime.date(2026, 10, 23)


@pytest.mark.django_db
def test_descuento_sobre_el_umbral_requiere_aprobacion(datos_base):
    """RN-05."""
    futura = datetime.date.today() + datetime.timedelta(days=10)
    sin_umbral = _cotizacion(datos_base, futura, descuento_pct=Decimal("5"))
    con_umbral = _cotizacion(
        datos_base, futura, numero="COT-2026-0002", descuento_pct=Decimal("15")
    )

    assert sin_umbral.requiere_aprobacion is False
    assert con_umbral.requiere_aprobacion is True


@pytest.mark.django_db
def test_precio_de_linea_aplica_el_margen(datos_base):
    """RF-COM-04: precio = costo estimado mas margen."""
    futura = datetime.date.today() + datetime.timedelta(days=10)
    cotizacion = _cotizacion(datos_base, futura)
    linea = CotizacionLinea(
        cotizacion=cotizacion, modelo=datos_base["modelo"], cantidad=1,
        costo_material_uf=Decimal("27.2000"),
        costo_hh_uf=Decimal("12.5000"),
        margen_pct=Decimal("25"),
    )

    assert linea.costo_estimado_uf == Decimal("39.7000")
    assert linea.calcular_precio() == Decimal("49.6250")


@pytest.mark.django_db
def test_total_aplica_descuento(datos_base):
    futura = datetime.date.today() + datetime.timedelta(days=10)
    cotizacion = _cotizacion(datos_base, futura, descuento_pct=Decimal("10"))
    CotizacionLinea.objects.create(
        cotizacion=cotizacion, modelo=datos_base["modelo"], cantidad=2,
        precio_uf=Decimal("50"),
    )

    assert cotizacion.recalcular_total() == Decimal("90.0000")


@pytest.mark.django_db
def test_valor_uf_queda_congelado(datos_base):
    """RN-03: el total en pesos usa la UF guardada, no la vigente."""
    futura = datetime.date.today() + datetime.timedelta(days=10)
    cotizacion = _cotizacion(datos_base, futura, total_uf=Decimal("100"))

    assert cotizacion.total_clp == Decimal("4012550")


@pytest.mark.django_db
def test_anticipo_y_saldo(datos_base):
    """RN-15: el anticipo se calcula sobre el total."""
    futura = datetime.date.today() + datetime.timedelta(days=10)
    cotizacion = _cotizacion(datos_base, futura, total_uf=Decimal("100"))
    estado_oc = EstadoDocumento.objects.create(
        tipo_documento="orden_compra", codigo="pendiente", nombre="Pendiente"
    )
    orden = OrdenCompra.objects.create(
        numero="OC-2026-0001", cotizacion=cotizacion,
        cliente=datos_base["cliente"], estado=estado_oc,
        total_uf=Decimal("100"), anticipo_pct=Decimal("50"),
    )

    assert orden.monto_anticipo_uf == Decimal("50.0000")
    assert orden.monto_saldo_uf == Decimal("50.0000")


# ---------------------------------------------------------------------------
# Datos de demostracion
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_cargar_demo_es_repetible_y_emite_el_anticipo():
    """
    El comando no debe fallar si ya existen documentos numerados (se usan los
    correlativos del sistema) y debe dejar el anticipo listo para pagar.
    """
    import datetime as _dt
    from io import StringIO
    from unittest.mock import patch as _patch

    from django.core.management import call_command

    from apps.comercial.models import OrdenCompra
    from apps.pagos.models import DocumentoCobro, IndicadorEconomico

    IndicadorEconomico.objects.create(
        codigo="UF", fecha=_dt.date(2026, 1, 1), valor=Decimal("40000")
    )
    salida = StringIO()
    call_command("cargar_estados", stdout=salida)
    with _patch("requests.get", side_effect=AssertionError("sin red en pruebas")):
        call_command("cargar_demo", stdout=salida)
        call_command("cargar_demo", stdout=salida)            # ya cargado: no hace nada
        call_command("cargar_demo", "--forzar", stdout=salida)  # vuelve a sembrar

    assert "No se pudo sembrar" not in salida.getvalue()
    assert OrdenCompra.objects.count() == 2
    assert DocumentoCobro.objects.filter(tipo="anticipo").count() == 2


@pytest.mark.django_db
def test_emitir_cotizacion_la_envia_por_correo(datos_base):
    """RF-COM-09: al emitir desde la API, el cliente recibe la cotizacion."""
    from django.core import mail
    from rest_framework.test import APIClient

    from apps.clientes.models import ContactoCliente

    datos_base["usuario"].is_superuser = True
    datos_base["usuario"].save()
    ContactoCliente.objects.create(cliente=datos_base["cliente"], nombre="Compras",
                                   email="compras@maipo.cl", principal=True)
    cotizacion = _cotizacion(
        datos_base, datetime.date.today() + datetime.timedelta(days=30)
    )
    cotizacion.estado = EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="borrador", nombre="Borrador"
    )
    cotizacion.save()
    CotizacionLinea.objects.create(
        cotizacion=cotizacion, modelo=datos_base["modelo"], cantidad=1,
        precio_uf=Decimal("150.0000"),
    )

    api = APIClient()
    api.force_authenticate(datos_base["usuario"])
    respuesta = api.post(f"/api/v1/cotizaciones/{cotizacion.pk}/emitir/")

    assert respuesta.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["compras@maipo.cl"]
    assert cotizacion.numero in mail.outbox[0].subject
    assert "150,00 UF" in mail.outbox[0].body  # formato chileno
