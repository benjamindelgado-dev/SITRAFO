"""
Pruebas del pago en linea con PayPal (CU-PAG-02) y de la emision de cobros.

PayPal se simula con dobles de prueba: la suite no depende de la
disponibilidad del Sandbox ni de credenciales reales. Se verifican las
reglas propias de SITRAFO: conciliacion del monto, idempotencia, aislamiento
entre clientes y degradacion controlada ante fallos de la pasarela.
"""
import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from requests.exceptions import ConnectTimeout

from apps.clientes.models import Cliente
from apps.comercial.models import (
    Cotizacion,
    EstadoDocumento,
    OrdenCompra,
    SolicitudPresupuesto,
)
from apps.configuracion.models import LogIntegracion, ParametroSistema
from apps.pagos.models import DocumentoCobro, IndicadorEconomico, TransaccionPago
from apps.pagos.services import cobros
from apps.seguridad.models import Auditoria

HOY = datetime.date(2026, 9, 24)


class RespuestaFalsa:
    def __init__(self, datos, status_code=200):
        self._datos = datos
        self.status_code = status_code

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._datos


class PayPalFalso:
    """
    Doble de prueba de la API de PayPal.

    Responde segun la URL y deja registro de las llamadas recibidas, para
    poder verificar cabeceras como la clave de idempotencia.
    """

    def __init__(self, monto_capturado=None, estado_captura="COMPLETED",
                 captura_codigo=201, captura_error=None):
        self.monto_capturado = monto_capturado
        self.estado_captura = estado_captura
        self.captura_codigo = captura_codigo
        self.captura_error = captura_error
        self.llamadas = []
        self.monto_solicitado = None

    def post(self, url, **kwargs):
        self.llamadas.append((url, kwargs))
        if url.endswith("/v1/oauth2/token"):
            return RespuestaFalsa({"access_token": "TOKEN-PRUEBA", "expires_in": 32400})
        if url.endswith("/v2/checkout/orders"):
            self.monto_solicitado = kwargs["json"]["purchase_units"][0]["amount"]["value"]
            return RespuestaFalsa({
                "id": "ORDEN-PP-1",
                "status": "PAYER_ACTION_REQUIRED",
                "links": [
                    {"rel": "self", "href": "https://api-m.sandbox.paypal.com/x"},
                    {"rel": "payer-action",
                     "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDEN-PP-1"},
                ],
            }, status_code=201)
        if url.endswith("/capture"):
            if self.captura_error:
                raise self.captura_error
            if self.captura_codigo >= 400:
                return RespuestaFalsa(
                    {"name": "UNPROCESSABLE_ENTITY",
                     "details": [{"issue": "INSTRUMENT_DECLINED"}]},
                    status_code=self.captura_codigo,
                )
            return RespuestaFalsa(self._orden_capturada(), status_code=201)
        raise AssertionError(f"URL no esperada: {url}")

    def get(self, url, **kwargs):
        self.llamadas.append((url, kwargs))
        return RespuestaFalsa(self._orden_capturada())

    def _orden_capturada(self):
        valor = self.monto_capturado or self.monto_solicitado
        return {
            "id": "ORDEN-PP-1",
            "status": "COMPLETED",
            "purchase_units": [{"payments": {"captures": [{
                "id": "CAPTURA-1",
                "status": self.estado_captura,
                "amount": {"currency_code": "USD", "value": valor},
            }]}}],
        }


@pytest.fixture(autouse=True)
def _paypal_configurado(settings):
    settings.PAYPAL_CLIENT_ID = "cliente-prueba"
    settings.PAYPAL_SECRET = "secreto-prueba"
    settings.PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def escenario(db, django_user_model, client):
    cliente = Cliente.objects.create(
        rut="76543210-3", razon_social="Electrica del Maipo SpA", tipo_persona="juridica"
    )
    otro = Cliente.objects.create(
        rut="77777777-7", razon_social="Otra Empresa Ltda", tipo_persona="juridica"
    )
    usuario = django_user_model.objects.create_user(
        "maipo", "c@c.cl", "ClaveSegura2026", cliente=cliente, es_interno=False
    )
    ajeno = django_user_model.objects.create_user(
        "ajeno", "a@a.cl", "ClaveSegura2026", cliente=otro, es_interno=False
    )
    interno = django_user_model.objects.create_user(
        "ejecutivo", "e@e.cl", "ClaveSegura2026", es_interno=True
    )

    solicitud = SolicitudPresupuesto.objects.create(
        numero="SP-2026-0001", cliente=cliente, cantidad=1,
        estado=EstadoDocumento.objects.create(
            tipo_documento="solicitud", codigo="cotizada", nombre="Cotizada"),
    )
    cotizacion = Cotizacion.objects.create(
        numero="COT-2026-0001", solicitud=solicitud, cliente=cliente,
        estado=EstadoDocumento.objects.create(
            tipo_documento="cotizacion", codigo="aceptada", nombre="Aceptada"),
        ejecutivo=interno, valor_uf=Decimal("40000"), fecha_valor_uf=HOY,
        vence_el=HOY + datetime.timedelta(days=30), total_uf=Decimal("100.0000"),
    )
    orden = OrdenCompra.objects.create(
        numero="OC-2026-0001", cotizacion=cotizacion, cliente=cliente,
        estado=EstadoDocumento.objects.create(
            tipo_documento="orden_compra", codigo="confirmada", nombre="Confirmada"),
        total_uf=Decimal("100.0000"), anticipo_pct=Decimal("50"),
    )

    IndicadorEconomico.objects.create(codigo="UF", fecha=HOY, valor=Decimal("40000"))
    IndicadorEconomico.objects.create(codigo="USD", fecha=HOY, valor=Decimal("950"))

    client.force_login(usuario)
    return {"client": client, "cliente": cliente, "usuario": usuario, "ajeno": ajeno,
            "orden": orden}


@pytest.fixture
def documento(escenario):
    documento, _ = cobros.emitir_anticipo(escenario["orden"])
    return documento


def _iniciar_y_volver(escenario, documento, paypal):
    """Recorre el flujo web completo: pagar, aprobar en PayPal y volver."""
    c = escenario["client"]
    with patch("requests.post", side_effect=paypal.post):
        respuesta = c.post(reverse("web:pagar_documento", args=[documento.pk]))
    assert respuesta.status_code == 302
    assert "sandbox.paypal.com/checkoutnow" in respuesta["Location"]

    with patch("requests.post", side_effect=paypal.post), patch("time.sleep"):
        return c.get(reverse("web:pago_retorno"), {"token": "ORDEN-PP-1",
                                                   "PayerID": "COMPRADOR"})


# ---------------------------------------------------------------------------
# Emision del documento de cobro (RN-15, RN-03)
# ---------------------------------------------------------------------------
def test_anticipo_congela_uf_y_pesos(documento):
    assert documento.tipo == DocumentoCobro.Tipo.ANTICIPO
    assert documento.monto_uf == Decimal("50.0000")
    assert documento.valor_uf == Decimal("40000")
    assert documento.monto_clp == Decimal("2000000")
    assert documento.numero.startswith("DC-")


def test_emitir_anticipo_es_idempotente(escenario, documento):
    otra_vez, creado = cobros.emitir_anticipo(escenario["orden"])
    assert creado is False
    assert otra_vez.pk == documento.pk
    assert DocumentoCobro.objects.count() == 1


def test_conversion_a_dolares():
    assert cobros.convertir_a_usd(Decimal("2000000"), Decimal("950")) == Decimal("2105.26")


# ---------------------------------------------------------------------------
# Flujo completo de pago
# ---------------------------------------------------------------------------
def test_pago_aprobado_marca_documento_pagado(escenario, documento):
    paypal = PayPalFalso()
    respuesta = _iniciar_y_volver(escenario, documento, paypal)

    assert respuesta.status_code == 302
    documento.refresh_from_db()
    transaccion = TransaccionPago.objects.get()
    assert documento.estado == DocumentoCobro.Estado.PAGADO
    assert transaccion.estado == TransaccionPago.Estado.APROBADA
    assert transaccion.moneda == "USD"
    assert transaccion.monto == Decimal("2105.26")
    assert transaccion.respuesta["conversion"]["dolar_observado"] == "950.0000"
    assert Auditoria.objects.filter(entidad="documento_cobro", origen="web").exists()


def test_se_envia_clave_de_idempotencia(escenario, documento):
    """Los reintentos no deben poder generar un cobro duplicado."""
    paypal = PayPalFalso()
    _iniciar_y_volver(escenario, documento, paypal)

    cabeceras = [kw.get("headers", {}) for url, kw in paypal.llamadas
                 if "/v2/checkout/orders" in url]
    assert cabeceras
    assert all("PayPal-Request-Id" in c for c in cabeceras)


def test_credenciales_no_quedan_en_el_log(escenario, documento):
    _iniciar_y_volver(escenario, documento, PayPalFalso())
    for log in LogIntegracion.objects.filter(servicio="paypal"):
        assert "secreto-prueba" not in log.endpoint
        assert "TOKEN-PRUEBA" not in log.endpoint
    assert LogIntegracion.objects.filter(servicio="paypal", exitoso=True).count() == 3


def test_monto_capturado_distinto_no_marca_pagado(escenario, documento):
    """Excepcion E7 de CU-PAG-02: nunca se concilia un monto distinto."""
    paypal = PayPalFalso(monto_capturado="10.00")
    _iniciar_y_volver(escenario, documento, paypal)

    documento.refresh_from_db()
    transaccion = TransaccionPago.objects.get()
    assert documento.estado == DocumentoCobro.Estado.PENDIENTE
    assert transaccion.estado == TransaccionPago.Estado.PENDIENTE_CONCILIACION


def test_pago_rechazado_deja_documento_pendiente(escenario, documento):
    paypal = PayPalFalso(captura_codigo=422)
    _iniciar_y_volver(escenario, documento, paypal)

    documento.refresh_from_db()
    assert documento.estado == DocumentoCobro.Estado.PENDIENTE
    transaccion = TransaccionPago.objects.get()
    assert transaccion.estado == TransaccionPago.Estado.RECHAZADA
    assert transaccion.respuesta["captura"]["motivo"] == "INSTRUMENT_DECLINED"


def test_sin_respuesta_al_capturar_queda_pendiente_de_conciliacion(escenario, documento):
    paypal = PayPalFalso(captura_error=ConnectTimeout("sin conexion"))
    _iniciar_y_volver(escenario, documento, paypal)

    transaccion = TransaccionPago.objects.get()
    assert transaccion.estado == TransaccionPago.Estado.PENDIENTE_CONCILIACION

    # La conciliacion posterior consulta PayPal y cierra el pago
    with patch("requests.get", side_effect=paypal.get):
        resultado = cobros.conciliar_pendiente(transaccion)
    documento.refresh_from_db()
    assert "conciliada" in resultado
    assert documento.estado == DocumentoCobro.Estado.PAGADO


def test_retorno_repetido_no_cobra_dos_veces(escenario, documento):
    paypal = PayPalFalso()
    _iniciar_y_volver(escenario, documento, paypal)
    capturas = sum(1 for url, _ in paypal.llamadas if url.endswith("/capture"))

    with patch("requests.post", side_effect=paypal.post):
        escenario["client"].get(reverse("web:pago_retorno"), {"token": "ORDEN-PP-1"})
    capturas_despues = sum(1 for url, _ in paypal.llamadas if url.endswith("/capture"))
    assert capturas_despues == capturas


def test_cancelar_en_paypal_deja_documento_pendiente(escenario, documento):
    paypal = PayPalFalso()
    with patch("requests.post", side_effect=paypal.post):
        escenario["client"].post(reverse("web:pagar_documento", args=[documento.pk]))
    escenario["client"].get(reverse("web:pago_cancelado"), {"token": "ORDEN-PP-1"})

    documento.refresh_from_db()
    assert documento.estado == DocumentoCobro.Estado.PENDIENTE
    assert TransaccionPago.objects.get().estado == TransaccionPago.Estado.CANCELADA


# ---------------------------------------------------------------------------
# Degradacion controlada y reglas de acceso
# ---------------------------------------------------------------------------
def test_pasarela_caida_no_modifica_el_documento(escenario, documento):
    """RF-INT-03: el fallo se informa al cliente, no rompe el proceso."""
    with patch("requests.post", side_effect=ConnectTimeout("sin conexion")), \
         patch("time.sleep"):
        respuesta = escenario["client"].post(
            reverse("web:pagar_documento", args=[documento.pk]), follow=True
        )

    assert respuesta.status_code == 200
    assert "no esta disponible" in respuesta.content.decode()
    assert TransaccionPago.objects.count() == 0
    documento.refresh_from_db()
    assert documento.estado == DocumentoCobro.Estado.PENDIENTE


def test_pago_deshabilitado_desde_escritorio(escenario, documento):
    """El interruptor del panel Canal web bloquea el pago en linea."""
    ParametroSistema.objects.create(
        clave="web.pago_en_linea_habilitado", valor="false", tipo_dato="booleano",
        ambito="canal_web", usuario=escenario["usuario"],
    )
    paypal = PayPalFalso()
    with patch("requests.post", side_effect=paypal.post):
        escenario["client"].post(reverse("web:pagar_documento", args=[documento.pk]))

    assert paypal.llamadas == []
    assert TransaccionPago.objects.count() == 0


def test_documento_vencido_no_se_puede_pagar(escenario, documento):
    documento.vence_el = datetime.date(2020, 1, 1)
    documento.save()
    with pytest.raises(cobros.ErrorCobro):
        cobros.validar_pagable(documento)


def test_cliente_no_ve_cobros_ajenos(escenario, documento, client):
    """RN-16: aislamiento entre clientes."""
    client.force_login(escenario["ajeno"])
    respuesta = client.get(reverse("web:documento_cobro", args=[documento.pk]))
    assert respuesta.status_code == 404


def test_detalle_muestra_monto_en_dolares(escenario, documento):
    respuesta = escenario["client"].get(reverse("web:documento_cobro", args=[documento.pk]))
    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "105,26" in contenido  # US$ 2105,26 con el separador de miles del locale
    assert "Pagar con PayPal" in contenido


def test_mis_pedidos_lista_el_cobro(escenario, documento):
    respuesta = escenario["client"].get(reverse("web:mis_pedidos"))
    assert documento.numero in respuesta.content.decode()


def test_pago_aprobado_envia_comprobante(escenario, documento,
                                          django_capture_on_commit_callbacks):
    from django.core import mail

    with django_capture_on_commit_callbacks(execute=True):
        _iniciar_y_volver(escenario, documento, PayPalFalso())

    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert documento.numero in correo.subject
    assert correo.to == ["c@c.cl"]            # cuenta web del cliente
    assert "ORDEN-PP-1" in correo.body
    assert correo.alternatives[0][1] == "text/html"


def test_pago_rechazado_no_envia_comprobante(escenario, documento,
                                              django_capture_on_commit_callbacks):
    from django.core import mail

    with django_capture_on_commit_callbacks(execute=True):
        _iniciar_y_volver(escenario, documento, PayPalFalso(captura_codigo=422))
    assert mail.outbox == []
