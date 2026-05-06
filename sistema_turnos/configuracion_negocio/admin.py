from django.contrib import admin

from .models import ConfiguracionNegocio


@admin.register(ConfiguracionNegocio)
class ConfiguracionNegocioAdmin(admin.ModelAdmin):
    list_display = (
        "negocio",
        "permite_reserva_online",
        "permite_cancelacion_online",
        "politica_confirmacion",
        "intervalo_turnos_minutos",
    )
    list_filter = (
        "permite_reserva_online",
        "permite_cancelacion_online",
        "politica_confirmacion",
    )
    search_fields = ("negocio__nombre",)
