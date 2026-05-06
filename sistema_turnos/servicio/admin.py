from django.contrib import admin

from .models import Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "negocio",
        "estado",
        "duracion_minutos",
        "precio",
        "visible_en_reserva_online",
    )
    list_filter = ("estado", "visible_en_reserva_online", "categoria")
    search_fields = ("nombre", "slug", "negocio__nombre", "categoria")
    prepopulated_fields = {"slug": ("nombre",)}
