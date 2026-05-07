from django.urls import path

from .views import (
    ClienteActivarView,
    ClienteCreateView,
    ClienteDesactivarView,
    ClienteDetailView,
    ClienteListView,
    ClienteUpdateView,
)

app_name = "clientes"

urlpatterns = [
    path("", ClienteListView.as_view(), name="lista"),
    path("crear/", ClienteCreateView.as_view(), name="crear"),
    path("<int:pk>/", ClienteDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ClienteUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", ClienteDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", ClienteActivarView.as_view(), name="activar"),
]
