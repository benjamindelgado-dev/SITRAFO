"""
Dominio 8 — Pagos y moneda.

Tablas: indicador_economico, documento_cobro, transaccion_pago.

Cubre RF-PAG-01 a RF-PAG-06. La regla central es RN-03: el valor de la UF se
congela en el documento al momento de emitirlo.
"""
from decimal import Decimal

from django.db import models
from django.utils import timezone


class IndicadorEconomico(models.Model):
    """
    Serie historica de indicadores obtenidos del servicio externo.

    El almacenamiento como serie es lo que permite operar con el ultimo valor
    conocido cuando el servicio no responde (RF-PAG-06).
    """

    class Codigo(models.TextChoices):
        UF = "UF", "Unidad de Fomento"
        UTM = "UTM", "Unidad Tributaria Mensual"
        USD = "USD", "Dolar observado"

    id_indicador = models.AutoField(primary_key=True)
    codigo = models.CharField(
        max_length=10, choices=Codigo.choices, verbose_name="indicador"
    )
    fecha = models.DateField(verbose_name="fecha del valor")
    valor = models.DecimalField(
        max_digits=14, decimal_places=4, verbose_name="valor"
    )
    obtenido_en = models.DateTimeField(
        auto_now_add=True, verbose_name="obtenido del servicio en"
    )

    class Meta:
        db_table = "indicador_economico"
        verbose_name = "indicador economico"
        verbose_name_plural = "indicadores economicos"
        ordering = ["-fecha", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo", "fecha"], name="uq_indicador_codigo_fecha"
            ),
            models.CheckConstraint(
                condition=models.Q(valor__gt=0), name="ck_indicador_positivo"
            ),
        ]
        indexes = [
            models.Index(fields=["codigo", "-fecha"], name="idx_indicador_busqueda"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} {self.fecha}: {self.valor}"

    @classmethod
    def valor_a(cls, fecha=None, codigo: str = "UF"):
        """
        Valor del indicador a una fecha.

        Si no existe el de esa fecha, devuelve el ultimo anterior conocido.
        Devuelve None solo si no hay ningun valor almacenado.
        """
        fecha = fecha or timezone.localdate()
        return (
            cls.objects.filter(codigo=codigo, fecha__lte=fecha)
            .order_by("-fecha")
            .first()
        )


class DocumentoCobro(models.Model):
    """
    Obligacion de pago derivada de una orden de compra (RN-15).

    Almacena el monto en UF y el equivalente en pesos congelado a la fecha de
    emision, para que el cobro no varie con el indicador.
    """

    class Tipo(models.TextChoices):
        ANTICIPO = "anticipo", "Anticipo"
        SALDO = "saldo", "Saldo"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PAGADO = "pagado", "Pagado"
        ANULADO = "anulado", "Anulado"

    id_documento_cobro = models.AutoField(primary_key=True)
    numero = models.CharField(
        max_length=20, unique=True, verbose_name="numero correlativo"
    )
    orden_compra = models.ForeignKey(
        "comercial.OrdenCompra", on_delete=models.PROTECT,
        related_name="documentos_cobro", db_column="id_orden_compra",
        verbose_name="orden de compra",
    )
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, verbose_name="tipo de cobro"
    )
    monto_uf = models.DecimalField(
        max_digits=14, decimal_places=4, verbose_name="monto en UF"
    )
    valor_uf = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="valor de la UF aplicado"
    )
    monto_clp = models.DecimalField(
        max_digits=16, decimal_places=2, verbose_name="monto en pesos (congelado)"
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE,
        verbose_name="estado",
    )
    vence_el = models.DateField(verbose_name="vence el")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="emitido en")

    class Meta:
        db_table = "documento_cobro"
        verbose_name = "documento de cobro"
        verbose_name_plural = "documentos de cobro"
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto_uf__gt=0), name="ck_cobro_monto_positivo"
            )
        ]

    def __str__(self) -> str:
        return f"{self.numero} ({self.get_tipo_display()})"

    @property
    def esta_vencido(self) -> bool:
        return (
            self.estado == self.Estado.PENDIENTE
            and timezone.localdate() > self.vence_el
        )

    @property
    def total_pagado_clp(self) -> Decimal:
        aprobadas = self.transacciones.filter(
            estado=TransaccionPago.Estado.APROBADA
        )
        return sum((t.monto for t in aprobadas), Decimal("0"))

    def calcular_monto_clp(self):
        """Congela el equivalente en pesos al emitir (RN-03)."""
        self.monto_clp = (self.monto_uf * self.valor_uf).quantize(Decimal("1"))
        return self.monto_clp

    @staticmethod
    def generar_numero() -> str:
        anio = timezone.localdate().year
        ultimo = (
            DocumentoCobro.objects.filter(numero__startswith=f"DC-{anio}-")
            .order_by("-numero")
            .first()
        )
        siguiente = int(ultimo.numero.split("-")[-1]) + 1 if ultimo else 1
        return f"DC-{anio}-{siguiente:04d}"


class TransaccionPago(models.Model):
    """
    Intento de pago procesado por la pasarela externa.

    Un documento puede tener varias transacciones: un intento cancelado o
    rechazado no impide uno posterior. El estado pendiente de conciliacion
    cubre la ausencia de respuesta especificada en CU-PAG-02.
    """

    class Estado(models.TextChoices):
        INICIADA = "iniciada", "Iniciada"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"
        CANCELADA = "cancelada", "Cancelada"
        PENDIENTE_CONCILIACION = "pendiente_conciliacion", "Pendiente de conciliacion"

    id_transaccion = models.AutoField(primary_key=True)
    documento_cobro = models.ForeignKey(
        DocumentoCobro, on_delete=models.PROTECT, related_name="transacciones",
        db_column="id_documento_cobro", verbose_name="documento de cobro",
    )
    id_externo = models.CharField(
        max_length=120, verbose_name="identificador de la pasarela"
    )
    pasarela = models.CharField(max_length=40, verbose_name="pasarela utilizada")
    monto = models.DecimalField(
        max_digits=16, decimal_places=2, verbose_name="monto"
    )
    moneda = models.CharField(
        max_length=3, default="CLP", verbose_name="moneda (ISO 4217)"
    )
    estado = models.CharField(
        max_length=30, choices=Estado.choices, default=Estado.INICIADA,
        verbose_name="estado",
    )
    iniciada_en = models.DateTimeField(
        auto_now_add=True, verbose_name="iniciada en"
    )
    resuelta_en = models.DateTimeField(
        null=True, blank=True, verbose_name="resuelta en"
    )
    respuesta = models.JSONField(
        null=True, blank=True, verbose_name="respuesta completa de la pasarela"
    )

    class Meta:
        db_table = "transaccion_pago"
        verbose_name = "transaccion de pago"
        verbose_name_plural = "transacciones de pago"
        ordering = ["-iniciada_en"]

    def __str__(self) -> str:
        return f"{self.id_externo} ({self.get_estado_display()})"

    @property
    def monto_capturado(self) -> Decimal | None:
        """
        Monto que la pasarela informa como efectivamente cobrado.

        Se lee de la respuesta de captura almacenada. Devuelve None si la
        transaccion aun no tiene captura registrada.
        """
        captura = (self.respuesta or {}).get("captura") or {}
        valor = (captura.get("monto") or {}).get("valor")
        if valor is None:
            return None
        try:
            return Decimal(str(valor))
        except (ArithmeticError, ValueError):
            return None

    @property
    def monto_coincide(self) -> bool:
        """
        Verificacion de conciliacion (excepcion E7 de CU-PAG-02).

        En pesos se compara contra el monto congelado del documento. En otra
        moneda (PayPal no opera en CLP, se cobra en USD) se compara el monto
        capturado por la pasarela contra el monto que SITRAFO solicito cobrar,
        que ya fue calculado desde el monto en pesos del documento.
        """
        if self.moneda == "CLP":
            return self.monto == self.documento_cobro.monto_clp
        capturado = self.monto_capturado
        return capturado is not None and capturado == self.monto

    def conciliar(self) -> bool:
        """
        Marca el documento como pagado solo si el monto coincide.

        Devuelve si la conciliacion fue exitosa.
        """
        if self.estado != self.Estado.APROBADA:
            return False
        if not self.monto_coincide:
            return False
        self.documento_cobro.estado = DocumentoCobro.Estado.PAGADO
        self.documento_cobro.save(update_fields=["estado"])
        return True
