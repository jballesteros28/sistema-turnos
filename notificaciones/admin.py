from django.contrib import admin

from .models import NotificacionEmail


@admin.register(NotificacionEmail)
class NotificacionEmailAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "destinatario_email",
        "estado",
        "negocio",
        "turno",
        "enviado_en",
        "creado_en",
    )
    list_filter = ("tipo", "estado", "negocio", "creado_en")
    search_fields = (
        "destinatario_email",
        "asunto",
        "negocio__nombre",
        "turno__cliente__nombre",
        "turno__cliente__apellido",
    )
    ordering = ("-creado_en",)
