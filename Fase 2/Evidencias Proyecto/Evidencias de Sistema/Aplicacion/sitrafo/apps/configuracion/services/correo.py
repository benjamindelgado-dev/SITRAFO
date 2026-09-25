"""
Integracion de correo transaccional con Brevo (API REST v3).

Sustenta RF-COM-09 (envio de la cotizacion al cliente) y las notificaciones
del flujo documental.

Se implementa como un backend de correo de Django: el resto del sistema
envia correos con las herramientas estandar de Django (EmailMultiAlternatives)
y no sabe que proveedor esta detras. Cambiar de proveedor, o usar la consola
en desarrollo, es solo cambiar EMAIL_BACKEND.

Como todo servicio externo, pasa por ClienteServicioExterno: cada envio
queda en log_integracion (RF-INT-01) y un fallo nunca interrumpe el proceso
de negocio que lo origino (RF-INT-03).

Nota sobre reintentos: Brevo no ofrece clave de idempotencia. Un reintento
tras un timeout podria duplicar un correo; se acepta ese riesgo porque un
correo duplicado es preferible a uno perdido, y se limita a dos intentos.
"""
import logging
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

from .base import ClienteServicioExterno, RespuestaServicio

logger = logging.getLogger(__name__)

URL_BREVO = "https://api.brevo.com/v3"


def _direccion(texto: str) -> dict:
    """'Nombre <correo@x.cl>' -> {'name': 'Nombre', 'email': 'correo@x.cl'}"""
    nombre, correo = parseaddr(texto)
    direccion = {"email": correo}
    if nombre:
        direccion["name"] = nombre
    return direccion


class ClienteBrevo(ClienteServicioExterno):
    nombre_servicio = "correo"
    tiempo_espera = 8
    max_intentos = 2

    def __init__(self, url_base: str | None = None, api_key: str | None = None):
        super().__init__(url_base or getattr(settings, "BREVO_URL", URL_BREVO))
        self.api_key = api_key if api_key is not None else settings.BREVO_API_KEY

    def enviar(self, mensaje) -> RespuestaServicio:
        """Envia un EmailMessage de Django. Devuelve el resultado, no lanza."""
        if not self.api_key:
            return RespuestaServicio(False, mensaje_error="BREVO_API_KEY no configurada.")

        cuerpo = {
            "sender": _direccion(mensaje.from_email or settings.DEFAULT_FROM_EMAIL),
            "to": [_direccion(d) for d in mensaje.to],
            "subject": mensaje.subject,
            "textContent": mensaje.body,
        }
        if mensaje.cc:
            cuerpo["cc"] = [_direccion(d) for d in mensaje.cc]
        if mensaje.bcc:
            cuerpo["bcc"] = [_direccion(d) for d in mensaje.bcc]
        if mensaje.reply_to:
            cuerpo["replyTo"] = _direccion(mensaje.reply_to[0])
        for contenido, tipo in getattr(mensaje, "alternatives", []):
            if tipo == "text/html":
                cuerpo["htmlContent"] = contenido

        return self.solicitar(
            "POST", "/smtp/email",
            json=cuerpo,
            headers={"api-key": self.api_key, "accept": "application/json",
                     "content-type": "application/json"},
        )


class BrevoEmailBackend(BaseEmailBackend):
    """Backend de correo de Django que entrega los mensajes via Brevo."""

    def send_messages(self, email_messages) -> int:
        cliente = ClienteBrevo()
        enviados = 0
        for mensaje in email_messages:
            resultado = cliente.enviar(mensaje)
            if resultado:
                enviados += 1
                continue
            logger.warning("Correo no enviado (%s): %s", mensaje.subject,
                           resultado.mensaje_error)
            if not self.fail_silently:
                raise RuntimeError(f"Brevo rechazo el envio: {resultado.mensaje_error}")
        return enviados
