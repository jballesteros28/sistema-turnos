from django.contrib import admin

from .models import Disponibilidad


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = (
        "negocio",
        "sucursal",
        "profesional",
        "dia",
        "hora_inicio",
        "hora_fin",
        "activo",
    )
    list_filter = ("activo", "dia_semana", "negocio", "sucursal", "profesional")
    search_fields = (
        "negocio__nombre",
        "sucursal__nombre",
        "profesional__nombre",
        "profesional__apellido",
        "profesional__nombre_visible",
    )
    ordering = ("negocio", "sucursal", "profesional", "dia_semana", "hora_inicio")

    @admin.display(description="Dia de semana", ordering="dia_semana")
    def dia(self, obj):
        return obj.get_dia_semana_display()
