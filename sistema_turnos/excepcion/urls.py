from django.urls import path

from .views import (
    ExcepcionAgendaActivarView,
    ExcepcionAgendaCreateView,
    ExcepcionAgendaDesactivarView,
    ExcepcionAgendaDetailView,
    ExcepcionAgendaListView,
    ExcepcionAgendaUpdateView,
)

app_name = "excepciones"

urlpatterns = [
    path("", ExcepcionAgendaListView.as_view(), name="lista"),
    path("crear/", ExcepcionAgendaCreateView.as_view(), name="crear"),
    path("<int:pk>/", ExcepcionAgendaDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ExcepcionAgendaUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", ExcepcionAgendaDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", ExcepcionAgendaActivarView.as_view(), name="activar"),
]
