from django.contrib import admin

from .models import Profesional


@admin.register(Profesional)
class ProfesionalAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_visible",
        "negocio",
        "estado",
        "tipo_profesional",
        "acepta_turnos",
        "visible_en_reserva_online",
    )
    list_filter = ("estado", "tipo_profesional", "acepta_turnos", "visible_en_reserva_online")
    search_fields = ("nombre", "apellido", "nombre_visible", "slug", "negocio__nombre")
    prepopulated_fields = {"slug": ("nombre_visible",)}
    filter_horizontal = ("sucursales", "servicios")
