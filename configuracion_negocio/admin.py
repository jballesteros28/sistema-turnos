from django.contrib import admin

from .models import ConfiguracionNegocio


@admin.register(ConfiguracionNegocio)
class ConfiguracionNegocioAdmin(admin.ModelAdmin):
    list_display = (
        "negocio",
        "permite_reserva_online",
        "permite_cancelacion_online",
        "politica_confirmacion",
        "anticipacion_minima_reserva_minutos",
        "anticipacion_maxima_reserva_dias",
        "buffer_entre_turnos_minutos",
        "intervalo_turnos_minutos",
        "permite_turnos_pasados",
    )
    list_filter = (
        "permite_reserva_online",
        "permite_cancelacion_online",
        "politica_confirmacion",
        "permite_turnos_pasados",
    )
    search_fields = ("negocio__nombre",)
    ordering = ("negocio__nombre",)
