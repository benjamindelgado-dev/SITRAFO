"""
Dominio 3 — Catalogo de productos.

Tablas: familia_producto, modelo_producto, parametro_tecnico, valor_parametro,
modelo_parametro, precio_base_modelo, bom_modelo, tarea_estandar_modelo.

Cubre RF-CAT-01 a RF-CAT-09 y RF-ADM-06.
"""
from django.conf import settings
from django.db import models

from apps.common.models import ActivableModel, VigenciaModel


class FamiliaProducto(ActivableModel):
    """Agrupacion de modelos por caracteristicas comunes (RF-CAT-01)."""

    id_familia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True, verbose_name="nombre")
    descripcion = models.CharField(
        max_length=200, blank=True, verbose_name="descripcion"
    )

    class Meta:
        db_table = "familia_producto"
        verbose_name = "familia de producto"
        verbose_name_plural = "familias de producto"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class ParametroTecnico(models.Model):
    """
    Caracteristica tecnica configurable de un transformador.

    Se modela como tabla y no como columnas fijas para que agregar un
    parametro sea un registro nuevo y no una migracion de esquema (RF-CAT-03).
    """

    class TipoDato(models.TextChoices):
        NUMERICO = "numerico", "Numerico"
        TEXTO = "texto", "Texto"
        LISTA = "lista", "Lista de valores"

    id_parametro = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=40, unique=True, verbose_name="codigo")
    nombre = models.CharField(max_length=100, verbose_name="nombre visible")
    unidad = models.CharField(max_length=20, verbose_name="unidad de medida")
    tipo_dato = models.CharField(
        max_length=20, choices=TipoDato.choices, verbose_name="tipo de dato"
    )
    obligatorio = models.BooleanField(
        default=True,
        verbose_name="obligatorio por defecto",
        help_text="Obligatoriedad en el formulario web. Configurable (RF-ADM-04).",
    )

    class Meta:
        db_table = "parametro_tecnico"
        verbose_name = "parametro tecnico"
        verbose_name_plural = "parametros tecnicos"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.unidad})"


class ValorParametro(ActivableModel):
    """Valor admisible de un parametro de tipo lista."""

    id_valor = models.AutoField(primary_key=True)
    parametro = models.ForeignKey(
        ParametroTecnico, on_delete=models.CASCADE, related_name="valores",
        db_column="id_parametro", verbose_name="parametro",
    )
    valor = models.CharField(max_length=60, verbose_name="valor")
    orden = models.PositiveSmallIntegerField(
        default=0, verbose_name="orden de presentacion"
    )

    class Meta:
        db_table = "valor_parametro"
        verbose_name = "valor de parametro"
        verbose_name_plural = "valores de parametro"
        ordering = ["parametro", "orden", "valor"]
        constraints = [
            models.UniqueConstraint(
                fields=["parametro", "valor"], name="uq_valor_parametro"
            )
        ]

    def __str__(self) -> str:
        return self.valor


class ModeloProducto(ActivableModel):
    """
    Modelo base parametrizable de transformador.

    No representa existencias: representa una configuracion de fabricacion.
    El atributo publicado controla su visibilidad en el catalogo web y es
    administrado desde la aplicacion de escritorio (RF-ADM-06).
    """

    id_modelo = models.AutoField(primary_key=True)
    familia = models.ForeignKey(
        FamiliaProducto, on_delete=models.PROTECT, related_name="modelos",
        db_column="id_familia", verbose_name="familia",
    )
    codigo = models.CharField(max_length=40, unique=True, verbose_name="codigo")
    nombre = models.CharField(max_length=150, verbose_name="nombre comercial")
    descripcion = models.TextField(blank=True, verbose_name="descripcion tecnica")
    publicado = models.BooleanField(
        default=False, verbose_name="publicado en el catalogo web"
    )
    parametros = models.ManyToManyField(
        ParametroTecnico, through="ModeloParametro", related_name="modelos",
        verbose_name="parametros tecnicos",
    )

    class Meta:
        db_table = "modelo_producto"
        verbose_name = "modelo de producto"
        verbose_name_plural = "modelos de producto"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

    @property
    def precio_vigente(self):
        """Precio base vigente hoy, o None si no hay precio definido."""
        precio = self.precios.filter(vigente_hasta__isnull=True).first()
        return precio.monto_uf if precio else None

    @property
    def horas_estandar_totales(self):
        """Suma de las horas hombre estimadas de las tareas estandar."""
        from django.db.models import Sum

        total = self.tareas_estandar.aggregate(t=Sum("horas_estimadas"))["t"]
        return total or 0


class ModeloParametro(models.Model):
    """Parametro aplicable a un modelo, con su valor por defecto."""

    modelo = models.ForeignKey(
        ModeloProducto, on_delete=models.CASCADE, related_name="parametros_asignados",
        db_column="id_modelo", verbose_name="modelo",
    )
    parametro = models.ForeignKey(
        ParametroTecnico, on_delete=models.PROTECT, related_name="modelos_asignados",
        db_column="id_parametro", verbose_name="parametro",
    )
    valor_defecto = models.CharField(
        max_length=60, blank=True, verbose_name="valor por defecto"
    )
    obligatorio = models.BooleanField(
        default=True, verbose_name="obligatorio para este modelo"
    )

    class Meta:
        db_table = "modelo_parametro"
        verbose_name = "parametro del modelo"
        verbose_name_plural = "parametros del modelo"
        constraints = [
            models.UniqueConstraint(
                fields=["modelo", "parametro"], name="uq_modelo_parametro"
            )
        ]

    def __str__(self) -> str:
        return f"{self.modelo} - {self.parametro}"


class PrecioBaseModelo(VigenciaModel):
    """Precio base del modelo, versionado por vigencia (RN-17, RF-CAT-06)."""

    id_precio = models.AutoField(primary_key=True)
    modelo = models.ForeignKey(
        ModeloProducto, on_delete=models.CASCADE, related_name="precios",
        db_column="id_modelo", verbose_name="modelo",
    )
    monto_uf = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="monto en UF"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        db_column="id_usuario", verbose_name="registrado por",
    )

    class Meta:
        db_table = "precio_base_modelo"
        verbose_name = "precio base de modelo"
        verbose_name_plural = "precios base de modelo"
        ordering = ["modelo", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(
                fields=["modelo", "vigente_desde"], name="uq_precio_modelo_vigencia"
            ),
            models.CheckConstraint(
                condition=models.Q(monto_uf__gte=0), name="ck_precio_modelo_no_negativo"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.modelo} desde {self.vigente_desde}: {self.monto_uf} UF"


class BomModelo(models.Model):
    """
    Lista de materiales base del modelo (RF-CAT-04).

    Junto a TareaEstandarModelo es la fuente del calculo automatico de costo
    estimado exigido por RF-COM-04.
    """

    id_bom = models.AutoField(primary_key=True)
    modelo = models.ForeignKey(
        ModeloProducto, on_delete=models.CASCADE, related_name="materiales",
        db_column="id_modelo", verbose_name="modelo",
    )
    material = models.ForeignKey(
        "inventario.Material", on_delete=models.PROTECT, related_name="usos_en_modelos",
        db_column="id_material", verbose_name="material",
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="cantidad por unidad"
    )
    observacion = models.CharField(
        max_length=200, blank=True, verbose_name="observacion"
    )

    class Meta:
        db_table = "bom_modelo"
        verbose_name = "material del modelo"
        verbose_name_plural = "lista de materiales del modelo"
        ordering = ["modelo", "material"]
        constraints = [
            models.UniqueConstraint(
                fields=["modelo", "material"], name="uq_bom_modelo_material"
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0), name="ck_bom_cantidad_positiva"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.modelo} usa {self.cantidad} de {self.material}"


class TareaEstandarModelo(models.Model):
    """Tarea productiva estandar del modelo, con sus horas hombre (RF-CAT-05)."""

    id_tarea_estandar = models.AutoField(primary_key=True)
    modelo = models.ForeignKey(
        ModeloProducto, on_delete=models.CASCADE, related_name="tareas_estandar",
        db_column="id_modelo", verbose_name="modelo",
    )
    nombre = models.CharField(max_length=120, verbose_name="nombre de la tarea")
    secuencia = models.PositiveSmallIntegerField(verbose_name="secuencia")
    horas_estimadas = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="horas hombre estimadas"
    )

    class Meta:
        db_table = "tarea_estandar_modelo"
        verbose_name = "tarea estandar del modelo"
        verbose_name_plural = "tareas estandar del modelo"
        ordering = ["modelo", "secuencia"]
        constraints = [
            models.UniqueConstraint(
                fields=["modelo", "secuencia"], name="uq_tarea_estandar_secuencia"
            ),
            models.CheckConstraint(
                condition=models.Q(horas_estimadas__gt=0),
                name="ck_tarea_horas_positivas",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.secuencia}. {self.nombre}"
