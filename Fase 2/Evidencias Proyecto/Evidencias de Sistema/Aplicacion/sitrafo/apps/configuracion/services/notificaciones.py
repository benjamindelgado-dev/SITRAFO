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
- Avisos internos: cuando el trabajo pasa de un rol a otro, se avisa por
  correo a los usuarios internos activos cuyo rol tiene el permiso de la
  accion que sigue (por ejemplo, ensayo.actualizar para calidad). Se buscan
  por permiso y no por nombre de rol porque la matriz es configurable.
- CORREO_REDIRIGIR_A (solo desarrollo): si esta definido, todos los correos
  se desvian a esa direccion, indicando en el asunto a quien iban dirigidos.
- CORREO_COPIA_A (marcha blanca): si esta definido, cada correo sale a su
  destinatario real y ademas con copia oculta a esa direccion, para revisar
  que se envien bien. No se copian los correos con enlaces personales, como
  la recuperacion de clave. Si ambas variables estan definidas, manda la
  redireccion.
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


def _casilla(correo: str) -> str:
    """Casilla real de una direccion: ana+calidad@x.cl y ana@x.cl son la misma."""
    local, _, dominio = correo.strip().lower().partition("@")
    return f"{local.split('+')[0]}@{dominio}"


def usuarios_con_permiso(codigo: str, excluir=()) -> list[str]:
    """
    Correos de los usuarios internos activos cuyo rol otorga el permiso.

    El superusuario sin rol no se incluye: los avisos van a quien opera el
    proceso, no a quien administra el sistema.
    """
    from apps.seguridad.models import Usuario

    consulta = (
        Usuario.objects.filter(
            is_active=True, estado=Usuario.Estado.ACTIVO, es_interno=True,
            roles__activo=True, roles__permisos_asignados__permiso__codigo=codigo,
        )
        .exclude(email="")
        .exclude(pk__in=[u.pk for u in excluir if u is not None])
    )
    return sorted(set(consulta.values_list("email", flat=True)))


def correo_de(usuario) -> list[str]:
    if usuario is None or not usuario.email or not usuario.is_active:
        return []
    return [usuario.email]


def url_sitio(nombre_ruta: str, *args) -> str:
    base = getattr(settings, "SITIO_URL", "http://localhost:8000").rstrip("/")
    return f"{base}{reverse(nombre_ruta, args=args)}"


def enviar(plantilla: str, asunto: str, destinatarios: list[str], contexto: dict,
           adjuntos: list[tuple[str, bytes, str]] | None = None,
           copia: bool = True) -> bool:
    """
    Renderiza templates/correo/<plantilla>.txt y .html y envia el correo.

    copia=False excluye el correo de la copia de control (CORREO_COPIA_A).
    Devuelve si el backend acepto el envio. Nunca lanza excepciones.
    """
    destinatarios = list(dict.fromkeys(d.strip() for d in destinatarios if d and d.strip()))
    if not destinatarios:
        logger.warning("Correo '%s' sin destinatarios; no se envia.", asunto)
        return False

    ocultos = []
    redirigir = getattr(settings, "CORREO_REDIRIGIR_A", "")
    copia_a = getattr(settings, "CORREO_COPIA_A", "")
    if redirigir:
        asunto = f"{asunto} [para: {', '.join(destinatarios)}]"
        destinatarios = [redirigir]
    elif copia and copia_a and _casilla(copia_a) not in {_casilla(d) for d in destinatarios}:
        ocultos = [copia_a]

    contexto = {**contexto, "sitio_url": getattr(settings, "SITIO_URL", "")}
    try:
        texto = render_to_string(f"correo/{plantilla}.txt", contexto)
        html = render_to_string(f"correo/{plantilla}.html", contexto)
        mensaje = EmailMultiAlternatives(
            subject=asunto, body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL, to=destinatarios, bcc=ocultos,
        )
        mensaje.attach_alternative(html, "text/html")
        for nombre, contenido, tipo in adjuntos or []:
            mensaje.attach(nombre, contenido, tipo)
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
    """Envio de la cotizacion al cliente, con el PDF adjunto (RF-COM-09)."""
    from apps.comercial.pdf import cotizacion_pdf

    try:
        adjuntos = [(f"{cotizacion.numero}.pdf", cotizacion_pdf(cotizacion),
                     "application/pdf")]
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo generar el PDF de %s", cotizacion.numero)
        adjuntos = []   # el correo sale igual, con el enlace al portal
    return enviar(
        "cotizacion_emitida",
        f"SITRAFO: cotizacion {cotizacion.numero} disponible",
        destinatarios_de(cotizacion.cliente),
        {"cotizacion": cotizacion,
         "url": url_sitio("web:detalle_cotizacion", cotizacion.pk)},
        adjuntos=adjuntos,
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


def notificar_estado_pedido(orden, titulo: str, mensaje: str) -> bool:
    """Hitos del pedido: confirmado, en fabricacion y entregado (RF-COM-17)."""
    return enviar(
        "pedido_estado",
        f"SITRAFO: {titulo} ({orden.numero})",
        destinatarios_de(orden.cliente),
        {"orden": orden, "titulo": titulo, "mensaje": mensaje,
         "url": url_sitio("web:mis_pedidos")},
    )


# ----------------------------------------------------------------------
# Avisos internos: el trabajo pasa de un rol a otro
# ----------------------------------------------------------------------
def avisar(destinatarios: list[str], asunto: str, titulo: str, mensaje: str,
           donde: str, detalle: list[tuple[str, str]] | None = None) -> bool:
    """Aviso a usuarios internos, con donde atenderlo en el escritorio."""
    return enviar(
        "aviso_interno", f"SITRAFO: {asunto}", destinatarios,
        {"titulo": titulo, "mensaje": mensaje, "donde": donde,
         "detalle": detalle or []},
    )


def _modelo(objeto) -> str:
    modelo = getattr(objeto, "modelo", None)
    return f"{modelo.codigo} - {modelo.nombre}" if modelo else "Sin modelo de catalogo"


def avisar_solicitud_nueva(solicitud) -> bool:
    """1. Un cliente envia una solicitud: la toma un ejecutivo comercial."""
    return avisar(
        usuarios_con_permiso("solicitud.actualizar"),
        f"nueva solicitud {solicitud.numero}",
        "Llego una nueva solicitud de presupuesto",
        f"{solicitud.cliente.razon_social} envio la solicitud {solicitud.numero} "
        "desde el portal web. Asignela y prepare la cotizacion.",
        "Solicitudes",
        [("Modelo", _modelo(solicitud)), ("Unidades", str(solicitud.cantidad)),
         ("Fecha deseada", solicitud.fecha_deseada.strftime("%d-%m-%Y")
          if solicitud.fecha_deseada else "Sin fecha")],
    )


def avisar_cotizacion_en_aprobacion(cotizacion) -> bool:
    """2. Descuento sobre el umbral: la aprueba otro ejecutivo (RN-05)."""
    return avisar(
        usuarios_con_permiso("cotizacion.aprobar", excluir=[cotizacion.ejecutivo]),
        f"cotizacion {cotizacion.numero} espera su aprobacion",
        "Una cotizacion espera su aprobacion",
        f"{cotizacion.ejecutivo} envio a aprobacion la cotizacion {cotizacion.numero} "
        f"de {cotizacion.cliente.razon_social} porque su descuento supera el umbral. "
        "Revisela y apruebela (Emitir) o devuelvala con un motivo.",
        "Cotizaciones",
        [("Descuento", f"{cotizacion.descuento_pct.normalize():f}%"),
         ("Total", f"{cotizacion.total_uf:.2f} UF")],
    )


def avisar_cotizacion_resuelta(cotizacion, aprobador, aprobada: bool,
                               motivo: str = "") -> bool:
    """3. El aprobador resolvio: se avisa al ejecutivo que la elaboro."""
    if aprobada:
        titulo = "Su cotizacion fue aprobada y emitida"
        mensaje = (f"{aprobador} aprobo la cotizacion {cotizacion.numero} y se "
                   f"envio a {cotizacion.cliente.razon_social}.")
    else:
        titulo = "Su cotizacion fue devuelta"
        mensaje = (f"{aprobador} devolvio la cotizacion {cotizacion.numero} a "
                   f"borrador. Motivo: {motivo}. Corrijala y envie de nuevo.")
    return avisar(
        correo_de(cotizacion.ejecutivo),
        f"cotizacion {cotizacion.numero} {'aprobada' if aprobada else 'devuelta'}",
        titulo, mensaje, "Cotizaciones",
    )


def avisar_orden_para_produccion(orden, ordenes_trabajo, error: str = "") -> bool:
    """4. Se pago el anticipo: la orden pasa a produccion."""
    if ordenes_trabajo:
        mensaje = (f"{orden.cliente.razon_social} pago el anticipo de la orden de "
                   f"compra {orden.numero} y se generaron "
                   f"{len(ordenes_trabajo)} orden(es) de trabajo. Planifiquelas e "
                   "inicie la fabricacion.")
        detalle = [(ot.numero, f"{ot.cantidad} x {_modelo(ot)}") for ot in ordenes_trabajo]
    else:
        mensaje = (f"{orden.cliente.razon_social} pago el anticipo de la orden de "
                   f"compra {orden.numero}, pero las ordenes de trabajo no se "
                   f"pudieron generar solas: {error} Generelas desde Ordenes de compra.")
        detalle = []
    return avisar(
        usuarios_con_permiso("orden_trabajo.actualizar"),
        f"orden de compra {orden.numero} lista para produccion",
        "Una orden de compra paso a produccion", mensaje, "Ordenes de trabajo", detalle,
    )


def avisar_ot_en_calidad(ot) -> bool:
    """5. Fabricacion terminada: la OT espera los ensayos de calidad."""
    return avisar(
        usuarios_con_permiso("ensayo.actualizar"),
        f"orden de trabajo {ot.numero} espera control de calidad",
        "Una orden de trabajo espera control de calidad",
        f"La orden de trabajo {ot.numero} termino su fabricacion. Inicie el control, "
        "registre los ensayos y apruebelo para liberarla.",
        "Control de calidad",
        [("Modelo", _modelo(ot)), ("Unidades", str(ot.cantidad)),
         ("Orden de compra", ot.orden_compra.numero)],
    )


def avisar_no_conformidad(nc) -> bool:
    """6. Ensayo fuera de rango: produccion debe corregir."""
    ot = nc.resultado.control.orden_trabajo
    return avisar(
        usuarios_con_permiso("orden_trabajo.actualizar"),
        f"no conformidad en la orden {ot.numero}",
        "Calidad registro una no conformidad",
        f"Un ensayo de la orden de trabajo {ot.numero} quedo fuera de rango. "
        "Coordine la correccion; calidad cerrara la no conformidad con la accion "
        "correctiva y repetira el ensayo.",
        "No conformidades",
        [("Severidad", nc.get_severidad_display()), ("Detalle", nc.descripcion)],
    )


def avisar_ot_liberada(ot) -> bool:
    """7. Calidad aprobo: produccion puede cerrar la OT."""
    return avisar(
        usuarios_con_permiso("orden_trabajo.actualizar"),
        f"orden de trabajo {ot.numero} liberada por calidad",
        "Una orden de trabajo quedo liberada por calidad",
        f"Calidad aprobo el control de la orden de trabajo {ot.numero}. "
        "Ya puede cerrarla.",
        "Ordenes de trabajo",
        [("Modelo", _modelo(ot)), ("Orden de compra", ot.orden_compra.numero)],
    )


def avisar_saldo_pagado(documento) -> bool:
    """8. El cliente pago el saldo: comercial coordina y registra la entrega."""
    orden = documento.orden_compra
    ejecutivo = getattr(orden.cotizacion, "ejecutivo", None)
    destinatarios = correo_de(ejecutivo) or usuarios_con_permiso("orden_compra.actualizar")
    return avisar(
        destinatarios,
        f"saldo pagado de la orden {orden.numero}",
        "El cliente pago el saldo: coordine la entrega",
        f"{orden.cliente.razon_social} pago el saldo ({documento.numero}) de la orden "
        f"de compra {orden.numero}. Coordine el despacho y registre la entrega.",
        "Ordenes de compra",
    )
