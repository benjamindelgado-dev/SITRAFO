"""
Pruebas de anulacion de documentos (RF-COM-15, RN-13) y de los documentos
PDF (RF-COM-09, RF-CAT-09).
"""
from decimal import Decimal

from django.core import mail

from apps.comercial.models import Cotizacion, OrdenCompra, SolicitudPresupuesto
from apps.comercial.test_flujo import _cotizar, _url_solicitud, flujo  # noqa: F401
from apps.pagos.models import DocumentoCobro
from apps.seguridad.models import Auditoria

MOTIVO = {"motivo": "El cliente desistio de la compra"}


def _hasta_orden(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    base = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}"
    flujo["interno"].post(f"{base}/emitir/")
    flujo["externo"].post(f"{base}/aceptar/")
    return cotizacion, flujo["interno"].post(f"{base}/generar_orden_compra/").data


def test_anular_exige_motivo_y_queda_auditado(flujo):  # noqa: F811
    url = _url_solicitud(flujo, "anular")
    assert flujo["interno"].post(url, {"motivo": "no"}, format="json").status_code == 409
    respuesta = flujo["interno"].post(url, MOTIVO, format="json")

    assert respuesta.status_code == 200
    assert respuesta.data["estado_codigo"] == "desestimada"
    assert Auditoria.objects.filter(accion="anulacion", entidad="solicitud_presupuesto").exists()
    assert SolicitudPresupuesto.objects.count() == 1      # nada se borra (RN-13)


def test_solicitud_con_cotizacion_vigente_no_se_anula(flujo):  # noqa: F811
    _cotizar(flujo)
    respuesta = flujo["interno"].post(_url_solicitud(flujo, "anular"), MOTIVO, format="json")
    assert respuesta.status_code == 409


def test_anular_cotizacion_libera_la_solicitud_para_recotizar(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    url = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/anular/"
    assert flujo["interno"].post(url, MOTIVO, format="json").status_code == 200

    assert Cotizacion.objects.get().estado.codigo == "anulada"
    assert flujo["interno"].post(_url_solicitud(flujo, "cotizar"), {},
                                 format="json").status_code == 201


def test_anular_orden_anula_sus_cobros_pendientes(flujo):  # noqa: F811
    _, orden = _hasta_orden(flujo)
    url = f"/api/v1/ordenes-compra/{orden['id_orden_compra']}/anular/"
    assert flujo["interno"].post(url, MOTIVO, format="json").status_code == 200

    assert OrdenCompra.objects.get().estado.codigo == "anulada"
    assert DocumentoCobro.objects.get().estado == DocumentoCobro.Estado.ANULADO


def test_orden_con_pago_no_se_anula(flujo):  # noqa: F811
    _, orden = _hasta_orden(flujo)
    DocumentoCobro.objects.update(estado=DocumentoCobro.Estado.PAGADO)
    url = f"/api/v1/ordenes-compra/{orden['id_orden_compra']}/anular/"
    respuesta = flujo["interno"].post(url, MOTIVO, format="json")
    assert respuesta.status_code == 409
    assert "pagos" in respuesta.data["detalle"]


def test_el_cliente_no_anula(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    url = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/anular/"
    assert flujo["externo"].post(url, MOTIVO, format="json").status_code == 403


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def test_emitir_adjunta_el_pdf_de_la_cotizacion(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    flujo["interno"].post(f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/emitir/")

    nombre, contenido, tipo = mail.outbox[0].attachments[0]
    assert nombre == f"{cotizacion['numero']}.pdf" and tipo == "application/pdf"
    assert contenido.startswith(b"%PDF")


def test_cliente_descarga_su_cotizacion_pero_no_un_borrador(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    url = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/pdf/"
    assert flujo["externo"].get(url).status_code == 404          # borrador
    flujo["interno"].post(f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/emitir/")
    respuesta = flujo["externo"].get(url)
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert Decimal(cotizacion["total_uf"]) > 0
