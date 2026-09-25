"""
Vistas de la aplicacion web orientada al cliente.

Todas las consultas se restringen al cliente de la cuenta autenticada
(RN-16). El filtro se aplica aqui, en la capa de vista y servicio, y nunca
en la plantilla.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from apps.catalogo.models import ModeloProducto
from apps.comercial.models import (
    Cotizacion,
    CotizacionHistorial,
    EstadoDocumento,
    OrdenCompra,
    SolicitudEspecificacion,
    SolicitudHistorial,
    SolicitudPresupuesto,
)
from apps.configuracion.models import AvisoSitio, ParametroSistema
from apps.pagos.models import DocumentoCobro, TransaccionPago
from apps.pagos.services import cobros
from apps.produccion.models import OrdenTrabajo

from .forms import LoginForm, RegistroClienteForm, SolicitudPresupuestoForm


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _cliente_de(request):
    """Cliente asociado a la cuenta autenticada."""
    return request.user.cliente


def _contexto_base(request):
    return {
        "avisos": AvisoSitio.vigentes(),
        "pago_habilitado": ParametroSistema.obtener(
            "web.pago_en_linea_habilitado", True
        ),
    }


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
class LoginClienteView(LoginView):
    template_name = "web/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(_contexto_base(self.request))
        contexto["autorregistro"] = ParametroSistema.obtener(
            "web.autorregistro_habilitado", True
        )
        return contexto


class LogoutClienteView(LogoutView):
    next_page = reverse_lazy("web:login")


class RegistroView(FormView):
    """Autorregistro de cliente (RF-CLI-06)."""

    template_name = "web/registro.html"
    form_class = RegistroClienteForm
    success_url = reverse_lazy("web:inicio")

    def dispatch(self, request, *args, **kwargs):
        if not ParametroSistema.obtener("web.autorregistro_habilitado", True):
            messages.warning(
                request,
                "El registro en linea se encuentra deshabilitado. "
                "Contacte al area comercial.",
            )
            return redirect("web:login")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        usuario = form.guardar()
        login(self.request, usuario)
        messages.success(
            self.request,
            f"Cuenta creada correctamente. Bienvenido, {usuario.username}.",
        )
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
@login_required
def inicio(request):
    cliente = _cliente_de(request)
    contexto = _contexto_base(request)

    if cliente is None:
        contexto["sin_cliente"] = True
        return render(request, "web/inicio.html", contexto)

    contexto.update(
        {
            "cliente": cliente,
            "solicitudes_abiertas": SolicitudPresupuesto.objects.filter(
                cliente=cliente, estado__es_final=False
            ).count(),
            "cotizaciones_por_responder": Cotizacion.objects.filter(
                cliente=cliente, estado__codigo="emitida"
            ).count(),
            "ordenes_activas": OrdenCompra.objects.filter(
                cliente=cliente, estado__es_final=False
            ).count(),
            "en_fabricacion": OrdenTrabajo.objects.filter(
                orden_compra__cliente=cliente, estado__es_final=False
            ).count(),
            "terminados": OrdenTrabajo.objects.filter(
                orden_compra__cliente=cliente, estado__es_final=True
            ).count(),
            "ultimas_cotizaciones": Cotizacion.objects.filter(cliente=cliente)
            .select_related("estado")
            .order_by("-creado_en")[:5],
        }
    )
    return render(request, "web/inicio.html", contexto)


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------
@login_required
def catalogo(request):
    """Solo modelos publicados desde la aplicacion de escritorio (RF-ADM-06)."""
    modelos = (
        ModeloProducto.objects.filter(publicado=True, activo=True)
        .select_related("familia")
        .prefetch_related("precios")
    )

    busqueda = request.GET.get("q", "").strip()
    if busqueda:
        modelos = modelos.filter(nombre__icontains=busqueda)

    familia = request.GET.get("familia")
    if familia:
        modelos = modelos.filter(familia_id=familia)

    from apps.catalogo.models import FamiliaProducto

    contexto = _contexto_base(request)
    contexto.update(
        {
            "modelos": modelos,
            "familias": FamiliaProducto.objects.filter(activo=True),
            "busqueda": busqueda,
            "familia_seleccionada": familia,
        }
    )
    return render(request, "web/catalogo.html", contexto)


@login_required
def ficha_modelo(request, pk):
    modelo = get_object_or_404(
        ModeloProducto.objects.select_related("familia").prefetch_related(
            "parametros_asignados__parametro", "precios"
        ),
        pk=pk,
        publicado=True,
        activo=True,
    )
    contexto = _contexto_base(request)
    contexto["modelo"] = modelo
    return render(request, "web/ficha_modelo.html", contexto)


# ---------------------------------------------------------------------------
# Solicitudes de presupuesto
# ---------------------------------------------------------------------------
@login_required
def solicitar_presupuesto(request):
    """CU-COM-01. El cliente lo asigna el sistema, nunca el formulario."""
    cliente = _cliente_de(request)
    if cliente is None:
        messages.error(request, "Su cuenta no tiene un cliente asociado.")
        return redirect("web:inicio")

    inicial = {}
    modelo_id = request.GET.get("modelo")
    if modelo_id:
        inicial["modelo"] = modelo_id

    form = SolicitudPresupuestoForm(
        request.POST or None, cliente=cliente, initial=inicial
    )

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            solicitud = form.save(commit=False)
            solicitud.cliente = cliente
            solicitud.numero = SolicitudPresupuesto.generar_numero()
            solicitud.estado = EstadoDocumento.objects.get(
                tipo_documento="solicitud", codigo="recibida"
            )
            solicitud.save()

            for parametro, valor in form.especificaciones_ingresadas():
                SolicitudEspecificacion.objects.create(
                    solicitud=solicitud, parametro=parametro, valor=valor
                )

            SolicitudHistorial.objects.create(
                solicitud=solicitud,
                estado_nuevo=solicitud.estado,
                usuario=request.user,
                observacion="Solicitud recibida desde la aplicacion web.",
            )

        messages.success(
            request,
            f"Solicitud {solicitud.numero} enviada. El area comercial la "
            "revisara y le hara llegar una cotizacion.",
        )
        return redirect("web:mis_solicitudes")

    contexto = _contexto_base(request)
    contexto["form"] = form
    return render(request, "web/solicitar.html", contexto)


@login_required
def mis_solicitudes(request):
    cliente = _cliente_de(request)
    solicitudes = (
        SolicitudPresupuesto.objects.filter(cliente=cliente)
        .select_related("estado", "modelo")
        .prefetch_related("especificaciones__parametro")
        .order_by("-creado_en")
    )
    contexto = _contexto_base(request)
    contexto["solicitudes"] = solicitudes
    return render(request, "web/mis_solicitudes.html", contexto)


# ---------------------------------------------------------------------------
# Cotizaciones
# ---------------------------------------------------------------------------
@login_required
def mis_cotizaciones(request):
    cliente = _cliente_de(request)
    cotizaciones = (
        Cotizacion.objects.filter(cliente=cliente)
        .select_related("estado")
        .prefetch_related("lineas__modelo")
        .order_by("-creado_en")
    )
    contexto = _contexto_base(request)
    contexto["cotizaciones"] = cotizaciones
    return render(request, "web/mis_cotizaciones.html", contexto)


@login_required
def detalle_cotizacion(request, pk):
    cliente = _cliente_de(request)
    cotizacion = get_object_or_404(
        Cotizacion.objects.select_related("estado", "solicitud")
        .prefetch_related("lineas__modelo", "historial__estado_nuevo"),
        pk=pk,
        cliente=cliente,
    )
    contexto = _contexto_base(request)
    contexto["cotizacion"] = cotizacion
    return render(request, "web/detalle_cotizacion.html", contexto)


def _cambiar_estado_cotizacion(cotizacion, codigo, usuario, observacion=""):
    anterior = cotizacion.estado
    cotizacion.estado = EstadoDocumento.objects.get(
        tipo_documento="cotizacion", codigo=codigo
    )
    cotizacion.save(update_fields=["estado"])
    CotizacionHistorial.objects.create(
        cotizacion=cotizacion,
        estado_anterior=anterior,
        estado_nuevo=cotizacion.estado,
        usuario=usuario,
        observacion=observacion,
    )


@login_required
def aceptar_cotizacion(request, pk):
    """
    CU-COM-08. La vigencia se verifica al confirmar y no solo al desplegar:
    una cotizacion puede vencer entre ambos momentos.
    """
    if request.method != "POST":
        return redirect("web:detalle_cotizacion", pk=pk)

    cliente = _cliente_de(request)
    cotizacion = get_object_or_404(Cotizacion, pk=pk, cliente=cliente)

    if cotizacion.estado.codigo != "emitida":
        messages.error(request, "Esta cotizacion ya no admite respuesta.")
        return redirect("web:detalle_cotizacion", pk=pk)

    if not cotizacion.esta_vigente:
        _cambiar_estado_cotizacion(
            cotizacion, "vencida", request.user,
            "Vencida al intentar aceptarla desde la web.",
        )
        messages.error(
            request,
            f"La cotizacion vencio el {cotizacion.vence_el:%d-%m-%Y}. "
            "Solicite una nueva.",
        )
        return redirect("web:detalle_cotizacion", pk=pk)

    _cambiar_estado_cotizacion(
        cotizacion, "aceptada", request.user, "Aceptada por el cliente."
    )
    messages.success(
        request,
        f"Cotizacion {cotizacion.numero} aceptada. El area comercial emitira "
        "la orden de compra.",
    )
    return redirect("web:detalle_cotizacion", pk=pk)


@login_required
def rechazar_cotizacion(request, pk):
    if request.method != "POST":
        return redirect("web:detalle_cotizacion", pk=pk)

    cliente = _cliente_de(request)
    cotizacion = get_object_or_404(Cotizacion, pk=pk, cliente=cliente)

    if cotizacion.estado.codigo != "emitida":
        messages.error(request, "Esta cotizacion ya no admite respuesta.")
        return redirect("web:detalle_cotizacion", pk=pk)

    motivo = request.POST.get("motivo", "").strip()
    if not motivo:
        messages.error(request, "Debe indicar el motivo del rechazo.")
        return redirect("web:detalle_cotizacion", pk=pk)

    _cambiar_estado_cotizacion(cotizacion, "rechazada", request.user, motivo)
    messages.info(request, f"Cotizacion {cotizacion.numero} rechazada.")
    return redirect("web:detalle_cotizacion", pk=pk)


# ---------------------------------------------------------------------------
# Pedidos y seguimiento
# ---------------------------------------------------------------------------
@login_required
def mis_pedidos(request):
    cliente = _cliente_de(request)
    ordenes = (
        OrdenCompra.objects.filter(cliente=cliente)
        .select_related("estado", "cotizacion")
        .prefetch_related("ordenes_trabajo__estado", "documentos_cobro")
        .order_by("-creado_en")
    )
    contexto = _contexto_base(request)
    contexto["ordenes"] = ordenes
    contexto["seccion"] = "pedidos"
    return render(request, "web/mis_pedidos.html", contexto)


@login_required
def seguimiento(request, pk):
    """Avance de fabricacion visible para el cliente (RF-OT-09)."""
    cliente = _cliente_de(request)
    orden_trabajo = get_object_or_404(
        OrdenTrabajo.objects.select_related("estado", "modelo", "orden_compra")
        .prefetch_related("tareas", "historial__estado_nuevo"),
        pk=pk,
        orden_compra__cliente=cliente,
    )
    contexto = _contexto_base(request)
    contexto["ot"] = orden_trabajo
    return render(request, "web/seguimiento.html", contexto)


@login_required
def perfil(request):
    cliente = _cliente_de(request)
    contexto = _contexto_base(request)
    contexto["cliente"] = cliente
    return render(request, "web/perfil.html", contexto)


# ---------------------------------------------------------------------------
# Pago en linea (CU-PAG-02)
# ---------------------------------------------------------------------------
def _documento_del_cliente(request, pk):
    """El documento solo es visible para el cliente dueno de la orden (RN-16)."""
    return get_object_or_404(
        DocumentoCobro.objects.select_related("orden_compra__estado"),
        pk=pk,
        orden_compra__cliente=_cliente_de(request),
    )


@login_required
def documento_cobro(request, pk):
    documento = _documento_del_cliente(request, pk)
    contexto = _contexto_base(request)
    contexto["seccion"] = "pedidos"
    contexto["documento"] = documento
    contexto["transacciones"] = documento.transacciones.all()

    try:
        cobros.validar_pagable(documento)
        contexto["puede_pagar"] = True
    except cobros.ErrorCobro as error:
        contexto["puede_pagar"] = False
        contexto["motivo_no_pagable"] = str(error)

    if contexto["puede_pagar"]:
        dolar = cobros.tipo_cambio_usd()
        if dolar is not None:
            contexto["dolar"] = dolar
            contexto["monto_usd"] = cobros.convertir_a_usd(documento.monto_clp, dolar.valor)
        else:
            contexto["puede_pagar"] = False
            contexto["motivo_no_pagable"] = (
                "No hay tipo de cambio disponible para calcular el cobro. Intente mas tarde."
            )

    return render(request, "web/documento_cobro.html", contexto)


@login_required
@require_POST
def pagar_documento(request, pk):
    """Crea la orden de pago en PayPal y redirige al cliente a aprobarla."""
    documento = _documento_del_cliente(request, pk)
    try:
        resultado = cobros.iniciar_pago(
            documento,
            url_retorno=request.build_absolute_uri(reverse("web:pago_retorno")),
            url_cancelacion=request.build_absolute_uri(reverse("web:pago_cancelado")),
        )
    except cobros.ErrorCobro as error:
        messages.error(request, str(error))
        return redirect("web:documento_cobro", pk=pk)

    if not resultado.exitoso:
        messages.error(request, resultado.mensaje)
        return redirect("web:documento_cobro", pk=pk)

    return redirect(resultado.url_aprobacion)


def _transaccion_de_retorno(request):
    """PayPal devuelve el identificador de su orden en el parametro token."""
    return get_object_or_404(
        TransaccionPago.objects.select_related("documento_cobro"),
        id_externo=request.GET.get("token", ""),
        documento_cobro__orden_compra__cliente=_cliente_de(request),
    )


@login_required
def pago_retorno(request):
    """El cliente aprobo el pago en PayPal: se captura y se concilia."""
    transaccion = _transaccion_de_retorno(request)
    resultado = cobros.confirmar_pago(transaccion, request.user)
    if resultado.exitoso:
        messages.success(request, resultado.mensaje)
    else:
        messages.error(request, resultado.mensaje)
    return redirect("web:documento_cobro", pk=transaccion.documento_cobro_id)


@login_required
def pago_cancelado(request):
    transaccion = _transaccion_de_retorno(request)
    cobros.cancelar_pago(transaccion)
    messages.info(request, "Pago cancelado. El documento sigue pendiente.")
    return redirect("web:documento_cobro", pk=transaccion.documento_cobro_id)
