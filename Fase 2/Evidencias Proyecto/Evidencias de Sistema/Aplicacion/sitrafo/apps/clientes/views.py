"""Vistas de la API para el dominio de clientes."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from apps.common.mixins import FiltradoPorClienteMixin
from apps.common.permissions import CuentaOperativa, PermisoPorRol

from .models import Cliente, Comuna, ContactoCliente, DireccionCliente, Region
from .serializers import (
    ClienteSerializer,
    ComunaSerializer,
    ContactoClienteSerializer,
    DireccionClienteSerializer,
    RegionSerializer,
)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogo territorial. Lectura para cualquier cuenta operativa."""

    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    lectura_libre = True
    pagination_class = None


class ComunaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comuna.objects.select_related("region")
    serializer_class = ComunaSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    lectura_libre = True
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["region"]
    search_fields = ["nombre"]
    # Catalogo acotado (346 comunas): sin paginar, igual que las regiones, para
    # que el escritorio reciba la lista completa en una sola llamada.
    pagination_class = None


class ClienteViewSet(viewsets.ModelViewSet):
    """
    Gestion de clientes.

    El cliente web solo accede a su propio registro; el ejecutivo comercial
    accede a todos.
    """

    serializer_class = ClienteSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "cliente"
    acciones_cliente = ("list", "retrieve")
    permisos_accion = {
        "documentos": "cliente.leer",
        "cuentas": "cuenta_web.leer",
        "suspender_cuenta": "cuenta_web.actualizar",
        "reactivar_cuenta": "cuenta_web.actualizar",
        # Un cliente con documentos no se borra: se deja inactivo
        "destroy": None,
    }
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["tipo_persona", "estado"]
    search_fields = ["rut", "razon_social", "nombre_fantasia"]

    def get_queryset(self):
        queryset = Cliente.objects.prefetch_related("contactos", "direcciones")
        usuario = self.request.user
        if usuario.is_superuser or usuario.es_interno:
            return queryset
        if usuario.cliente_id is None:
            return queryset.none()
        return queryset.filter(id_cliente=usuario.cliente_id)

    @action(detail=True, methods=["get"])
    def documentos(self, request, pk=None):
        """Historial completo de documentos del cliente (RF-CLI-07)."""
        cliente = self.get_object()

        def filas(consulta, campos):
            return [{c: getattr(d, c) for c in campos} | {"estado": d.estado.nombre}
                    for d in consulta.select_related("estado").order_by("-creado_en")]

        from apps.pagos.models import DocumentoCobro

        return Response({
            "solicitudes": filas(cliente.solicitudes.all(), ["numero", "creado_en", "cantidad"]),
            "cotizaciones": filas(cliente.cotizaciones.all(),
                                  ["numero", "creado_en", "total_uf", "vence_el"]),
            "ordenes_compra": filas(cliente.ordenes_compra.all(),
                                    ["numero", "creado_en", "total_uf"]),
            "cobros": [
                {"numero": d.numero, "tipo": d.get_tipo_display(), "estado": d.get_estado_display(),
                 "monto_uf": d.monto_uf, "monto_clp": d.monto_clp, "creado_en": d.creado_en}
                for d in DocumentoCobro.objects.filter(orden_compra__cliente=cliente)
                .order_by("-creado_en")
            ],
        })

    @action(detail=True, methods=["get"])
    def cuentas(self, request, pk=None):
        """Cuentas web del cliente con su estado (RF-ADM-03)."""
        cliente = self.get_object()
        return Response([
            {"id_usuario": u.pk, "username": u.username, "email": u.email,
             "estado": u.estado, "estado_nombre": u.get_estado_display(),
             "ultimo_acceso": u.ultimo_acceso}
            for u in cliente.cuentas.order_by("username")
        ])

    def _estado_cuenta(self, request, estado):
        from apps.seguridad.models import Auditoria

        cliente = self.get_object()
        cuenta = cliente.cuentas.filter(pk=request.data.get("cuenta")).first()
        if cuenta is None:
            return Response({"detalle": "La cuenta no pertenece a este cliente."},
                            status=status.HTTP_404_NOT_FOUND)
        anterior = cuenta.estado
        cuenta.estado = estado
        cuenta.intentos_fallidos = 0
        cuenta.save(update_fields=["estado", "intentos_fallidos"])
        Auditoria.objects.create(
            usuario=request.user, entidad="cuenta_web", id_registro=str(cuenta.pk),
            accion=Auditoria.Accion.MODIFICACION, valor_anterior={"estado": anterior},
            valor_nuevo={"estado": estado, "cliente": cliente.razon_social},
            origen=Auditoria.Origen.ESCRITORIO,
        )
        return self.cuentas(request, cliente.pk)

    @action(detail=True, methods=["post"])
    def suspender_cuenta(self, request, pk=None):
        """Una cuenta suspendida no puede ingresar ni operar en la web (RF-ADM-03)."""
        from apps.seguridad.models import Usuario

        return self._estado_cuenta(request, Usuario.Estado.SUSPENDIDO)

    @action(detail=True, methods=["post"])
    def reactivar_cuenta(self, request, pk=None):
        from apps.seguridad.models import Usuario

        return self._estado_cuenta(request, Usuario.Estado.ACTIVO)


class ContactoClienteViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    queryset = ContactoCliente.objects.select_related("cliente")
    serializer_class = ContactoClienteSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "cliente"
    acciones_cliente = ("list", "retrieve")
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "principal"]


class DireccionClienteViewSet(FiltradoPorClienteMixin, viewsets.ModelViewSet):
    queryset = DireccionCliente.objects.select_related("cliente", "comuna")
    serializer_class = DireccionClienteSerializer
    permission_classes = [CuentaOperativa, PermisoPorRol]
    modulo_permiso = "cliente"
    acciones_cliente = ("list", "retrieve")
    campo_cliente = "cliente_id"
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "tipo"]
    permisos_accion = {"geocodificar": "cliente.actualizar"}

    def perform_create(self, serializer):
        """Se guarda siempre; la geocodificacion es un complemento (RF-INT-03)."""
        from .geocodificacion import geocodificar

        direccion = serializer.save()
        geocodificar(direccion)

    @action(detail=True, methods=["post"])
    def geocodificar(self, request, pk=None):
        """Reintenta la geocodificacion de una direccion (RF-CLI-05)."""
        from .geocodificacion import geocodificar

        direccion = self.get_object()
        if not geocodificar(direccion):
            return Response({"detalle": "El servicio de geocodificacion no encontro la "
                                        "direccion o no esta disponible."},
                            status=status.HTTP_409_CONFLICT)
        return Response(DireccionClienteSerializer(direccion).data)

