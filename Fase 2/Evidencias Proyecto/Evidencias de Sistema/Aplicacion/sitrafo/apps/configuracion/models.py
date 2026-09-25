"""
Dominio 9 — Configuracion, canal web e integraciones.

Tablas: parametro_sistema, aviso_sitio, feriado, log_integracion.

Cubre RF-ADM-01 a RF-ADM-07 y RF-INT-01 a RF-INT-03. Es el dominio que
materializa la administracion del canal web desde la aplicacion de escritorio.
"""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ParametroSistema(models.Model):
    """
    Parametro configurable del sistema y del canal web.

    Concentra los valores que en los casos de uso aparecen como configurables:
    modo mantencion, habilitacion del pago en linea, vigencia de cotizaciones,
    umbral de descuento, porcentaje de anticipo, maximo de horas diarias y
    umbral de desviacion de costo.

    Toda modificacion genera ademas un registro en auditoria (RF-ADM-07).
    """

    class TipoDato(models.TextChoices):
        BOOLEANO = "booleano", "Booleano"
        NUMERICO = "numerico", "Numerico"
        TEXTO = "texto", "Texto"
        FECHA = "fecha", "Fecha"

    class Ambito(models.TextChoices):
        SISTEMA = "sistema", "Sistema"
        CANAL_WEB = "canal_web", "Canal web"
        COMERCIAL = "comercial", "Proceso comercial"
        PRODUCCION = "produccion", "Proceso productivo"

    id_parametro_sistema = models.AutoField(primary_key=True)
    clave = models.CharField(max_length=60, unique=True, verbose_name="clave")
    valor = models.CharField(max_length=300, verbose_name="valor actual")
    tipo_dato = models.CharField(
        max_length=20, choices=TipoDato.choices, verbose_name="tipo de dato"
    )
    ambito = models.CharField(
        max_length=30, choices=Ambito.choices, verbose_name="ambito"
    )
    descripcion = models.CharField(
        max_length=200, blank=True, verbose_name="descripcion funcional"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        db_column="id_usuario", verbose_name="modificado por",
    )
    modificado_en = models.DateTimeField(
        auto_now=True, verbose_name="modificado en"
    )

    class Meta:
        db_table = "parametro_sistema"
        verbose_name = "parametro del sistema"
        verbose_name_plural = "parametros del sistema"
        ordering = ["ambito", "clave"]

    def __str__(self) -> str:
        return f"{self.clave} = {self.valor}"

    # -- Lectura tipada -----------------------------------------------------
    @property
    def valor_tipado(self):
        if self.tipo_dato == self.TipoDato.BOOLEANO:
            return self.valor.strip().lower() in ("true", "1", "si", "activo")
        if self.tipo_dato == self.TipoDato.NUMERICO:
            from decimal import Decimal

            return Decimal(self.valor)
        return self.valor

    @classmethod
    def obtener(cls, clave: str, por_defecto=None):
        """
        Lee un parametro. Si no existe en base, cae al valor de settings.

        Esto permite que el sistema funcione antes de sembrar los parametros
        y que el escritorio los modifique en caliente sin redesplegar.
        """
        parametro = cls.objects.filter(clave=clave).first()
        if parametro:
            return parametro.valor_tipado
        return por_defecto


class AvisoSitio(models.Model):
    """Mensaje publicado en la web, administrado desde escritorio (RF-ADM-05)."""

    class Tipo(models.TextChoices):
        INFORMATIVO = "informativo", "Informativo"
        ADVERTENCIA = "advertencia", "Advertencia"
        MANTENCION = "mantencion", "Mantencion"

    id_aviso = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=120, verbose_name="titulo")
    cuerpo = models.TextField(verbose_name="contenido")
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, default=Tipo.INFORMATIVO,
        verbose_name="tipo",
    )
    vigente_desde = models.DateTimeField(verbose_name="publicar desde")
    vigente_hasta = models.DateTimeField(
        null=True, blank=True, verbose_name="publicar hasta"
    )
    activo = models.BooleanField(default=True, verbose_name="activo")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        db_column="id_usuario", verbose_name="creado por",
    )

    class Meta:
        db_table = "aviso_sitio"
        verbose_name = "aviso del sitio"
        verbose_name_plural = "avisos del sitio"
        ordering = ["-vigente_desde"]

    def __str__(self) -> str:
        return self.titulo

    @property
    def esta_publicado(self) -> bool:
        ahora = timezone.now()
        if not self.activo or self.vigente_desde > ahora:
            return False
        return self.vigente_hasta is None or self.vigente_hasta >= ahora

    @classmethod
    def vigentes(cls):
        ahora = timezone.now()
        return cls.objects.filter(
            activo=True, vigente_desde__lte=ahora
        ).filter(models.Q(vigente_hasta__isnull=True) | models.Q(vigente_hasta__gte=ahora))


class Feriado(models.Model):
    """
    Feriado legal obtenido del servicio externo (RN-08).

    El almacenamiento local permite calcular plazos aun cuando el servicio
    no responda, conforme a la excepcion especificada en CU-COM-03.
    """

    class Tipo(models.TextChoices):
        CIVIL = "civil", "Civil"
        RELIGIOSO = "religioso", "Religioso"
        REGIONAL = "regional", "Regional"

    id_feriado = models.AutoField(primary_key=True)
    fecha = models.DateField(unique=True, verbose_name="fecha")
    nombre = models.CharField(max_length=120, verbose_name="denominacion oficial")
    tipo = models.CharField(
        max_length=30, choices=Tipo.choices, default=Tipo.CIVIL, verbose_name="tipo"
    )
    obtenido_en = models.DateTimeField(
        auto_now_add=True, verbose_name="obtenido en"
    )

    class Meta:
        db_table = "feriado"
        verbose_name = "feriado"
        verbose_name_plural = "feriados"
        ordering = ["fecha"]

    def __str__(self) -> str:
        return f"{self.fecha}: {self.nombre}"

    @classmethod
    def sumar_dias_habiles(cls, fecha_inicio, dias: int):
        """
        Calcula la fecha resultante de sumar dias habiles (RF-COM-08).

        Excluye sabados, domingos y los feriados almacenados.
        """
        feriados = set(cls.objects.values_list("fecha", flat=True))
        fecha = fecha_inicio
        restantes = dias
        while restantes > 0:
            fecha += timedelta(days=1)
            if fecha.weekday() >= 5 or fecha in feriados:
                continue
            restantes -= 1
        return fecha

    @classmethod
    def es_habil(cls, fecha) -> bool:
        if fecha.weekday() >= 5:
            return False
        return not cls.objects.filter(fecha=fecha).exists()


class LogIntegracion(models.Model):
    """Registro de llamadas a servicios externos (RF-INT-01)."""

    id_log = models.BigAutoField(primary_key=True)
    servicio = models.CharField(max_length=40, verbose_name="servicio invocado")
    endpoint = models.CharField(max_length=255, verbose_name="recurso")
    metodo = models.CharField(max_length=10, verbose_name="metodo HTTP")
    codigo_respuesta = models.SmallIntegerField(verbose_name="codigo de estado")
    latencia_ms = models.IntegerField(verbose_name="latencia (ms)")
    exitoso = models.BooleanField(verbose_name="exitoso")
    mensaje_error = models.CharField(
        max_length=500, blank=True, verbose_name="detalle del error"
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="fecha y hora"
    )

    class Meta:
        db_table = "log_integracion"
        verbose_name = "llamada a servicio externo"
        verbose_name_plural = "log de integraciones"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["servicio", "-fecha_hora"], name="idx_log_servicio"),
        ]

    def __str__(self) -> str:
        marca = "OK" if self.exitoso else "ERROR"
        return f"{self.servicio} {self.codigo_respuesta} {marca} ({self.latencia_ms} ms)"
