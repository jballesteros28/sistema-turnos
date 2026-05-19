from django.contrib import admin

from .models import ExcepcionAgenda


@admin.register(ExcepcionAgenda)
class ExcepcionAgendaAdmin(admin.ModelAdmin):
    list_display = (
        "negocio",
        "sucursal",
        "profesional",
        "tipo",
        "titulo",
        "fecha_hora_inicio",
        "fecha_hora_fin",
        "bloquea_turnos",
        "activo",
    )
    list_filter = (
        "tipo",
        "bloquea_turnos",
        "activo",
        "negocio",
        "sucursal",
        "profesional",
    )
    search_fields = (
        "titulo",
        "descripcion",
        "negocio__nombre",
        "profesional__nombre",
        "profesional__apellido",
        "profesional__nombre_visible",
        "sucursal__nombre",
    )
    ordering = ("negocio", "fecha_hora_inicio", "tipo")
