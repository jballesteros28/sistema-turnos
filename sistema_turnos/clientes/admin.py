from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre_visible", "negocio", "estado", "telefono", "email")
    list_filter = ("estado", "acepta_recordatorios")
    search_fields = (
        "nombre",
        "apellido",
        "nombre_visible",
        "telefono",
        "whatsapp",
        "email",
        "numero_documento",
    )
    prepopulated_fields = {"slug": ("nombre_visible",)}
