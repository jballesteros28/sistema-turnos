from django.urls import path

from .views import (
    DisponibilidadActivarView,
    DisponibilidadCreateView,
    DisponibilidadDesactivarView,
    DisponibilidadDetailView,
    DisponibilidadListView,
    DisponibilidadUpdateView,
)

app_name = "disponibilidades"

urlpatterns = [
    path("", DisponibilidadListView.as_view(), name="lista"),
    path("crear/", DisponibilidadCreateView.as_view(), name="crear"),
    path("<int:pk>/", DisponibilidadDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", DisponibilidadUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", DisponibilidadDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", DisponibilidadActivarView.as_view(), name="activar"),
]
