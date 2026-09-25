"""Administracion de Django para el dominio de seguridad."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm

from .models import Auditoria, Permiso, Rol, RolPermiso, Usuario, UsuarioRol


class RolPermisoInline(admin.TabularInline):
    model = RolPermiso
    extra = 1
    autocomplete_fields = ["permiso"]


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]
    inlines = [RolPermisoInline]


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ["codigo", "modulo", "operacion"]
    list_filter = ["modulo", "operacion"]
    search_fields = ["codigo", "modulo"]


class UsuarioRolInline(admin.TabularInline):
    model = UsuarioRol
    extra = 1
    autocomplete_fields = ["rol"]


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    change_password_form = AdminPasswordChangeForm
    inlines = [UsuarioRolInline]
    list_display = ["username", "email", "es_interno", "estado", "ultimo_acceso"]
    list_filter = ["es_interno", "estado", "is_staff"]
    search_fields = ["username", "email"]
    ordering = ["username"]
    filter_horizontal = []

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Datos de contacto", {"fields": ("email",)}),
        ("Tipo de cuenta", {"fields": ("es_interno", "cliente")}),
        ("Estado", {"fields": ("estado", "intentos_fallidos", "ultimo_acceso")}),
        ("Permisos del administrador", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "es_interno"),
        }),
    )
    readonly_fields = ["ultimo_acceso"]


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    """Solo lectura: la bitacora nunca se edita a mano (RF-SEG-08)."""

    list_display = ["fecha_hora", "usuario", "entidad", "accion", "origen"]
    list_filter = ["accion", "entidad", "origen", "fecha_hora"]
    search_fields = ["entidad", "id_registro", "usuario__username"]
    date_hierarchy = "fecha_hora"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
