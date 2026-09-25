"""
Dominio 7 — Control de calidad.

Tablas: protocolo_calidad, punto_control, control_calidad, resultado_control,
no_conformidad.

Cubre RF-CAL-01 a RF-CAL-05. La regla central es RN-12: una orden de trabajo
no puede cerrarse con controles obligatorios pendientes o no conformidades
abiertas.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import ActivableModel


class ProtocoloCalidad(ActivableModel):
    """Conjunto de ensayos aplicables a un modelo de producto (RF-CAL-01)."""

    id_protocolo = models.AutoField(primary_key=True)
    modelo = models.ForeignKey(
        "catalogo.ModeloProducto", on_delete=models.PROTECT, related_name="protocolos",
        db_column="id_modelo", verbose_name="modelo",
    )
    nombre = models.CharField(max_length=120, verbose_name="nombre del protocolo")
    version = models.PositiveSmallIntegerField(default=1, verbose_name="version")
    norma_referencia = models.CharField(
        max_length=80, blank=True, verbose_name="norma de referencia"
    )

    class Meta:
        db_table = "protocolo_calidad"
        verbose_name = "protocolo de calidad"
        verbose_name_plural = "protocolos de calidad"
        ordering = ["modelo", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["modelo", "nombre", "version"], name="uq_protocolo_version"
            )
        ]

    def __str__(self) -> str:
        return f"{self.nombre} v{self.version}"

    @property
    def puntos_obligatorios(self):
        return self.puntos.filter(obligatorio=True)


class PuntoControl(models.Model):
    """Ensayo individual con su criterio de aceptacion (RF-CAL-02)."""

    id_punto = models.AutoField(primary_key=True)
    protocolo = models.ForeignKey(
        ProtocoloCalidad, on_delete=models.CASCADE, related_name="puntos",
        db_column="id_protocolo", verbose_name="protocolo",
    )
    nombre = models.CharField(max_length=120, verbose_name="nombre del ensayo")
    tipo_ensayo = models.CharField(max_length=60, verbose_name="tipo de ensayo")
    unidad = models.CharField(max_length=20, verbose_name="unidad de medida")
    valor_esperado = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True,
        verbose_name="valor nominal esperado",
    )
    tolerancia_inf = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True,
        verbose_name="limite inferior admisible",
    )
    tolerancia_sup = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True,
        verbose_name="limite superior admisible",
    )
    obligatorio = models.BooleanField(
        default=True,
        verbose_name="obligatorio",
        help_text="Si es obligatorio, condiciona el cierre de la orden (RN-12).",
    )
    secuencia = models.PositiveSmallIntegerField(verbose_name="secuencia")

    class Meta:
        db_table = "punto_control"
        verbose_name = "punto de control"
        verbose_name_plural = "puntos de control"
        ordering = ["protocolo", "secuencia"]
        constraints = [
            models.UniqueConstraint(
                fields=["protocolo", "secuencia"], name="uq_punto_control_secuencia"
            )
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.unidad})"

    def evaluar(self, valor_medido: Decimal) -> bool:
        """Compara el valor medido contra el rango de tolerancia."""
        if self.tolerancia_inf is not None and valor_medido < self.tolerancia_inf:
            return False
        if self.tolerancia_sup is not None and valor_medido > self.tolerancia_sup:
            return False
        return True


class ControlCalidad(models.Model):
    """Ejecucion de un protocolo sobre una orden de trabajo (RF-CAL-03)."""

    class Estado(models.TextChoices):
        EN_PROCESO = "en_proceso", "En proceso"
        CONFORME = "conforme", "Conforme"
        CON_NO_CONFORMIDADES = "con_nc", "Con no conformidades"

    id_control = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(
        "produccion.OrdenTrabajo", on_delete=models.PROTECT,
        related_name="controles_calidad", db_column="id_orden_trabajo",
        verbose_name="orden de trabajo",
    )
    protocolo = models.ForeignKey(
        ProtocoloCalidad, on_delete=models.PROTECT, related_name="controles",
        db_column="id_protocolo", verbose_name="protocolo aplicado",
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="controles_ejecutados", db_column="id_inspector",
        verbose_name="inspector responsable",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="fecha y hora")
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.EN_PROCESO,
        verbose_name="estado",
    )
    observacion = models.CharField(
        max_length=300, blank=True, verbose_name="observacion general"
    )

    class Meta:
        db_table = "control_calidad"
        verbose_name = "control de calidad"
        verbose_name_plural = "controles de calidad"
        ordering = ["-fecha_hora"]

    def __str__(self) -> str:
        return f"Control de {self.orden_trabajo} - {self.protocolo}"

    def actualizar_estado(self, guardar: bool = True):
        """Conforme solo si todos los resultados registrados lo son."""
        resultados = self.resultados.all()
        if not resultados.exists():
            self.estado = self.Estado.EN_PROCESO
        elif resultados.filter(conforme=False).exists():
            self.estado = self.Estado.CON_NO_CONFORMIDADES
        else:
            self.estado = self.Estado.CONFORME
        if guardar:
            self.save(update_fields=["estado"])
        return self.estado

    @property
    def puntos_pendientes(self):
        """Puntos obligatorios del protocolo que aun no tienen resultado."""
        ejecutados = self.resultados.values_list("punto_id", flat=True)
        return self.protocolo.puntos_obligatorios.exclude(id_punto__in=ejecutados)


class ResultadoControl(models.Model):
    """
    Valor medido en un punto de control.

    La repeticion de un ensayo genera un registro nuevo sin eliminar el
    anterior, de modo que el informe exhiba la secuencia completa.
    """

    id_resultado = models.AutoField(primary_key=True)
    control = models.ForeignKey(
        ControlCalidad, on_delete=models.CASCADE, related_name="resultados",
        db_column="id_control", verbose_name="control",
    )
    punto = models.ForeignKey(
        PuntoControl, on_delete=models.PROTECT, related_name="resultados",
        db_column="id_punto", verbose_name="punto de control",
    )
    valor_medido = models.DecimalField(
        max_digits=14, decimal_places=4, verbose_name="valor medido"
    )
    conforme = models.BooleanField(verbose_name="conforme")
    observacion = models.CharField(
        max_length=300, blank=True, verbose_name="observacion"
    )
    registrado_en = models.DateTimeField(
        auto_now_add=True, verbose_name="registrado en"
    )

    class Meta:
        db_table = "resultado_control"
        verbose_name = "resultado de control"
        verbose_name_plural = "resultados de control"
        ordering = ["control", "punto", "-registrado_en"]

    def __str__(self) -> str:
        marca = "conforme" if self.conforme else "NO CONFORME"
        return f"{self.punto}: {self.valor_medido} ({marca})"

    def save(self, *args, **kwargs):
        """La conformidad se determina automaticamente contra la tolerancia."""
        if self.punto_id and self.valor_medido is not None:
            self.conforme = self.punto.evaluar(self.valor_medido)
        super().save(*args, **kwargs)


class NoConformidad(models.Model):
    """
    Desviacion detectada en un punto de control (RF-CAL-04).

    Mientras exista una no conformidad abierta, la orden de trabajo no puede
    cerrarse (RN-12).
    """

    class Severidad(models.TextChoices):
        MENOR = "menor", "Menor"
        MAYOR = "mayor", "Mayor"
        CRITICA = "critica", "Critica"

    class Estado(models.TextChoices):
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    id_no_conformidad = models.AutoField(primary_key=True)
    resultado = models.OneToOneField(
        ResultadoControl, on_delete=models.PROTECT, related_name="no_conformidad",
        db_column="id_resultado", verbose_name="resultado que la origino",
    )
    descripcion = models.CharField(max_length=300, verbose_name="descripcion")
    severidad = models.CharField(
        max_length=20, choices=Severidad.choices, verbose_name="severidad"
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="no_conformidades_asignadas", db_column="id_responsable",
        verbose_name="responsable de la accion correctiva",
    )
    accion_correctiva = models.TextField(
        blank=True, verbose_name="accion correctiva"
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ABIERTA,
        verbose_name="estado",
    )
    abierta_en = models.DateTimeField(auto_now_add=True, verbose_name="abierta en")
    cerrada_en = models.DateTimeField(
        null=True, blank=True, verbose_name="cerrada en"
    )
    usuario_cierre = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", db_column="id_usuario_cierre",
        verbose_name="usuario que cerro",
    )

    class Meta:
        db_table = "no_conformidad"
        verbose_name = "no conformidad"
        verbose_name_plural = "no conformidades"
        ordering = ["-abierta_en"]

    def __str__(self) -> str:
        return f"NC {self.id_no_conformidad} ({self.get_severidad_display()})"

    def cerrar(self, usuario, accion_correctiva: str = ""):
        from django.utils import timezone

        if accion_correctiva:
            self.accion_correctiva = accion_correctiva
        self.estado = self.Estado.CERRADA
        self.cerrada_en = timezone.now()
        self.usuario_cierre = usuario
        self.save(
            update_fields=["estado", "cerrada_en", "usuario_cierre", "accion_correctiva"]
        )
