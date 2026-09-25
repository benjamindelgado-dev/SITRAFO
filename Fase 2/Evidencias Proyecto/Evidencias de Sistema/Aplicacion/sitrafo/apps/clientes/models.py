"""
Dominio 2 — Clientes.

Tablas: region, comuna, cliente, contacto_cliente, direccion_cliente.
Cubre RF-CLI-01 a RF-CLI-07.
"""
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.validators import limpiar_rut, validar_rut


class Region(models.Model):
    """Division administrativa mayor. Tabla de catalogo semilla."""

    id_region = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True, verbose_name="nombre")
    codigo = models.CharField(max_length=10, verbose_name="codigo oficial")

    class Meta:
        db_table = "region"
        verbose_name = "region"
        verbose_name_plural = "regiones"
        ordering = ["id_region"]

    def __str__(self) -> str:
        return self.nombre


class Comuna(models.Model):
    """
    Division administrativa menor.

    Se separa de region para evitar la dependencia transitiva que se
    produciria si el nombre de la region fuese atributo de la direccion (3FN).
    """

    id_comuna = models.AutoField(primary_key=True)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="comunas",
        db_column="id_region", verbose_name="region",
    )
    nombre = models.CharField(max_length=80, verbose_name="nombre")

    class Meta:
        db_table = "comuna"
        verbose_name = "comuna"
        verbose_name_plural = "comunas"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["region", "nombre"], name="uq_comuna_region_nombre"
            )
        ]

    def __str__(self) -> str:
        return self.nombre


class Cliente(TimeStampedModel):
    """Persona natural o juridica que solicita cotizaciones (RF-CLI-01)."""

    class TipoPersona(models.TextChoices):
        NATURAL = "natural", "Persona natural"
        JURIDICA = "juridica", "Persona juridica"

    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"

    id_cliente = models.AutoField(primary_key=True)
    rut = models.CharField(
        max_length=12, unique=True, validators=[validar_rut], verbose_name="RUT"
    )
    razon_social = models.CharField(max_length=150, verbose_name="razon social")
    nombre_fantasia = models.CharField(
        max_length=150, blank=True, verbose_name="nombre de fantasia"
    )
    tipo_persona = models.CharField(
        max_length=10, choices=TipoPersona.choices, verbose_name="tipo de persona"
    )
    giro = models.CharField(max_length=150, blank=True, verbose_name="giro")
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ACTIVO,
        verbose_name="estado",
    )

    class Meta:
        db_table = "cliente"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["razon_social"]

    def __str__(self) -> str:
        return f"{self.razon_social} ({self.rut})"

    def save(self, *args, **kwargs):
        """Normaliza el RUT antes de guardar, para que la unicidad funcione."""
        self.rut = limpiar_rut(self.rut)
        super().save(*args, **kwargs)


class ContactoCliente(models.Model):
    """Persona de contacto asociada a un cliente (RF-CLI-03)."""

    id_contacto = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="contactos",
        db_column="id_cliente", verbose_name="cliente",
    )
    nombre = models.CharField(max_length=120, verbose_name="nombre")
    cargo = models.CharField(max_length=80, blank=True, verbose_name="cargo")
    email = models.EmailField(max_length=150, blank=True, verbose_name="correo")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="telefono")
    principal = models.BooleanField(
        default=False, verbose_name="es contacto principal"
    )

    class Meta:
        db_table = "contacto_cliente"
        verbose_name = "contacto de cliente"
        verbose_name_plural = "contactos de cliente"
        ordering = ["-principal", "nombre"]

    def __str__(self) -> str:
        return self.nombre


class DireccionCliente(models.Model):
    """
    Direccion del cliente, tipificada segun su uso (RF-CLI-04).

    El atributo validada permite registrar la direccion aun cuando el servicio
    de geocodificacion no responda, conforme al flujo alternativo de CU-COM-01.
    """

    class Tipo(models.TextChoices):
        FACTURACION = "facturacion", "Facturacion"
        DESPACHO = "despacho", "Despacho"
        INSTALACION = "instalacion", "Instalacion"

    id_direccion = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="direcciones",
        db_column="id_cliente", verbose_name="cliente",
    )
    comuna = models.ForeignKey(
        Comuna, on_delete=models.PROTECT, related_name="direcciones",
        db_column="id_comuna", verbose_name="comuna",
    )
    tipo = models.CharField(
        max_length=20, choices=Tipo.choices, verbose_name="tipo de direccion"
    )
    calle = models.CharField(max_length=200, verbose_name="calle")
    numero = models.CharField(max_length=20, blank=True, verbose_name="numero")
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name="latitud",
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name="longitud",
    )
    validada = models.BooleanField(
        default=False, verbose_name="validada por geocodificacion"
    )

    class Meta:
        db_table = "direccion_cliente"
        verbose_name = "direccion de cliente"
        verbose_name_plural = "direcciones de cliente"
        ordering = ["cliente", "tipo"]

    def __str__(self) -> str:
        return f"{self.calle} {self.numero}, {self.comuna}".strip()
