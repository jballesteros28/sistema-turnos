from django.contrib import admin

from .models import Disponibilidad


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = (
        "profesional",
        "sucursal",
        "negocio",
        "dia_semana",
        "hora_inicio",
        "hora_fin",
        "activo",
    )
    list_filter = ("activo", "dia_semana", "negocio")
    search_fields = ("profesional__nombre", "profesional__apellido", "sucursal__nombre")
