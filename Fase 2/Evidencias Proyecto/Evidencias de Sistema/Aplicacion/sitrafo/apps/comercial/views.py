"""Vistas de la API para el dominio comercial."""
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.common.mixins import FiltradoPorClienteMixin
from apps.common.permissions import (
    CuentaOperativa,
    PermisoPorRol,
    registrar_acceso_denegado,
)
from apps.configuracion.models import ParametroSistema
from apps.configuracion.services import notificaciones
from apps.configuracion.services.indicadores import valor_uf
from apps.pagos.services.cobros import ErrorCobro, emitir_anticipo

from . import services
from .models import (
    Cotizacion,
    CotizacionHistorial,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraHistorial,
    OrdenCompraLinea,
    SolicitudPresupuesto,
)
from .serializers import (
    CotizacionSerializer,
    CotizarSolicitudSerializer,
    EstadoDocumentoSerializer,
    OrdenCompraSerializer,
    SolicitudPresupuestoSerializer,
)


class EstadoDocumentoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstadoDocumento.objects.all()
    serializer_class = EstadoDocumentoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    lectura_libre = True
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo_documento"]
    pagination_class = None


class SolicitudPresupuestoViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    """Solicitudes de presupuesto (CU-COM-01, CU-COM-02)."""

    queryset = (
        SolicitudPresupuesto.objects.select_related("cliente", "modelo", "estado")
        .prefetch_related("especificaciones__parametro", "historial")
    )
    serializer_class = SolicitudPresupuestoSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "solicitud"
    acciones_cliente = ("list", "retrieve", "create")
    permisos_accion = {
        "asignar": "solicitud.actualizar",
        "costeo": "cotizacion.crear",
        "cotizar": "cotizacion.crear",
        # La solicitud no se edita ni se borra: cambia de estado por el flujo
        "update": None, "partial_update": None, "destroy": None,
    }
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "cliente", "ejecutivo"]
    search_fields = ["numero"]
    ordering_fields = ["creado_en", "numero"]

    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        """Asigna la solicitud a un ejecutivo comercial (CU-COM-02)."""
        solicitud = self.get_object()
        estado_anterior = solicitud.estado
        solicitud.ejecutivo = request.user
        solicitud.estado = EstadoDocumento.objects.get(
            tipo_documento="solicitud", codigo="asignada"
        )
        solicitud.save(update_fields=["ejecutivo", "estado"])

        from .models import SolicitudHistorial

        SolicitudHistorial.objects.create(
            solicitud=solicitud,
            estado_anterior=estado_anterior,
            estado_nuevo=solicitud.estado,
            usuario=request.user,
            observacion=f"Asignada a {request.user.username}.",
        )
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=["get"])
    def costeo(self, request, pk=None):
        """
        Costo estimado y precio sugerido para cotizar la solicitud (RF-COM-04).

        Solo consulta: no crea nada. La aplicacion de escritorio lo usa para
        prellenar el formulario de la cotizacion.
        """
        solicitud = self.get_object()
        if solicitud.modelo is None:
            return Response({"detalle": "La solicitud no indica un modelo del catalogo."},
                            status=status.HTTP_409_CONFLICT)
        try:
            costeo = services.costear_modelo(
                solicitud.modelo, request.query_params.get("margen")
            )
        except ArithmeticError:
            return Response({"margen": "Debe ser un numero."},
                            status=status.HTTP_400_BAD_REQUEST)
        uf, fecha_uf, exacto = valor_uf()
        return Response({
            "solicitud": solicitud.numero,
            "cliente": solicitud.cliente.razon_social,
            "modelo": solicitud.modelo.nombre,
            "cantidad": solicitud.cantidad,
            "costo_material_uf": costeo.costo_material_uf,
            "costo_hh_uf": costeo.costo_hh_uf,
            "horas_estandar": costeo.horas_estandar,
            "tarifa_referencia_uf": costeo.tarifa_referencia_uf,
            "costo_estimado_uf": costeo.costo_estimado_uf,
            "margen_pct": costeo.margen_pct,
            "precio_base_uf": costeo.precio_base_uf,
            "precio_sugerido_uf": costeo.precio_sugerido_uf,
            "origen_precio": costeo.origen_precio,
            "valor_uf": uf,
            "fecha_valor_uf": fecha_uf,
            "uf_del_dia": exacto,
            "plazo_defecto_dias_habiles": services.PLAZO_DEFECTO_DIAS_HABILES,
        })

    @action(detail=True, methods=["post"])
    def cotizar(self, request, pk=None):
        """Elabora la cotizacion en borrador desde la solicitud (CU-COM-03)."""
        solicitud = self.get_object()
        entrada = CotizarSolicitudSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            cotizacion = services.cotizar_solicitud(
                solicitud, request.user, **entrada.validated_data
            )
        except services.ErrorComercial as error:
            return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(CotizacionSerializer(cotizacion).data,
                        status=status.HTTP_201_CREATED)


class CotizacionViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    """Cotizaciones. Incluye la aceptacion y el rechazo del cliente."""

    queryset = (
        Cotizacion.objects.select_related("cliente", "estado", "solicitud")
        .prefetch_related("lineas__modelo", "historial", "ordenes_compra")
    )
    serializer_class = CotizacionSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "cotizacion"
    acciones_cliente = ("list", "retrieve", "aceptar", "rechazar")
    permisos_accion = {
        "aceptar": "cotizacion.actualizar",
        "rechazar": "cotizacion.actualizar",
        "emitir": "cotizacion.actualizar",
        "solicitar_aprobacion": "cotizacion.actualizar",
        "enviar_correo": "cotizacion.actualizar",
        "devolver": "cotizacion.aprobar",
        "generar_orden_compra": "orden_compra.crear",
        # La cotizacion nace desde una solicitud (accion cotizar) y cambia
        # solo por las acciones del flujo
        "create": None, "update": None, "partial_update": None, "destroy": None,
    }
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "cliente"]
    search_fields = ["numero"]
    ordering_fields = ["creado_en", "vence_el"]

    def _cambiar_estado(self, cotizacion, codigo, usuario, observacion=""):
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
        return cotizacion

    @action(detail=True, methods=["post"])
    def aceptar(self, request, pk=None):
        """
        Aceptacion por el cliente (CU-COM-08).

        La vigencia se vuelve a verificar al confirmar, no solo al desplegar
        la vista: una cotizacion puede vencer entre ambos momentos.
        """
        cotizacion = self.get_object()

        if cotizacion.estado.codigo != "emitida":
            return Response(
                {"detalle": "Solo puede aceptarse una cotizacion emitida."},
                status=status.HTTP_409_CONFLICT,
            )

        if not cotizacion.esta_vigente:
            self._cambiar_estado(
                cotizacion, "vencida", request.user,
                "Vencida al momento de intentar aceptarla.",
            )
            return Response(
                {
                    "detalle": "La cotizacion vencio el "
                               f"{cotizacion.vence_el}. Solicite una nueva.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        self._cambiar_estado(
            cotizacion, "aceptada", request.user, "Aceptada por el cliente."
        )
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        """Rechazo por el cliente, con motivo (CU-COM-08, flujo A5)."""
        cotizacion = self.get_object()

        if cotizacion.estado.codigo != "emitida":
            return Response(
                {"detalle": "Solo puede rechazarse una cotizacion emitida."},
                status=status.HTTP_409_CONFLICT,
            )

        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return Response(
                {"motivo": "Debe indicar el motivo del rechazo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self._cambiar_estado(cotizacion, "rechazada", request.user, motivo)
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        """
        Emision al cliente (CU-COM-07).

        - Solo desde borrador o en aprobacion; si el descuento supera el umbral,
          debe haber pasado por aprobacion (RN-05).
        - Congela la UF del dia de emision y la vigencia corre desde hoy (RN-03).
        - Envia la cotizacion por correo al cliente (RF-COM-09).
        """
        cotizacion = self.get_object()

        if cotizacion.estado.codigo not in ("borrador", "en_aprobacion"):
            return Response(
                {"detalle": f"Una cotizacion {cotizacion.estado.nombre.lower()} "
                            "no puede emitirse."},
                status=status.HTTP_409_CONFLICT,
            )
        if cotizacion.requiere_aprobacion and cotizacion.estado.codigo != "en_aprobacion":
            return Response(
                {
                    "detalle": "El descuento supera el umbral autorizado: "
                               "requiere aprobacion interna antes de emitir.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Emitir una cotizacion en aprobacion es aprobarla (RN-05): exige el
        # permiso de aprobacion y que quien aprueba no sea quien la elaboro,
        # para que el control del descuento lo ejerza otra persona.
        aprobando = cotizacion.estado.codigo == "en_aprobacion"
        if aprobando:
            denegado = self._verificar_aprobador(request, cotizacion)
            if denegado:
                return denegado
        if not cotizacion.lineas.exists():
            return Response({"detalle": "La cotizacion no tiene lineas."},
                            status=status.HTTP_409_CONFLICT)

        uf, fecha_uf, _ = valor_uf()
        if uf is not None:
            cotizacion.valor_uf, cotizacion.fecha_valor_uf = uf, fecha_uf
        cotizacion.vence_el = Cotizacion.calcular_vencimiento(
            timezone.localdate(),
            int(ParametroSistema.obtener("comercial.vigencia_cotizacion_dias", 30)),
        )
        cotizacion.save(update_fields=["valor_uf", "fecha_valor_uf", "vence_el"])
        cotizacion.recalcular_total()
        self._cambiar_estado(
            cotizacion, "emitida", request.user,
            "Aprobada y emitida al cliente." if aprobando else "Emitida al cliente.",
        )
        # RF-COM-09. Si el correo falla, la emision queda registrada igual.
        enviado = notificaciones.notificar_cotizacion_emitida(cotizacion)
        datos = dict(self.get_serializer(cotizacion).data)
        datos["correo_enviado"] = enviado
        datos["aviso_correo"] = (
            "Se envio por correo al cliente." if enviado else
            "No se pudo enviar el correo: reenvielo desde el panel Cotizaciones."
        )
        return Response(datos)

    def _verificar_aprobador(self, request, cotizacion):
        """Devuelve una respuesta de rechazo, o None si el usuario puede aprobar."""
        usuario = request.user
        if not usuario.has_perm("cotizacion.aprobar"):
            registrar_acceso_denegado(request, self, "aprobar", ["cotizacion.aprobar"])
            return Response({"detail": "Su rol no autoriza aprobar cotizaciones."},
                            status=status.HTTP_403_FORBIDDEN)
        if cotizacion.ejecutivo_id == usuario.pk:
            registrar_acceso_denegado(request, self, "aprobar_propia", ["cotizacion.aprobar"])
            return Response(
                {"detalle": "No puede aprobar una cotizacion elaborada por usted. "
                            "Debe aprobarla otro ejecutivo."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @action(detail=True, methods=["post"])
    def solicitar_aprobacion(self, request, pk=None):
        """Envia a aprobacion interna un borrador con descuento sobre el umbral (RN-05)."""
        cotizacion = self.get_object()
        if cotizacion.estado.codigo != "borrador":
            return Response({"detalle": "Solo un borrador puede enviarse a aprobacion."},
                            status=status.HTTP_409_CONFLICT)
        if not cotizacion.requiere_aprobacion:
            return Response(
                {"detalle": "El descuento no supera el umbral: puede emitirse directamente."},
                status=status.HTTP_409_CONFLICT,
            )
        self._cambiar_estado(
            cotizacion, "en_aprobacion", request.user,
            f"Descuento de {cotizacion.descuento_pct}% enviado a aprobacion.",
        )
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        """El aprobador rechaza el descuento: la cotizacion vuelve a borrador."""
        cotizacion = self.get_object()
        if cotizacion.estado.codigo != "en_aprobacion":
            return Response({"detalle": "Solo una cotizacion en aprobacion puede devolverse."},
                            status=status.HTTP_409_CONFLICT)
        denegado = self._verificar_aprobador(request, cotizacion)
        if denegado:
            return denegado
        motivo = (request.data.get("motivo") or "").strip()
        if not motivo:
            return Response({"motivo": "Indique por que se devuelve la cotizacion."},
                            status=status.HTTP_400_BAD_REQUEST)
        self._cambiar_estado(cotizacion, "borrador", request.user, f"Devuelta: {motivo}")
        return Response(self.get_serializer(cotizacion).data)

    @action(detail=True, methods=["post"])
    def enviar_correo(self, request, pk=None):
        """Reenvia al cliente una cotizacion ya emitida (RF-COM-09)."""
        cotizacion = self.get_object()
        if cotizacion.estado.codigo == "borrador":
            return Response({"detalle": "Un borrador no se envia al cliente."},
                            status=status.HTTP_409_CONFLICT)
        if not notificaciones.notificar_cotizacion_emitida(cotizacion):
            return Response(
                {"detalle": "No se pudo enviar el correo. Revise el registro de "
                            "integraciones y los contactos del cliente."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"detalle": "Cotizacion enviada por correo."})

    @action(detail=True, methods=["post"])
    def generar_orden_compra(self, request, pk=None):
        """
        Genera la orden de compra desde una cotizacion aceptada (RN-06).

        Es el unico camino para crear una orden de compra.
        """
        cotizacion = self.get_object()

        if cotizacion.estado.codigo != "aceptada":
            return Response(
                {"detalle": "Solo una cotizacion aceptada origina una orden de compra."},
                status=status.HTTP_409_CONFLICT,
            )

        if cotizacion.ordenes_compra.exists():
            return Response(
                {"detalle": "Esta cotizacion ya tiene una orden de compra."},
                status=status.HTTP_409_CONFLICT,
            )

        estado_oc = EstadoDocumento.objects.get(
            tipo_documento="orden_compra", codigo="pendiente"
        )
        orden = OrdenCompra.objects.create(
            numero=OrdenCompra.generar_numero(),
            cotizacion=cotizacion,
            cliente=cotizacion.cliente,
            estado=estado_oc,
            total_uf=cotizacion.total_uf,
        )
        for linea in cotizacion.lineas.all():
            OrdenCompraLinea.objects.create(
                orden_compra=orden,
                cotizacion_linea=linea,
                cantidad=linea.cantidad,
                precio_uf=linea.precio_uf,
            )
        OrdenCompraHistorial.objects.create(
            orden_compra=orden,
            estado_nuevo=estado_oc,
            usuario=request.user,
            observacion=f"Generada desde la cotizacion {cotizacion.numero}.",
        )

        # RN-15: el anticipo nace con la orden. Si no hay UF disponible para
        # congelarlo, la orden igual se crea y el anticipo se emite despues
        # con el comando emitir_cobros (degradacion controlada, RF-INT-03).
        try:
            emitir_anticipo(orden)
        except ErrorCobro:
            pass

        return Response(
            OrdenCompraSerializer(orden).data, status=status.HTTP_201_CREATED
        )


class OrdenCompraViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    queryset = (
        OrdenCompra.objects.select_related("cliente", "estado", "cotizacion")
        .prefetch_related("lineas__cotizacion_linea__modelo", "historial",
                          "documentos_cobro", "ordenes_trabajo")
    )
    serializer_class = OrdenCompraSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "orden_compra"
    acciones_cliente = ("list", "retrieve")
    permisos_accion = {
        "confirmar": "orden_compra.actualizar",
        "generar_ordenes_trabajo": "orden_trabajo.crear",
        "registrar_entrega": "orden_compra.actualizar",
        # La orden nace solo desde una cotizacion aceptada (RN-06)
        "create": None, "update": None, "partial_update": None, "destroy": None,
    }
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "cliente"]
    search_fields = ["numero"]

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """Confirma la orden, habilitando la generacion de la OT (RN-07)."""
        orden = self.get_object()
        if orden.estado.codigo != "pendiente":
            return Response(
                {"detalle": "Solo una orden pendiente puede confirmarse."},
                status=status.HTTP_409_CONFLICT,
            )
        anterior = orden.estado
        orden.estado = EstadoDocumento.objects.get(
            tipo_documento="orden_compra", codigo="confirmada"
        )
        orden.save(update_fields=["estado"])
        OrdenCompraHistorial.objects.create(
            orden_compra=orden,
            estado_anterior=anterior,
            estado_nuevo=orden.estado,
            usuario=request.user,
            observacion="Orden confirmada.",
        )
        return Response(self.get_serializer(orden).data)

    @action(detail=True, methods=["post"])
    def generar_ordenes_trabajo(self, request, pk=None):
        """
        Genera las ordenes de trabajo de una orden confirmada (CU-OT-01, RN-07).

        La ejecuta el jefe de produccion: la orden de compra es del area
        comercial, pero la planificacion es de produccion.
        """
        from apps.produccion import services as produccion
        from apps.produccion.serializers import OrdenTrabajoSerializer

        orden = self.get_object()
        try:
            creadas = produccion.generar_ordenes_trabajo(orden, request.user)
        except produccion.ErrorProduccion as error:
            return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(OrdenTrabajoSerializer(creadas, many=True).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def registrar_entrega(self, request, pk=None):
        """
        Entrega del pedido al cliente: cierra el flujo documental.

        Exige la fabricacion terminada (todas las ordenes de trabajo cerradas,
        es decir, con calidad aprobada) y el saldo pagado (RN-15).
        """
        from apps.pagos.services.cobros import fabricacion_terminada, saldo_pagado

        orden = self.get_object()
        if orden.estado.codigo != "en_produccion":
            return Response({"detalle": f"La orden esta {orden.estado.nombre.lower()}."},
                            status=status.HTTP_409_CONFLICT)
        if not fabricacion_terminada(orden):
            return Response({"detalle": "Aun hay ordenes de trabajo sin cerrar."},
                            status=status.HTTP_409_CONFLICT)
        if not saldo_pagado(orden):
            return Response({"detalle": "El saldo aun no esta pagado."},
                            status=status.HTTP_409_CONFLICT)
        anterior = orden.estado
        orden.estado = EstadoDocumento.objects.get(tipo_documento="orden_compra",
                                                   codigo="entregada")
        orden.save(update_fields=["estado"])
        OrdenCompraHistorial.objects.create(
            orden_compra=orden, estado_anterior=anterior, estado_nuevo=orden.estado,
            usuario=request.user,
            observacion=(request.data.get("observacion") or "Pedido entregado al cliente.")[:300],
        )
        return Response(self.get_serializer(orden).data)
