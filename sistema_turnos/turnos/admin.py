from django.contrib import admin

from .models import Turno


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_hora_inicio",
        "fecha_hora_fin",
        "cliente",
        "profesional",
        "servicio",
        "sucursal",
        "estado",
    )
    list_filter = ("estado", "origen", "negocio", "sucursal", "profesional")
    search_fields = (
        "cliente__nombre",
        "cliente__apellido",
        "profesional__nombre",
        "profesional__apellido",
        "servicio__nombre",
    )
    date_hierarchy = "fecha_hora_inicio"
