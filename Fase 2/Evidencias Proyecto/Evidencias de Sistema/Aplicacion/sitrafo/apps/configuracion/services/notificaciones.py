"""
Notificaciones por correo del flujo documental.

Define que correo se envia en cada evento y a quien. El envio en si lo hace
el backend configurado en EMAIL_BACKEND (Brevo en ejecucion, consola en
desarrollo sin clave, memoria en pruebas).

Reglas:
- Una notificacion nunca interrumpe el proceso que la origina: si el correo
  falla, la solicitud, la cotizacion o el pago quedan registrados igual
  (RF-INT-03). El fallo queda en log_integracion.
- Destinatarios: el contacto principal del cliente; si no tiene, los demas
  contactos con correo; si tampoco, las cuentas web del cliente.
- CORREO_REDIRIGIR_A (solo desarrollo y demostracion): si esta definido,
  todos los correos se desvian a esa direccion, indicando en el asunto a
  quien iban dirigidos. Evita escribir a clientes ficticios de los datos de
  demostracion.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def destinatarios_de(cliente) -> list[str]:
    contactos = cliente.contactos.exclude(email="").order_by("-principal")
    principal = [c.email for c in contactos if c.principal]
    if principal:
        return principal
    correos = [c.email for c in contactos]
    if correos:
        return correos
    return list(
        cliente.cuentas.filter(is_active=True).exclude(email="")
        .values_list("email", flat=True)
    )


def url_sitio(nombre_ruta: str, *args) -> str:
    base = getattr(settings, "SITIO_URL", "http://localhost:8000").rstrip("/")
    return f"{base}{reverse(nombre_ruta, args=args)}"


def enviar(plantilla: str, asunto: str, destinatarios: list[str], contexto: dict) -> bool:
    """
    Renderiza templates/correo/<plantilla>.txt y .html y envia el correo.

    Devuelve si el backend acepto el envio. Nunca lanza excepciones.
    """
    if not destinatarios:
        logger.warning("Correo '%s' sin destinatarios; no se envia.", asunto)
        return False

    redirigir = getattr(settings, "CORREO_REDIRIGIR_A", "")
    if redirigir:
        asunto = f"{asunto} [para: {', '.join(destinatarios)}]"
        destinatarios = [redirigir]

    contexto = {**contexto, "sitio_url": getattr(settings, "SITIO_URL", "")}
    try:
        texto = render_to_string(f"correo/{plantilla}.txt", contexto)
        html = render_to_string(f"correo/{plantilla}.html", contexto)
        mensaje = EmailMultiAlternatives(
            subject=asunto, body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL, to=destinatarios,
        )
        mensaje.attach_alternative(html, "text/html")
        return mensaje.send(fail_silently=True) == 1
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo preparar el correo '%s'", asunto)
        return False


# ----------------------------------------------------------------------
# Eventos del flujo
# ----------------------------------------------------------------------
def notificar_solicitud_recibida(solicitud) -> bool:
    """Acuse de recibo de la solicitud de presupuesto (CU-COM-01)."""
    return enviar(
        "solicitud_recibida",
        f"SITRAFO: recibimos su solicitud {solicitud.numero}",
        destinatarios_de(solicitud.cliente),
        {"solicitud": solicitud, "url": url_sitio("web:mis_solicitudes")},
    )


def notificar_cotizacion_emitida(cotizacion) -> bool:
    """Envio de la cotizacion al cliente (RF-COM-09, CU-COM-07)."""
    return enviar(
        "cotizacion_emitida",
        f"SITRAFO: cotizacion {cotizacion.numero} disponible",
        destinatarios_de(cotizacion.cliente),
        {"cotizacion": cotizacion,
         "url": url_sitio("web:detalle_cotizacion", cotizacion.pk)},
    )


def notificar_pago_confirmado(transaccion) -> bool:
    """Comprobante de pago en linea (CU-PAG-02)."""
    documento = transaccion.documento_cobro
    return enviar(
        "pago_confirmado",
        f"SITRAFO: pago recibido de {documento.numero}",
        destinatarios_de(documento.orden_compra.cliente),
        {"transaccion": transaccion, "documento": documento,
         "url": url_sitio("web:documento_cobro", documento.pk)},
    )


def notificar_saldo_emitido(documento) -> bool:
    """Aviso de pedido terminado con el saldo por pagar (RN-15)."""
    return enviar(
        "saldo_emitido",
        f"SITRAFO: su pedido {documento.orden_compra.numero} esta listo",
        destinatarios_de(documento.orden_compra.cliente),
        {"documento": documento, "url": url_sitio("web:documento_cobro", documento.pk)},
    )
