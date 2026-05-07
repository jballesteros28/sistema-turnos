from django.contrib import admin

from .models import Negocio


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_negocio", "estado", "ciudad", "pais")
    list_filter = ("estado", "tipo_negocio", "pais")
    search_fields = ("nombre", "slug", "email_principal", "telefono_principal")
    ordering = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}
