from django.contrib import admin

from .models import Turno


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = (
        "negocio",
        "sucursal",
        "cliente",
        "profesional",
        "servicio",
        "fecha_hora_inicio",
        "fecha_hora_fin",
        "estado",
    )
    list_filter = (
        "estado",
        "origen",
        "negocio",
        "sucursal",
        "profesional",
        "servicio",
    )
    search_fields = (
        "negocio__nombre",
        "sucursal__nombre",
        "cliente__nombre",
        "cliente__apellido",
        "cliente__nombre_visible",
        "profesional__nombre",
        "profesional__apellido",
        "profesional__nombre_visible",
        "servicio__nombre",
    )
    ordering = ("-fecha_hora_inicio",)
    date_hierarchy = "fecha_hora_inicio"
