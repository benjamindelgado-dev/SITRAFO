"""
Modelos abstractos compartidos por todos los dominios.

No generan tablas propias: se heredan. Concentran aqui el comportamiento
transversal para no repetirlo en las 54 tablas del modelo.
"""
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Registra cuando se creo y cuando se modifico por ultima vez."""

    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="creado en")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="modificado en")

    class Meta:
        abstract = True


class ActivableModel(models.Model):
    """
    Entidad que no se elimina fisicamente.

    Da cumplimiento a RN-13: los registros se desactivan, nunca se borran.
    """

    activo = models.BooleanField(default=True, verbose_name="activo")

    class Meta:
        abstract = True


class VigenciaModel(models.Model):
    """
    Registro versionado por periodo de vigencia.

    Da cumplimiento a RN-17: precios y tarifas no se sobrescriben, se
    versionan. Un registro con vigente_hasta nulo es el vigente actual.
    """

    vigente_desde = models.DateField(verbose_name="vigente desde")
    vigente_hasta = models.DateField(
        null=True, blank=True, verbose_name="vigente hasta"
    )

    class Meta:
        abstract = True

    @property
    def esta_vigente(self) -> bool:
        from django.utils import timezone

        hoy = timezone.localdate()
        if self.vigente_desde > hoy:
            return False
        return self.vigente_hasta is None or self.vigente_hasta >= hoy


class HistorialEstadoModel(TimeStampedModel):
    """
    Base de las tablas de historial de estados.

    Da cumplimiento a RN-14. Se usa una tabla de historial por tipo de
    documento (y no una unica tabla generica) para que la clave foranea
    sea verificada por el motor de base de datos.
    """

    estado_anterior = models.ForeignKey(
        "comercial.EstadoDocumento",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="estado anterior",
    )
    estado_nuevo = models.ForeignKey(
        "comercial.EstadoDocumento",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="estado nuevo",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="responsable",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="fecha y hora")
    observacion = models.CharField(
        max_length=300, blank=True, verbose_name="observacion"
    )

    class Meta:
        abstract = True
        ordering = ["-fecha_hora"]
