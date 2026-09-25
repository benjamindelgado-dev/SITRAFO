"""Administracion de Django para el dominio de clientes."""
from django.contrib import admin

from .models import Cliente, Comuna, ContactoCliente, DireccionCliente, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["codigo", "nombre"]
    search_fields = ["nombre", "codigo"]


@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "region"]
    list_filter = ["region"]
    search_fields = ["nombre"]
    autocomplete_fields = ["region"]


class ContactoInline(admin.TabularInline):
    model = ContactoCliente
    extra = 1


class DireccionInline(admin.TabularInline):
    model = DireccionCliente
    extra = 1
    autocomplete_fields = ["comuna"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["rut", "razon_social", "tipo_persona", "estado", "creado_en"]
    list_filter = ["tipo_persona", "estado"]
    search_fields = ["rut", "razon_social", "nombre_fantasia"]
    inlines = [ContactoInline, DireccionInline]
