from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "negocio", "estado", "ciudad", "es_principal", "acepta_turnos")
    list_filter = ("estado", "acepta_turnos", "es_principal", "pais", "negocio")
    search_fields = ("nombre", "slug", "negocio__nombre", "telefono", "email")
    ordering = ("negocio", "nombre")
    prepopulated_fields = {"slug": ("nombre",)}
