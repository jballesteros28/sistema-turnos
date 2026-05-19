from django.contrib import admin

from .forms import DisponibilidadForm
from .models import DiaSemana, Disponibilidad


class DiasSemanaListFilter(admin.SimpleListFilter):
    title = "Dias de semana"
    parameter_name = "dia_semana"

    def lookups(self, request, model_admin):
        return DiaSemana.choices

    def queryset(self, request, queryset):
        dias_validos = {str(value) for value, _label in DiaSemana.choices}
        if self.value() not in dias_validos:
            return queryset

        dia_semana = int(self.value())
        ids = [
            disponibilidad.pk
            for disponibilidad in queryset
            if disponibilidad.incluye_dia(dia_semana)
        ]
        return queryset.filter(pk__in=ids)


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    form = DisponibilidadForm
    list_display = (
        "negocio",
        "sucursal",
        "profesional",
        "dias_semana_display",
        "hora_inicio",
        "hora_fin",
        "activo",
    )
    list_filter = ("activo", DiasSemanaListFilter, "negocio", "sucursal", "profesional")
    search_fields = (
        "negocio__nombre",
        "sucursal__nombre",
        "profesional__nombre",
        "profesional__apellido",
        "profesional__nombre_visible",
    )
    ordering = ("negocio", "sucursal", "profesional", "dia_semana", "hora_inicio")

    @admin.display(description="Dias de semana", ordering="dia_semana")
    def dias_semana_display(self, obj):
        return obj.dias_semana_display()
