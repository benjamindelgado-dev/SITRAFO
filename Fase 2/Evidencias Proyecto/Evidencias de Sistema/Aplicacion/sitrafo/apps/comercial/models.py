"""
Dominio 4 — Proceso comercial.

Tablas: estado_documento, solicitud_presupuesto, solicitud_especificacion,
solicitud_historial, cotizacion, cotizacion_linea, cotizacion_historial,
orden_compra, orden_compra_linea, orden_compra_historial.

Cubre RF-COM-01 a RF-COM-17.
"""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import HistorialEstadoModel, TimeStampedModel


class EstadoDocumento(models.Model):
    """
    Catalogo de estados aplicables a cada tipo de documento del flujo.

    Parametriza las maquinas de estado: agregar un estado es un registro,
    no una migracion de esquema.
    """

    class TipoDocumento(models.TextChoices):
        SOLICITUD = "solicitud", "Solicitud de presupuesto"
        COTIZACION = "cotizacion", "Cotizacion"
        ORDEN_COMPRA = "orden_compra", "Orden de compra"
        ORDEN_TRABAJO = "orden_trabajo", "Orden de trabajo"

    id_estado = models.AutoField(primary_key=True)
    tipo_documento = models.CharField(
        max_length=30, choices=TipoDocumento.choices, verbose_name="tipo de documento"
    )
    codigo = models.CharField(max_length=30, verbose_name="codigo")
    nombre = models.CharField(max_length=60, verbose_name="nombre visible")
    es_final = models.BooleanField(
        default=False, verbose_name="cierra el ciclo del documento"
    )

    class Meta:
        db_table = "estado_documento"
        verbose_name = "estado de documento"
        verbose_name_plural = "estados de documento"
        ordering = ["tipo_documento", "id_estado"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "codigo"], name="uq_estado_documento"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_documento_display()}: {self.nombre}"


class SolicitudPresupuesto(TimeStampedModel):
    """
    Requerimiento de cotizacion originado por el cliente en la web.

    Cubre RF-COM-01 y RF-COM-02.
    """

    id_solicitud = models.AutoField(primary_key=True)
    numero = models.CharField(
        max_length=20, unique=True, verbose_name="numero correlativo"
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, related_name="solicitudes",
        db_column="id_cliente", verbose_name="cliente",
    )
    modelo = models.ForeignKey(
        "catalogo.ModeloProducto", on_delete=models.PROTECT, null=True, blank=True,
        related_name="solicitudes", db_column="id_modelo",
        verbose_name="modelo base",
        help_text="Nulo si la solicitud no parte de un modelo del catalogo.",
    )
    direccion = models.ForeignKey(
        "clientes.DireccionCliente", on_delete=models.PROTECT, null=True, blank=True,
        related_name="solicitudes", db_column="id_direccion",
        verbose_name="direccion de instalacion",
    )
    cantidad = models.PositiveIntegerField(verbose_name="unidades requeridas")
    fecha_deseada = models.DateField(
        null=True, blank=True, verbose_name="fecha de entrega deseada"
    )
    estado = models.ForeignKey(
        EstadoDocumento, on_delete=models.PROTECT, related_name="solicitudes",
        db_column="id_estado", verbose_name="estado actual",
    )
    ejecutivo = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="solicitudes_asignadas", db_column="id_ejecutivo",
        verbose_name="ejecutivo asignado",
    )

    class Meta:
        db_table = "solicitud_presupuesto"
        verbose_name = "solicitud de presupuesto"
        verbose_name_plural = "solicitudes de presupuesto"
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0), name="ck_solicitud_cantidad_positiva"
            )
        ]

    def __str__(self) -> str:
        return f"Solicitud {self.numero}"

    @staticmethod
    def generar_numero() -> str:
        """Correlativo con formato SP-AAAA-NNNN."""
        anio = timezone.localdate().year
        ultima = (
            SolicitudPresupuesto.objects.filter(numero__startswith=f"SP-{anio}-")
            .order_by("-numero")
            .first()
        )
        siguiente = int(ultima.numero.split("-")[-1]) + 1 if ultima else 1
        return f"SP-{anio}-{siguiente:04d}"


class SolicitudEspecificacion(models.Model):
    """
    Valor de cada parametro tecnico declarado por el cliente (RN-02).

    Se modela como tabla y no como columnas fijas para que los parametros
    sean administrables sin migrar el esquema.
    """

    solicitud = models.ForeignKey(
        SolicitudPresupuesto, on_delete=models.CASCADE, related_name="especificaciones",
        db_column="id_solicitud", verbose_name="solicitud",
    )
    parametro = models.ForeignKey(
        "catalogo.ParametroTecnico", on_delete=models.PROTECT,
        related_name="especificaciones", db_column="id_parametro",
        verbose_name="parametro tecnico",
    )
    valor = models.CharField(max_length=60, verbose_name="valor declarado")

    class Meta:
        db_table = "solicitud_especificacion"
        verbose_name = "especificacion de la solicitud"
        verbose_name_plural = "especificaciones de la solicitud"
        constraints = [
            models.UniqueConstraint(
                fields=["solicitud", "parametro"], name="uq_solicitud_parametro"
            )
        ]

    def __str__(self) -> str:
        return f"{self.parametro}: {self.valor}"


class SolicitudHistorial(HistorialEstadoModel):
    """Historial de estados de la solicitud (RN-14)."""

    id_historial = models.BigAutoField(primary_key=True)
    solicitud = models.ForeignKey(
        SolicitudPresupuesto, on_delete=models.CASCADE, related_name="historial",
        db_column="id_solicitud", verbose_name="solicitud",
    )

    class Meta(HistorialEstadoModel.Meta):
        db_table = "solicitud_historial"
        verbose_name = "historial de la solicitud"
        verbose_name_plural = "historial de la solicitud"


class Cotizacion(TimeStampedModel):
    """
    Oferta formal al cliente, con vigencia limitada y valores congelados.

    El valor de la UF y su fecha quedan congelados en el documento (RN-03):
    una cotizacion emitida hace un mes no cambia de monto al variar la UF.
    """

    id_cotizacion = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=20, verbose_name="numero correlativo")
    version = models.PositiveSmallIntegerField(default=1, verbose_name="version")
    solicitud = models.ForeignKey(
        SolicitudPresupuesto, on_delete=models.PROTECT, related_name="cotizaciones",
        db_column="id_solicitud", verbose_name="solicitud de origen",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, related_name="cotizaciones",
        db_column="id_cliente", verbose_name="cliente",
    )
    estado = models.ForeignKey(
        EstadoDocumento, on_delete=models.PROTECT, related_name="cotizaciones",
        db_column="id_estado", verbose_name="estado actual",
    )
    ejecutivo = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="cotizaciones_emitidas", db_column="id_ejecutivo",
        verbose_name="ejecutivo responsable",
    )
    valor_uf = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="valor de la UF congelado"
    )
    fecha_valor_uf = models.DateField(verbose_name="fecha del valor de la UF")
    total_uf = models.DecimalField(
        max_digits=14, decimal_places=4, default=Decimal("0"),
        verbose_name="total en UF",
    )
    descuento_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"),
        verbose_name="descuento aplicado (%)",
    )
    plazo_dias_habiles = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="plazo de fabricacion (dias habiles)"
    )
    fecha_entrega = models.DateField(
        null=True, blank=True, verbose_name="fecha comprometida de entrega"
    )
    vence_el = models.DateField(verbose_name="vence el")

    class Meta:
        db_table = "cotizacion"
        verbose_name = "cotizacion"
        verbose_name_plural = "cotizaciones"
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["numero", "version"], name="uq_cotizacion_numero_version"
            ),
            models.CheckConstraint(
                condition=models.Q(descuento_pct__gte=0) & models.Q(descuento_pct__lte=100),
                name="ck_cotizacion_descuento_rango",
            ),
        ]

    def __str__(self) -> str:
        return f"Cotizacion {self.numero} v{self.version}"

    # -- Vigencia -----------------------------------------------------------
    @property
    def esta_vigente(self) -> bool:
        """Una cotizacion vencida no puede aceptarse (RN-04)."""
        return timezone.localdate() <= self.vence_el

    @property
    def dias_para_vencer(self) -> int:
        return (self.vence_el - timezone.localdate()).days

    @staticmethod
    def calcular_vencimiento(fecha_emision=None, dias=None):
        fecha_emision = fecha_emision or timezone.localdate()
        dias = dias or settings.SITRAFO["VIGENCIA_COTIZACION_DIAS"]
        return fecha_emision + timedelta(days=dias)

    # -- Totales ------------------------------------------------------------
    def recalcular_total(self, guardar: bool = True) -> Decimal:
        """Suma las lineas y aplica el descuento."""
        bruto = sum(
            (linea.precio_uf * linea.cantidad for linea in self.lineas.all()),
            Decimal("0"),
        )
        neto = bruto * (Decimal("1") - self.descuento_pct / Decimal("100"))
        self.total_uf = neto.quantize(Decimal("0.0001"))
        if guardar:
            self.save(update_fields=["total_uf"])
        return self.total_uf

    @property
    def total_clp(self) -> Decimal:
        """Equivalente en pesos con el valor de UF congelado en el documento."""
        return (self.total_uf * self.valor_uf).quantize(Decimal("1"))

    @property
    def requiere_aprobacion(self) -> bool:
        """El descuento sobre el umbral exige aprobacion interna (RN-05)."""
        return self.descuento_pct > settings.SITRAFO["UMBRAL_DESCUENTO_PCT"]

    def clean(self):
        if self.vence_el and self.fecha_valor_uf and self.vence_el < self.fecha_valor_uf:
            raise ValidationError(
                {"vence_el": "El vencimiento no puede ser anterior a la emision."}
            )

    @staticmethod
    def generar_numero() -> str:
        """Correlativo con formato COT-AAAA-NNNN. Se conserva entre versiones."""
        anio = timezone.localdate().year
        ultima = (
            Cotizacion.objects.filter(numero__startswith=f"COT-{anio}-")
            .order_by("-numero")
            .first()
        )
        siguiente = int(ultima.numero.split("-")[-1]) + 1 if ultima else 1
        return f"COT-{anio}-{siguiente:04d}"


class CotizacionLinea(models.Model):
    """
    Detalle de la cotizacion, con el desglose de costos.

    El desglose entre materiales y horas hombre se conserva aqui, y no solo
    el precio final, porque es el termino de comparacion contra el costo real
    de la orden de trabajo (RN-11).
    """

    id_linea = models.AutoField(primary_key=True)
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.CASCADE, related_name="lineas",
        db_column="id_cotizacion", verbose_name="cotizacion",
    )
    modelo = models.ForeignKey(
        "catalogo.ModeloProducto", on_delete=models.PROTECT, related_name="lineas_cotizadas",
        db_column="id_modelo", verbose_name="modelo cotizado",
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="unidades")
    costo_material_uf = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal("0"),
        verbose_name="costo estimado de materiales (UF)",
    )
    costo_hh_uf = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal("0"),
        verbose_name="costo estimado de horas hombre (UF)",
    )
    margen_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("25"),
        verbose_name="margen aplicado (%)",
    )
    precio_uf = models.DecimalField(
        max_digits=12, decimal_places=4, default=Decimal("0"),
        verbose_name="precio unitario (UF)",
    )

    class Meta:
        db_table = "cotizacion_linea"
        verbose_name = "linea de cotizacion"
        verbose_name_plural = "lineas de cotizacion"
        ordering = ["cotizacion", "id_linea"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0), name="ck_linea_cantidad_positiva"
            )
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.modelo}"

    @property
    def costo_estimado_uf(self) -> Decimal:
        """Costo unitario estimado: materiales mas horas hombre."""
        return self.costo_material_uf + self.costo_hh_uf

    def calcular_precio(self) -> Decimal:
        """Aplica el margen sobre el costo estimado (RF-COM-04)."""
        self.precio_uf = (
            self.costo_estimado_uf * (Decimal("1") + self.margen_pct / Decimal("100"))
        ).quantize(Decimal("0.0001"))
        return self.precio_uf


class CotizacionHistorial(HistorialEstadoModel):
    """Historial de estados de la cotizacion (RN-14)."""

    id_historial = models.BigAutoField(primary_key=True)
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.CASCADE, related_name="historial",
        db_column="id_cotizacion", verbose_name="cotizacion",
    )

    class Meta(HistorialEstadoModel.Meta):
        db_table = "cotizacion_historial"
        verbose_name = "historial de la cotizacion"
        verbose_name_plural = "historial de la cotizacion"


class OrdenCompra(TimeStampedModel):
    """
    Documento que formaliza la compra.

    Solo puede generarse desde una cotizacion aceptada (RN-06).
    """

    id_orden_compra = models.AutoField(primary_key=True)
    numero = models.CharField(
        max_length=20, unique=True, verbose_name="numero correlativo"
    )
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.PROTECT, related_name="ordenes_compra",
        db_column="id_cotizacion", verbose_name="cotizacion de origen",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, related_name="ordenes_compra",
        db_column="id_cliente", verbose_name="cliente",
    )
    estado = models.ForeignKey(
        EstadoDocumento, on_delete=models.PROTECT, related_name="ordenes_compra",
        db_column="id_estado", verbose_name="estado actual",
    )
    total_uf = models.DecimalField(
        max_digits=14, decimal_places=4, verbose_name="total en UF"
    )
    anticipo_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="anticipo acordado (%)",
    )

    class Meta:
        db_table = "orden_compra"
        verbose_name = "orden de compra"
        verbose_name_plural = "ordenes de compra"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"OC {self.numero}"

    @property
    def monto_anticipo_uf(self) -> Decimal:
        pct = self.anticipo_pct or Decimal(settings.SITRAFO["ANTICIPO_PORCENTAJE"])
        return (self.total_uf * pct / Decimal("100")).quantize(Decimal("0.0001"))

    @property
    def monto_saldo_uf(self) -> Decimal:
        return self.total_uf - self.monto_anticipo_uf

    @staticmethod
    def generar_numero() -> str:
        anio = timezone.localdate().year
        ultima = (
            OrdenCompra.objects.filter(numero__startswith=f"OC-{anio}-")
            .order_by("-numero")
            .first()
        )
        siguiente = int(ultima.numero.split("-")[-1]) + 1 if ultima else 1
        return f"OC-{anio}-{siguiente:04d}"


class OrdenCompraLinea(models.Model):
    """
    Detalle de la orden de compra.

    La referencia a la linea de cotizacion es el eslabon que permite recorrer
    la trazabilidad desde el producto fabricado hasta la especificacion
    tecnica que el cliente solicito originalmente.
    """

    id_linea_oc = models.AutoField(primary_key=True)
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE, related_name="lineas",
        db_column="id_orden_compra", verbose_name="orden de compra",
    )
    cotizacion_linea = models.ForeignKey(
        CotizacionLinea, on_delete=models.PROTECT, related_name="lineas_oc",
        db_column="id_cotizacion_linea", verbose_name="linea de cotizacion",
    )
    cantidad = models.PositiveIntegerField(verbose_name="unidades adquiridas")
    precio_uf = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="precio unitario (UF)"
    )

    class Meta:
        db_table = "orden_compra_linea"
        verbose_name = "linea de orden de compra"
        verbose_name_plural = "lineas de orden de compra"
        ordering = ["orden_compra", "id_linea_oc"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0), name="ck_linea_oc_cantidad_positiva"
            )
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.cotizacion_linea.modelo}"


class OrdenCompraHistorial(HistorialEstadoModel):
    """Historial de estados de la orden de compra (RN-14)."""

    id_historial = models.BigAutoField(primary_key=True)
    orden_compra = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE, related_name="historial",
        db_column="id_orden_compra", verbose_name="orden de compra",
    )

    class Meta(HistorialEstadoModel.Meta):
        db_table = "orden_compra_historial"
        verbose_name = "historial de la orden de compra"
        verbose_name_plural = "historial de la orden de compra"
