from django.contrib import admin

from .models import ExcepcionAgenda


@admin.register(ExcepcionAgenda)
class ExcepcionAgendaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "negocio",
        "tipo",
        "fecha_hora_inicio",
        "fecha_hora_fin",
        "bloquea_turnos",
        "activo",
    )
    list_filter = ("tipo", "bloquea_turnos", "activo", "negocio")
    search_fields = ("titulo", "descripcion", "profesional__nombre", "sucursal__nombre")
