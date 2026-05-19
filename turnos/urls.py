from django.urls import path

from .views import (
    TurnoAusenteView,
    TurnoCancelarView,
    TurnoCompletarView,
    TurnoConfirmarView,
    TurnoCreateView,
    TurnoDetailView,
    TurnoListView,
    TurnoUpdateView,
)

app_name = "turnos"

urlpatterns = [
    path("", TurnoListView.as_view(), name="lista"),
    path("crear/", TurnoCreateView.as_view(), name="crear"),
    path("<int:pk>/", TurnoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", TurnoUpdateView.as_view(), name="editar"),
    path("<int:pk>/cancelar/", TurnoCancelarView.as_view(), name="cancelar"),
    path("<int:pk>/confirmar/", TurnoConfirmarView.as_view(), name="confirmar"),
    path("<int:pk>/completar/", TurnoCompletarView.as_view(), name="completar"),
    path("<int:pk>/ausente/", TurnoAusenteView.as_view(), name="ausente"),
]
