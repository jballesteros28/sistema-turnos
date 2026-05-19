from django.urls import path

from .views import AgendaDiariaView, AgendaSemanalView

app_name = "agenda"

urlpatterns = [
    path("turnos/", AgendaDiariaView.as_view(), name="turnos"),
    path("semanal/", AgendaSemanalView.as_view(), name="semanal"),
]
