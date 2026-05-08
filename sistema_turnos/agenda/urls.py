from django.urls import path

from .views import AgendaDiariaView

app_name = "agenda"

urlpatterns = [
    path("", AgendaDiariaView.as_view(), name="turnos"),
]
