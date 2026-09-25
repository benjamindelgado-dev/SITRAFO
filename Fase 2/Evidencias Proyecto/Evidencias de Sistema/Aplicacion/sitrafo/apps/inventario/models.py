"""
Dominio 6 — Inventario (parte 1).

Tablas: categoria_material, material, proveedor, bodega, precio_material.
Cubre RF-INV-01 a RF-INV-08.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import ActivableModel, VigenciaModel
from apps.common.validators import limpiar_rut, validar_rut


class CategoriaMaterial(ActivableModel):
    """Agrupacion de materiales por tipo. Catalogo semilla."""

    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True, verbose_name="nombre")

    class Meta:
        db_table = "categoria_material"
        verbose_name = "categoria de material"
        verbose_name_plural = "categorias de material"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Material(ActivableModel):
    """
    Insumo utilizado en la fabricacion. No incluye productos terminados.

    stock_minimo es un parametro de gestion y si reside aqui. El stock actual
    NO se almacena: se obtiene por agregacion sobre movimiento_inventario,
    para evitar que el saldo y los movimientos discrepen.
    """

    class UnidadMedida(models.TextChoices):
        UNIDAD = "un", "Unidad"
        KILOGRAMO = "kg", "Kilogramo"
        METRO = "m", "Metro"
        METRO_CUADRADO = "m2", "Metro cuadrado"
        LITRO = "l", "Litro"

    id_material = models.AutoField(primary_key=True)
    categoria = models.ForeignKey(
        CategoriaMaterial, on_delete=models.PROTECT, related_name="materiales",
        db_column="id_categoria", verbose_name="categoria",
    )
    codigo = models.CharField(max_length=40, unique=True, verbose_name="codigo")
    nombre = models.CharField(max_length=150, verbose_name="nombre")
    unidad_medida = models.CharField(
        max_length=20, choices=UnidadMedida.choices, verbose_name="unidad de medida"
    )
    stock_minimo = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        verbose_name="stock minimo",
        help_text="Nivel bajo el cual se emite alerta (RF-INV-06).",
    )

    class Meta:
        db_table = "material"
        verbose_name = "material"
        verbose_name_plural = "materiales"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

    @property
    def costo_vigente(self):
        """Costo de compra vigente hoy, o None si no hay precio definido."""
        precio = self.precios.filter(vigente_hasta__isnull=True).first()
        return precio.costo_uf if precio else None


class Proveedor(ActivableModel):
    """Empresa que abastece materiales (RF-INV-02)."""

    id_proveedor = models.AutoField(primary_key=True)
    rut = models.CharField(
        max_length=12, unique=True, validators=[validar_rut], verbose_name="RUT"
    )
    razon_social = models.CharField(max_length=150, verbose_name="razon social")
    email = models.EmailField(max_length=150, blank=True, verbose_name="correo")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="telefono")

    class Meta:
        db_table = "proveedor"
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        ordering = ["razon_social"]

    def __str__(self) -> str:
        return self.razon_social

    def save(self, *args, **kwargs):
        self.rut = limpiar_rut(self.rut)
        super().save(*args, **kwargs)


class Bodega(ActivableModel):
    """Ubicacion fisica de almacenamiento (RF-INV-03)."""

    id_bodega = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, verbose_name="codigo")
    nombre = models.CharField(max_length=100, verbose_name="nombre")
    ubicacion = models.CharField(
        max_length=150, blank=True, verbose_name="ubicacion fisica"
    )

    class Meta:
        db_table = "bodega"
        verbose_name = "bodega"
        verbose_name_plural = "bodegas"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class PrecioMaterial(VigenciaModel):
    """
    Costo de compra del material, versionado por vigencia (RN-17).

    Si el precio fuese un atributo de Material, actualizarlo alteraria
    retroactivamente el costo real de todas las ordenes de trabajo cerradas.
    """

    id_precio_material = models.AutoField(primary_key=True)
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="precios",
        db_column="id_material", verbose_name="material",
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, null=True, blank=True,
        related_name="precios", db_column="id_proveedor", verbose_name="proveedor",
    )
    costo_uf = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="costo en UF"
    )

    class Meta:
        db_table = "precio_material"
        verbose_name = "precio de material"
        verbose_name_plural = "precios de material"
        ordering = ["material", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(
                fields=["material", "vigente_desde"],
                name="uq_precio_material_vigencia",
            ),
            models.CheckConstraint(
                condition=models.Q(costo_uf__gte=0), name="ck_precio_material_no_negativo"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.material} desde {self.vigente_desde}: {self.costo_uf} UF"


class MovimientoInventario(models.Model):
    """
    Registro de toda variacion de existencias (RF-INV-04, RF-INV-05).

    El stock actual se obtiene por agregacion sobre esta tabla. La referencia
    a consumo_material permite que el kardex exhiba el origen productivo de
    cada salida, y que el costo de la orden de trabajo y el saldo de
    inventario provengan del mismo hecho registrado una sola vez.
    """

    class Tipo(models.TextChoices):
        RECEPCION = "recepcion", "Recepcion"
        CONSUMO = "consumo", "Consumo productivo"
        AJUSTE = "ajuste", "Ajuste de inventario"
        DEVOLUCION = "devolucion", "Devolucion"

    id_movimiento = models.BigAutoField(primary_key=True)
    material = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="movimientos",
        db_column="id_material", verbose_name="material",
    )
    bodega = models.ForeignKey(
        Bodega, on_delete=models.PROTECT, related_name="movimientos",
        db_column="id_bodega", verbose_name="bodega",
    )
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, verbose_name="tipo de movimiento"
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=4,
        verbose_name="cantidad",
        help_text="Positiva en entradas, negativa en salidas.",
    )
    costo_unitario_uf = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="costo unitario (UF)"
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimientos", db_column="id_proveedor",
        verbose_name="proveedor",
        help_text="Solo en recepciones.",
    )
    consumo = models.OneToOneField(
        "produccion.ConsumoMaterial", on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimiento", db_column="id_consumo",
        verbose_name="consumo productivo de origen",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        db_column="id_usuario", verbose_name="responsable",
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name="fecha y hora")
    observacion = models.CharField(
        max_length=300, blank=True, verbose_name="observacion"
    )

    class Meta:
        db_table = "movimiento_inventario"
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(
                fields=["material", "bodega"], name="idx_mov_material_bodega"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.cantidad} de {self.material}"

    @staticmethod
    def stock_actual(material, bodega=None) -> Decimal:
        """Saldo calculado por agregacion. No se almacena (evita redundancia)."""
        qs = MovimientoInventario.objects.filter(material=material)
        if bodega is not None:
            qs = qs.filter(bodega=bodega)
        total = qs.aggregate(t=models.Sum("cantidad"))["t"]
        return total or Decimal("0")
