from django.contrib import admin

from .models import MiembroNegocio


@admin.register(MiembroNegocio)
class MiembroNegocioAdmin(admin.ModelAdmin):
    list_display = ("user", "negocio", "rol", "profesional", "activo")
    list_filter = ("rol", "activo", "negocio")
    search_fields = (
        "user__username",
        "user__email",
        "negocio__nombre",
        "profesional__nombre",
        "profesional__apellido",
    )
