"""
Dominio 5 — Ejecucion productiva.

Tablas: empleado, tarifa_hora_hombre, orden_trabajo, orden_trabajo_historial,
tarea_ot, consumo_material, registro_hora_hombre.

Es el dominio que captura el costo real: materiales consumidos y horas
hombre valorizadas, siempre imputados a una tarea (RN-09, RN-10, RN-11).

Cubre RF-OT-01 a RF-OT-11.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import ActivableModel, HistorialEstadoModel, TimeStampedModel
from apps.common.validators import limpiar_rut, validar_rut


class Empleado(ActivableModel):
    """Trabajador que ejecuta tareas productivas (RF-OT-11)."""

    id_empleado = models.AutoField(primary_key=True)
    rut = models.CharField(
        max_length=12, unique=True, validators=[validar_rut], verbose_name="RUT"
    )
    nombre = models.CharField(max_length=120, verbose_name="nombre completo")
    cargo = models.CharField(max_length=80, verbose_name="cargo")
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="empleado", db_column="id_usuario",
        verbose_name="usuario del sistema",
        help_text="Solo si el empleado registra directamente en el sistema.",
    )

    class Meta:
        db_table = "empleado"
        verbose_name = "empleado"
        verbose_name_plural = "empleados"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.cargo})"

    def save(self, *args, **kwargs):
        self.rut = limpiar_rut(self.rut)
        super().save(*args, **kwargs)

    def tarifa_vigente_a(self, fecha=None):
        """
        Tarifa aplicable a una fecha determinada (RN-10).

        Devuelve None si no hay tarifa definida para esa fecha.
        """
        fecha = fecha or timezone.localdate()
        return (
            self.tarifas.filter(vigente_desde__lte=fecha)
            .filter(models.Q(vigente_hasta__isnull=True) | models.Q(vigente_hasta__gte=fecha))
            .order_by("-vigente_desde")
            .first()
        )


class TarifaHoraHombre(models.Model):
    """
    Valor de la hora de trabajo, versionado por vigencia (RN-10, RN-17).

    Si la tarifa fuese un atributo de Empleado, un aumento de sueldo
    recalcularia el costo de todas las ordenes de trabajo ya cerradas.
    """

    id_tarifa = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="tarifas",
        db_column="id_empleado", verbose_name="empleado",
    )
    valor_hora_uf = models.DecimalField(
        max_digits=10, decimal_places=4, verbose_name="valor hora (UF)"
    )
    vigente_desde = models.DateField(verbose_name="vigente desde")
    vigente_hasta = models.DateField(
        null=True, blank=True, verbose_name="vigente hasta"
    )

    class Meta:
        db_table = "tarifa_hora_hombre"
        verbose_name = "tarifa de hora hombre"
        verbose_name_plural = "tarifas de hora hombre"
        ordering = ["empleado", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(
                fields=["empleado", "vigente_desde"], name="uq_tarifa_vigencia"
            ),
            models.CheckConstraint(
                condition=models.Q(valor_hora_uf__gt=0), name="ck_tarifa_positiva"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.empleado}: {self.valor_hora_uf} UF/h desde {self.vigente_desde}"


class OrdenTrabajo(TimeStampedModel):
    """
    Instruccion de fabricacion derivada de una orden de compra confirmada.

    Hereda el costo estimado de la cotizacion de origen, que es el termino de
    comparacion contra el costo real (RN-11).
    """

    id_orden_trabajo = models.AutoField(primary_key=True)
    numero = models.CharField(
        max_length=20, unique=True, verbose_name="numero correlativo"
    )
    orden_compra = models.ForeignKey(
        "comercial.OrdenCompra", on_delete=models.PROTECT, related_name="ordenes_trabajo",
        db_column="id_orden_compra", verbose_name="orden de compra de origen",
    )
    modelo = models.ForeignKey(
        "catalogo.ModeloProducto", on_delete=models.PROTECT, related_name="ordenes_trabajo",
        db_column="id_modelo", verbose_name="modelo a fabricar",
    )
    cantidad = models.PositiveIntegerField(verbose_name="unidades")
    estado = models.ForeignKey(
        "comercial.EstadoDocumento", on_delete=models.PROTECT,
        related_name="ordenes_trabajo", db_column="id_estado",
        verbose_name="estado actual",
    )
    costo_estimado_uf = models.DecimalField(
        max_digits=14, decimal_places=4,
        verbose_name="costo estimado heredado (UF)",
    )
    costo_real_uf = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True,
        verbose_name="costo real acumulado (UF)",
    )
    avance_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="avance (%)",
    )
    fecha_inicio = models.DateField(
        null=True, blank=True, verbose_name="inicio de fabricacion"
    )
    fecha_cierre = models.DateField(null=True, blank=True, verbose_name="cierre")

    class Meta:
        db_table = "orden_trabajo"
        verbose_name = "orden de trabajo"
        verbose_name_plural = "ordenes de trabajo"
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0), name="ck_ot_cantidad_positiva"
            )
        ]

    def __str__(self) -> str:
        return f"OT {self.numero}"

    # -- Costeo -------------------------------------------------------------
    @property
    def costo_materiales_uf(self) -> Decimal:
        total = Decimal("0")
        for tarea in self.tareas.all():
            for consumo in tarea.consumos.all():
                total += consumo.costo_total_uf
        return total

    @property
    def costo_hh_uf(self) -> Decimal:
        total = Decimal("0")
        for tarea in self.tareas.all():
            for registro in tarea.registros_hora.filter(anulado=False):
                total += registro.costo_total_uf
        return total

    def recalcular_costo_real(self, guardar: bool = True) -> Decimal:
        """Consolida materiales mas horas hombre (RN-11)."""
        self.costo_real_uf = (self.costo_materiales_uf + self.costo_hh_uf).quantize(
            Decimal("0.0001")
        )
        if guardar:
            self.save(update_fields=["costo_real_uf"])
        return self.costo_real_uf

    @property
    def desviacion_uf(self) -> Decimal:
        real = self.costo_real_uf or Decimal("0")
        return real - self.costo_estimado_uf

    @property
    def desviacion_pct(self) -> Decimal:
        if not self.costo_estimado_uf:
            return Decimal("0")
        return (self.desviacion_uf / self.costo_estimado_uf * Decimal("100")).quantize(
            Decimal("0.01")
        )

    @property
    def desviacion_requiere_justificacion(self) -> bool:
        umbral = Decimal(settings.SITRAFO["UMBRAL_DESVIACION_COSTO_PCT"])
        return abs(self.desviacion_pct) > umbral

    # -- Avance -------------------------------------------------------------
    def recalcular_avance(self, guardar: bool = True) -> Decimal:
        """
        Porcentaje de tareas terminadas sobre el total de tareas.

        El avance mide cuanto del trabajo esta hecho, no cuantas horas se
        consumieron: una tarea puede terminarse en menos horas de las
        estimadas, o requerir mas, y en ambos casos cuenta como terminada.
        La comparacion de horas reales con estimadas se refleja en el costo
        real y su desviacion (RN-11), no en el avance.
        """
        tareas = list(self.tareas.all())
        if not tareas:
            self.avance_pct = Decimal("0")
        else:
            terminadas = sum(1 for t in tareas if t.estado == TareaOT.Estado.TERMINADA)
            self.avance_pct = (
                Decimal(terminadas) / Decimal(len(tareas)) * Decimal("100")
            ).quantize(Decimal("0.01"))
        if guardar:
            self.save(update_fields=["avance_pct"])
        return self.avance_pct

    # -- Cierre -------------------------------------------------------------
    @property
    def tareas_pendientes(self):
        return self.tareas.exclude(estado=TareaOT.Estado.TERMINADA)

    def puede_cerrarse(self) -> tuple[bool, list[str]]:
        """
        Verifica las condiciones de cierre (RN-12).

        Devuelve si puede cerrarse y la lista de impedimentos.
        """
        impedimentos = []

        pendientes = self.tareas_pendientes.count()
        if pendientes:
            impedimentos.append(f"{pendientes} tarea(s) sin terminar.")

        from apps.calidad.models import NoConformidad

        # Un punto repetido cuenta una sola vez: importa que tenga resultado
        faltantes = sum(c.puntos_pendientes.count() for c in self.controles_calidad.all())
        if not self.controles_calidad.exists():
            impedimentos.append("No se ha ejecutado ningun control de calidad.")
        elif faltantes:
            impedimentos.append(f"{faltantes} punto(s) de control obligatorio(s) sin ejecutar.")

        abiertas = NoConformidad.objects.filter(
            resultado__control__orden_trabajo=self,
            estado=NoConformidad.Estado.ABIERTA,
        ).count()
        if abiertas:
            impedimentos.append(f"{abiertas} no conformidad(es) abierta(s).")

        return (not impedimentos), impedimentos

    @staticmethod
    def generar_numero() -> str:
        anio = timezone.localdate().year
        ultima = (
            OrdenTrabajo.objects.filter(numero__startswith=f"OT-{anio}-")
            .order_by("-numero")
            .first()
        )
        siguiente = int(ultima.numero.split("-")[-1]) + 1 if ultima else 1
        return f"OT-{anio}-{siguiente:04d}"


class OrdenTrabajoHistorial(HistorialEstadoModel):
    """Historial de estados de la orden de trabajo (RN-14)."""

    id_historial = models.BigAutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(
        OrdenTrabajo, on_delete=models.CASCADE, related_name="historial",
        db_column="id_orden_trabajo", verbose_name="orden de trabajo",
    )

    class Meta(HistorialEstadoModel.Meta):
        db_table = "orden_trabajo_historial"
        verbose_name = "historial de la orden de trabajo"
        verbose_name_plural = "historial de la orden de trabajo"


class TareaOT(models.Model):
    """
    Actividad productiva concreta dentro de una orden de trabajo.

    Es la unidad sobre la que se imputan materiales y horas: no existe
    consumo ni hora hombre sin tarea asociada (RN-09).
    """

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_EJECUCION = "en_ejecucion", "En ejecucion"
        TERMINADA = "terminada", "Terminada"

    id_tarea = models.AutoField(primary_key=True)
    orden_trabajo = models.ForeignKey(
        OrdenTrabajo, on_delete=models.CASCADE, related_name="tareas",
        db_column="id_orden_trabajo", verbose_name="orden de trabajo",
    )
    nombre = models.CharField(max_length=120, verbose_name="nombre de la tarea")
    secuencia = models.PositiveSmallIntegerField(verbose_name="secuencia")
    horas_estimadas = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="horas hombre estimadas"
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE,
        verbose_name="estado",
    )
    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, null=True, blank=True,
        related_name="tareas_asignadas", db_column="id_empleado",
        verbose_name="empleado asignado",
    )
    fecha_estimada = models.DateField(
        null=True, blank=True, verbose_name="fecha estimada"
    )

    class Meta:
        db_table = "tarea_ot"
        verbose_name = "tarea de la orden de trabajo"
        verbose_name_plural = "tareas de la orden de trabajo"
        ordering = ["orden_trabajo", "secuencia"]
        constraints = [
            models.UniqueConstraint(
                fields=["orden_trabajo", "secuencia"], name="uq_tarea_ot_secuencia"
            )
        ]

    def __str__(self) -> str:
        return f"{self.secuencia}. {self.nombre}"

    @property
    def horas_registradas(self) -> Decimal:
        return sum(
            (r.horas for r in self.registros_hora.filter(anulado=False)),
            Decimal("0"),
        )


class ConsumoMaterial(models.Model):
    """
    Material efectivamente utilizado en una tarea (RN-09).

    El costo unitario se congela al momento del consumo: si se consultara el
    precio vigente, el costo real de ordenes cerradas cambiaria con cada
    actualizacion de precios.
    """

    id_consumo = models.AutoField(primary_key=True)
    tarea = models.ForeignKey(
        TareaOT, on_delete=models.PROTECT, related_name="consumos",
        db_column="id_tarea", verbose_name="tarea",
    )
    material = models.ForeignKey(
        "inventario.Material", on_delete=models.PROTECT, related_name="consumos",
        db_column="id_material", verbose_name="material",
    )
    bodega = models.ForeignKey(
        "inventario.Bodega", on_delete=models.PROTECT, related_name="consumos",
        db_column="id_bodega", verbose_name="bodega de origen",
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="cantidad consumida"
    )
    costo_unitario_uf = models.DecimalField(
        max_digits=12, decimal_places=4,
        verbose_name="costo unitario congelado (UF)",
    )
    planificado = models.BooleanField(
        default=True, verbose_name="estaba previsto en la lista de materiales"
    )
    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, related_name="consumos_registrados",
        db_column="id_empleado", verbose_name="registrado por",
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="fecha del registro")

    class Meta:
        db_table = "consumo_material"
        verbose_name = "consumo de material"
        verbose_name_plural = "consumos de material"
        ordering = ["-fecha"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0), name="ck_consumo_cantidad_positiva"
            )
        ]

    def __str__(self) -> str:
        return f"{self.cantidad} de {self.material} en {self.tarea}"

    @property
    def costo_total_uf(self) -> Decimal:
        return self.cantidad * self.costo_unitario_uf


class RegistroHoraHombre(models.Model):
    """
    Horas trabajadas por un empleado sobre una tarea en una fecha (RN-10).

    La correccion se realiza por anulacion y nuevo registro, nunca por
    modificacion directa (RN-13).
    """

    id_registro = models.AutoField(primary_key=True)
    tarea = models.ForeignKey(
        TareaOT, on_delete=models.PROTECT, related_name="registros_hora",
        db_column="id_tarea", verbose_name="tarea",
    )
    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, related_name="horas_trabajadas",
        db_column="id_empleado", verbose_name="empleado",
    )
    fecha = models.DateField(verbose_name="fecha de la jornada")
    horas = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="horas trabajadas"
    )
    valor_hora_uf = models.DecimalField(
        max_digits=10, decimal_places=4,
        verbose_name="tarifa congelada (UF/hora)",
    )
    anulado = models.BooleanField(default=False, verbose_name="anulado")
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        db_column="id_usuario_registro", verbose_name="usuario que registro",
        help_text="Se distingue del empleado: el jefe puede registrar por un ausente.",
    )

    class Meta:
        db_table = "registro_hora_hombre"
        verbose_name = "registro de horas hombre"
        verbose_name_plural = "registros de horas hombre"
        ordering = ["-fecha", "-id_registro"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(horas__gt=0), name="ck_horas_positivas"
            )
        ]
        indexes = [
            models.Index(fields=["tarea", "empleado"], name="idx_hh_tarea_empleado"),
        ]

    def __str__(self) -> str:
        return f"{self.horas} h de {self.empleado} el {self.fecha}"

    @property
    def costo_total_uf(self) -> Decimal:
        return self.horas * self.valor_hora_uf

    def clean(self):
        if self.fecha and self.fecha > timezone.localdate():
            raise ValidationError({"fecha": "No se pueden registrar horas futuras."})
        maximo = settings.SITRAFO["MAX_HORAS_DIARIAS"]
        if self.horas and self.horas > maximo:
            raise ValidationError(
                {"horas": f"El maximo configurado es de {maximo} horas diarias."}
            )
