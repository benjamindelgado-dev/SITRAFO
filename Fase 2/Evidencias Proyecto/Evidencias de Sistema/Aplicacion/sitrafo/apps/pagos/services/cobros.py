"""
Servicios de negocio de cobro y pago en linea.

Concentra las reglas que no deben quedar repartidas entre vistas:

- RN-15: el anticipo se emite como documento de cobro derivado de la orden
  de compra, con la UF congelada al emitirlo (RN-03).
- CU-PAG-02: pago en linea del documento, con conciliacion del monto y
  manejo de la ausencia de respuesta de la pasarela.

Las vistas web y los comandos de administracion solo llaman a estas
funciones; ninguna regla de cobro vive en la plantilla ni en la vista.
"""
import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.comercial.models import OrdenCompra
from apps.configuracion.models import ParametroSistema
from apps.configuracion.services import notificaciones
from apps.configuracion.services.feriados import plazo_en_dias_habiles
from apps.configuracion.services.indicadores import ClienteIndicadores, valor_uf
from apps.pagos.models import DocumentoCobro, IndicadorEconomico, TransaccionPago
from apps.seguridad.models import Auditoria

from .paypal import ClientePayPal, extraer_captura

PASARELA = "paypal"
MONEDA_PASARELA = "USD"
DIAS_HABILES_VENCIMIENTO_ANTICIPO = 10


class ErrorCobro(Exception):
    """Regla de negocio que impide emitir o pagar un documento."""


@dataclass
class ResultadoPago:
    exitoso: bool
    mensaje: str
    url_aprobacion: str = ""
    transaccion: TransaccionPago | None = None


# ----------------------------------------------------------------------
# Emision de documentos de cobro
# ----------------------------------------------------------------------
def emitir_anticipo(orden: OrdenCompra) -> tuple[DocumentoCobro, bool]:
    """
    Emite el documento de cobro del anticipo de una orden de compra (RN-15).

    Es idempotente: si la orden ya tiene un anticipo vigente (no anulado),
    lo devuelve sin crear otro. Devuelve (documento, creado).
    """
    existente = orden.documentos_cobro.filter(
        tipo=DocumentoCobro.Tipo.ANTICIPO
    ).exclude(estado=DocumentoCobro.Estado.ANULADO).first()
    if existente:
        return existente, False

    valor, _fecha, _exacto = valor_uf()
    if valor is None:
        raise ErrorCobro(
            "No hay valor de UF disponible para congelar el cobro. "
            "Ejecute sincronizar_indicadores."
        )

    hoy = timezone.localdate()
    vence, _ = plazo_en_dias_habiles(hoy, DIAS_HABILES_VENCIMIENTO_ANTICIPO)

    documento = DocumentoCobro(
        numero=DocumentoCobro.generar_numero(),
        orden_compra=orden,
        tipo=DocumentoCobro.Tipo.ANTICIPO,
        monto_uf=orden.monto_anticipo_uf,
        valor_uf=valor,
        vence_el=vence,
    )
    documento.calcular_monto_clp()
    documento.save()
    return documento, True


# ----------------------------------------------------------------------
# Conversion de moneda
# ----------------------------------------------------------------------
def tipo_cambio_usd():
    """
    Dolar observado mas reciente conocido.

    Si no hay ninguno almacenado, intenta sincronizar con mindicador.cl.
    Devuelve el registro de IndicadorEconomico o None.
    """
    registro = IndicadorEconomico.valor_a(timezone.localdate(), "USD")
    if registro is None:
        ClienteIndicadores().sincronizar_dia()
        registro = IndicadorEconomico.valor_a(timezone.localdate(), "USD")
    return registro


def convertir_a_usd(monto_clp: Decimal, dolar: Decimal) -> Decimal:
    return (monto_clp / dolar).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ----------------------------------------------------------------------
# Pago en linea (CU-PAG-02)
# ----------------------------------------------------------------------
def pago_en_linea_habilitado() -> bool:
    """Interruptor administrado desde la aplicacion de escritorio (RF-ADM)."""
    return bool(ParametroSistema.obtener("web.pago_en_linea_habilitado", True))


def validar_pagable(documento: DocumentoCobro) -> None:
    if not pago_en_linea_habilitado():
        raise ErrorCobro("El pago en linea no esta disponible en este momento.")
    if documento.estado != DocumentoCobro.Estado.PENDIENTE:
        raise ErrorCobro("Este documento no tiene un saldo pendiente de pago.")
    if documento.esta_vencido:
        raise ErrorCobro(
            f"El documento vencio el {documento.vence_el:%d-%m-%Y}. "
            "Contacte al area comercial para reemitirlo."
        )


def iniciar_pago(documento: DocumentoCobro, url_retorno: str,
                 url_cancelacion: str, cliente_paypal: ClientePayPal | None = None
                 ) -> ResultadoPago:
    """
    Crea la orden de pago en PayPal y registra la transaccion como iniciada.

    Si PayPal no responde, no se registra transaccion y el documento queda
    igual: el cliente puede reintentar (degradacion controlada, RF-INT-03).
    """
    validar_pagable(documento)

    dolar = tipo_cambio_usd()
    if dolar is None:
        return ResultadoPago(
            False, "No hay tipo de cambio disponible para calcular el cobro. "
                   "Intente mas tarde."
        )

    monto_usd = convertir_a_usd(documento.monto_clp, dolar.valor)
    clave = str(uuid.uuid4())
    cliente_paypal = cliente_paypal or ClientePayPal()

    orden = cliente_paypal.crear_orden(
        monto=monto_usd,
        moneda=MONEDA_PASARELA,
        referencia=documento.numero,
        descripcion=f"SITRAFO {documento.get_tipo_display()} "
                    f"{documento.orden_compra.numero}",
        url_retorno=url_retorno,
        url_cancelacion=url_cancelacion,
        clave_idempotencia=clave,
    )
    if not orden.exitoso:
        return ResultadoPago(
            False, "La pasarela de pago no esta disponible en este momento. "
                   "Su documento no fue modificado; puede reintentar."
        )

    transaccion = TransaccionPago.objects.create(
        documento_cobro=documento,
        id_externo=orden.id_orden,
        pasarela=PASARELA,
        monto=monto_usd,
        moneda=MONEDA_PASARELA,
        estado=TransaccionPago.Estado.INICIADA,
        respuesta={
            "clave_idempotencia": clave,
            "orden": {"id": orden.id_orden, "estado": orden.estado},
            "conversion": {
                "monto_clp": str(documento.monto_clp),
                "dolar_observado": str(dolar.valor),
                "fecha_dolar": dolar.fecha.isoformat(),
                "monto_usd": str(monto_usd),
            },
        },
    )
    return ResultadoPago(True, "", url_aprobacion=orden.url_aprobacion,
                         transaccion=transaccion)


def _registrar_captura(transaccion: TransaccionPago, captura) -> None:
    respuesta = dict(transaccion.respuesta or {})
    respuesta["captura"] = {
        "id": captura.id_captura,
        "estado": captura.estado,
        "motivo": captura.motivo,
        "monto": {"valor": str(captura.monto) if captura.monto is not None else None,
                  "moneda": captura.moneda},
    }
    transaccion.respuesta = respuesta


@transaction.atomic
def confirmar_pago(transaccion: TransaccionPago, usuario,
                   cliente_paypal: ClientePayPal | None = None) -> ResultadoPago:
    """
    Captura el pago aprobado por el cliente y concilia el documento.

    Estados resultantes de la transaccion:
    - aprobada: PayPal cobro y el monto coincide; el documento queda pagado.
    - pendiente_conciliacion: PayPal no respondio, dejo el cobro pendiente, o
      el monto capturado no coincide. Requiere revision (conciliar_pagos).
    - rechazada: PayPal rechazo el medio de pago.
    """
    transaccion = TransaccionPago.objects.select_for_update().get(pk=transaccion.pk)
    documento = transaccion.documento_cobro

    if transaccion.estado == TransaccionPago.Estado.APROBADA:
        return ResultadoPago(True, "Este pago ya habia sido registrado.",
                             transaccion=transaccion)
    if transaccion.estado != TransaccionPago.Estado.INICIADA:
        return ResultadoPago(False, "Esta transaccion ya no admite confirmacion.",
                             transaccion=transaccion)

    captura = (cliente_paypal or ClientePayPal()).capturar_orden(transaccion.id_externo)
    _registrar_captura(transaccion, captura)
    transaccion.resuelta_en = timezone.now()

    if captura.sin_respuesta or captura.estado == "PENDING":
        transaccion.estado = TransaccionPago.Estado.PENDIENTE_CONCILIACION
        transaccion.save()
        return ResultadoPago(
            False, "No recibimos la confirmacion definitiva de la pasarela. "
                   "Su pago quedo en revision; no vuelva a pagar este documento.",
            transaccion=transaccion,
        )

    if not captura.exitoso:
        transaccion.estado = TransaccionPago.Estado.RECHAZADA
        transaccion.save()
        return ResultadoPago(
            False, "La pasarela rechazo el pago. Puede intentarlo con otro medio de pago.",
            transaccion=transaccion,
        )

    transaccion.estado = TransaccionPago.Estado.APROBADA
    transaccion.save()

    if not transaccion.conciliar():
        # Cobro realizado pero por un monto distinto: nunca se marca pagado solo
        transaccion.estado = TransaccionPago.Estado.PENDIENTE_CONCILIACION
        transaccion.save(update_fields=["estado"])
        return ResultadoPago(
            False, "El monto cobrado no coincide con el documento. "
                   "El area de finanzas revisara el pago.",
            transaccion=transaccion,
        )

    Auditoria.objects.create(
        usuario=usuario,
        entidad="documento_cobro",
        id_registro=str(documento.pk),
        accion=Auditoria.Accion.MODIFICACION,
        valor_anterior={"estado": DocumentoCobro.Estado.PENDIENTE},
        valor_nuevo={"estado": DocumentoCobro.Estado.PAGADO,
                     "transaccion": transaccion.id_externo,
                     "pasarela": PASARELA},
        origen=Auditoria.Origen.WEB,
    )
    # El comprobante sale solo cuando el pago ya quedo guardado
    transaction.on_commit(lambda: notificaciones.notificar_pago_confirmado(transaccion))
    return ResultadoPago(True, f"Pago de {documento.numero} registrado.",
                         transaccion=transaccion)


def cancelar_pago(transaccion: TransaccionPago) -> None:
    """El cliente volvio desde PayPal sin aprobar el pago."""
    if transaccion.estado == TransaccionPago.Estado.INICIADA:
        transaccion.estado = TransaccionPago.Estado.CANCELADA
        transaccion.resuelta_en = timezone.now()
        transaccion.save(update_fields=["estado", "resuelta_en"])


def conciliar_pendiente(transaccion: TransaccionPago,
                        cliente_paypal: ClientePayPal | None = None) -> str:
    """
    Revisa en PayPal una transaccion pendiente de conciliacion.

    Devuelve una descripcion del resultado. Solo marca el documento como
    pagado si PayPal confirma la captura y el monto coincide.
    """
    consulta = (cliente_paypal or ClientePayPal()).consultar_orden(transaccion.id_externo)
    if not consulta:
        return "sin respuesta de PayPal; se reintentara"

    captura = extraer_captura(consulta.datos or {})
    if captura.get("status") != "COMPLETED":
        return f"PayPal informa estado {captura.get('status') or consulta.datos.get('status')}"

    respuesta = dict(transaccion.respuesta or {})
    respuesta["captura"] = {
        "id": captura.get("id", ""),
        "estado": "COMPLETED",
        "motivo": "",
        "monto": {"valor": (captura.get("amount") or {}).get("value"),
                  "moneda": (captura.get("amount") or {}).get("currency_code", "")},
    }
    transaccion.respuesta = respuesta
    transaccion.estado = TransaccionPago.Estado.APROBADA
    transaccion.resuelta_en = timezone.now()
    transaccion.save()

    if transaccion.conciliar():
        return "conciliada: documento pagado"
    transaccion.estado = TransaccionPago.Estado.PENDIENTE_CONCILIACION
    transaccion.save(update_fields=["estado"])
    return "cobrada, pero el monto no coincide: requiere revision manual"
