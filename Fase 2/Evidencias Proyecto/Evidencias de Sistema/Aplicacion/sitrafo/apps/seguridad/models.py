"""
Dominio 1 — Seguridad, roles y auditoria.

Tablas: rol, permiso, rol_permiso, usuario, usuario_rol, auditoria.
Cubre RF-SEG-01 a RF-SEG-10 y RF-ADM-07.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from apps.common.models import ActivableModel


class Rol(ActivableModel):
    """Perfil de acceso al que se asocian permisos (RF-SEG-02)."""

    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60, unique=True, verbose_name="nombre")
    descripcion = models.CharField(
        max_length=200, blank=True, verbose_name="descripcion"
    )

    class Meta:
        db_table = "rol"
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Permiso(models.Model):
    """
    Operacion atomica sobre un modulo. Unidad minima de autorizacion.

    El codigo sigue el formato modulo.operacion, por ejemplo cotizacion.aprobar.
    """

    class Operacion(models.TextChoices):
        CREAR = "crear", "Crear"
        LEER = "leer", "Leer"
        ACTUALIZAR = "actualizar", "Actualizar"
        ANULAR = "anular", "Anular"

    id_permiso = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=80, unique=True, verbose_name="codigo")
    modulo = models.CharField(max_length=40, verbose_name="modulo")
    operacion = models.CharField(
        max_length=20, choices=Operacion.choices, verbose_name="operacion"
    )

    class Meta:
        db_table = "permiso"
        verbose_name = "permiso"
        verbose_name_plural = "permisos"
        ordering = ["modulo", "operacion"]

    def __str__(self) -> str:
        return self.codigo


class RolPermiso(models.Model):
    """Matriz de permisos por rol (RF-SEG-02)."""

    rol = models.ForeignKey(
        Rol, on_delete=models.CASCADE, related_name="permisos_asignados",
        db_column="id_rol", verbose_name="rol",
    )
    permiso = models.ForeignKey(
        Permiso, on_delete=models.CASCADE, related_name="roles_asignados",
        db_column="id_permiso", verbose_name="permiso",
    )
    otorgado_en = models.DateTimeField(
        auto_now_add=True, verbose_name="otorgado en"
    )

    class Meta:
        db_table = "rol_permiso"
        verbose_name = "permiso de rol"
        verbose_name_plural = "permisos de rol"
        constraints = [
            models.UniqueConstraint(
                fields=["rol", "permiso"], name="uq_rol_permiso"
            )
        ]

    def __str__(self) -> str:
        return f"{self.rol} - {self.permiso}"


class UsuarioManager(BaseUserManager):
    """Gestor del modelo de usuario propio."""

    use_in_migrations = True

    def create_user(self, username, email, password=None, **extra):
        if not username:
            raise ValueError("El usuario requiere un nombre de acceso.")
        if not email:
            raise ValueError("El usuario requiere un correo electronico.")
        usuario = self.model(
            username=username, email=self.normalize_email(email), **extra
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username, email, password=None, **extra):
        extra.setdefault("es_interno", True)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff en True.")
        return self.create_user(username, email, password, **extra)


class Usuario(AbstractBaseUser):
    """
    Credencial de acceso al sistema.

    Modela tanto al funcionario interno como a la cuenta web del cliente, de
    modo que la autenticacion, el bloqueo y la auditoria operen igual para
    ambos. El atributo estado soporta la suspension exigida por RF-ADM-03.
    """

    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        SUSPENDIDO = "suspendido", "Suspendido"
        BLOQUEADO = "bloqueado", "Bloqueado"

    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(
        max_length=60, unique=True, verbose_name="nombre de acceso"
    )
    email = models.EmailField(
        max_length=150, unique=True, verbose_name="correo electronico"
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cuentas",
        db_column="id_cliente",
        verbose_name="cliente asociado",
        help_text="Solo para cuentas web de cliente. Nulo en usuarios internos.",
    )
    es_interno = models.BooleanField(
        default=False, verbose_name="es usuario interno"
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ACTIVO,
        verbose_name="estado",
    )
    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0, verbose_name="intentos fallidos consecutivos"
    )
    ultimo_acceso = models.DateTimeField(
        null=True, blank=True, verbose_name="ultimo acceso exitoso"
    )
    roles = models.ManyToManyField(
        Rol, through="UsuarioRol", related_name="usuarios", verbose_name="roles"
    )

    # Requeridos por el panel de administracion de Django
    is_staff = models.BooleanField(default=False, verbose_name="acceso al admin")
    is_superuser = models.BooleanField(default=False, verbose_name="superusuario")
    is_active = models.BooleanField(default=True, verbose_name="cuenta habilitada")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="creado en")

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.username

    # -- Autorizacion -------------------------------------------------------
    def has_perm(self, perm, obj=None) -> bool:
        """
        Denegado por defecto (RN-18). El superusuario es la unica excepcion;
        el resto se resuelve contra la matriz rol_permiso.
        """
        if self.is_superuser:
            return True
        return perm in self.codigos_permiso()

    def codigos_permiso(self) -> set[str]:
        """
        Permisos efectivos del usuario segun sus roles activos.

        Se calcula una vez por instancia: en la API cada peticion carga su
        propio usuario, de modo que un cambio en la matriz rige desde la
        peticion siguiente.
        """
        if not hasattr(self, "_codigos_permiso"):
            self._codigos_permiso = set(
                RolPermiso.objects.filter(rol__usuarios=self, rol__activo=True)
                .values_list("permiso__codigo", flat=True)
            )
        return self._codigos_permiso

    def has_module_perms(self, app_label) -> bool:
        if self.is_superuser:
            return True
        return RolPermiso.objects.filter(
            rol__usuarios=self, rol__activo=True, permiso__modulo=app_label
        ).exists()

    # -- Estado de la cuenta ------------------------------------------------
    @property
    def puede_ingresar(self) -> bool:
        return self.is_active and self.estado == self.Estado.ACTIVO

    def registrar_acceso_exitoso(self) -> None:
        self.intentos_fallidos = 0
        self.ultimo_acceso = timezone.now()
        self.save(update_fields=["intentos_fallidos", "ultimo_acceso"])

    def registrar_intento_fallido(self, maximo: int) -> None:
        """Bloquea la cuenta al superar el maximo configurado (RF-SEG-04)."""
        self.intentos_fallidos += 1
        campos = ["intentos_fallidos"]
        if self.intentos_fallidos >= maximo:
            self.estado = self.Estado.BLOQUEADO
            campos.append("estado")
        self.save(update_fields=campos)


class UsuarioRol(models.Model):
    """Asignacion de roles a usuarios."""

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="roles_asignados",
        db_column="id_usuario", verbose_name="usuario",
    )
    rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT, related_name="usuarios_asignados",
        db_column="id_rol", verbose_name="rol",
    )
    asignado_en = models.DateTimeField(
        auto_now_add=True, verbose_name="asignado en"
    )

    class Meta:
        db_table = "usuario_rol"
        verbose_name = "rol de usuario"
        verbose_name_plural = "roles de usuario"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "rol"], name="uq_usuario_rol"
            )
        ]

    def __str__(self) -> str:
        return f"{self.usuario} - {self.rol}"


class Auditoria(models.Model):
    """
    Bitacora de operaciones sobre entidades sensibles.

    Cubre RF-SEG-08, RF-SEG-09 y RF-ADM-07. Se escribe desde la capa de
    servicio, de modo que quede registrada cualquiera sea la interfaz de
    origen.
    """

    class Accion(models.TextChoices):
        CREACION = "creacion", "Creacion"
        MODIFICACION = "modificacion", "Modificacion"
        ANULACION = "anulacion", "Anulacion"
        ACCESO_DENEGADO = "acceso_denegado", "Acceso denegado"

    class Origen(models.TextChoices):
        ESCRITORIO = "escritorio", "Aplicacion de escritorio"
        WEB = "web", "Aplicacion web"
        SISTEMA = "sistema", "Proceso automatico"

    id_auditoria = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="auditorias",
        db_column="id_usuario", verbose_name="usuario",
    )
    entidad = models.CharField(max_length=60, verbose_name="entidad afectada")
    id_registro = models.CharField(max_length=40, verbose_name="id del registro")
    accion = models.CharField(
        max_length=20, choices=Accion.choices, verbose_name="accion"
    )
    valor_anterior = models.JSONField(
        null=True, blank=True, verbose_name="valor anterior"
    )
    valor_nuevo = models.JSONField(
        null=True, blank=True, verbose_name="valor nuevo"
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="fecha y hora"
    )
    origen = models.CharField(
        max_length=40, choices=Origen.choices, blank=True, verbose_name="origen"
    )

    class Meta:
        db_table = "auditoria"
        verbose_name = "registro de auditoria"
        verbose_name_plural = "bitacora de auditoria"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(
                fields=["usuario", "entidad", "fecha_hora"], name="idx_aud_filtro"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.fecha_hora:%Y-%m-%d %H:%M} {self.accion} {self.entidad}"
