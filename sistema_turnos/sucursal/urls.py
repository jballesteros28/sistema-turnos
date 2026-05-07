from django.urls import path

from .views import (
    SucursalActivarView,
    SucursalCreateView,
    SucursalDesactivarView,
    SucursalDetailView,
    SucursalListView,
    SucursalUpdateView,
)

app_name = "sucursales"

urlpatterns = [
    path("", SucursalListView.as_view(), name="lista"),
    path("crear/", SucursalCreateView.as_view(), name="crear"),
    path("<int:pk>/", SucursalDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", SucursalUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", SucursalDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", SucursalActivarView.as_view(), name="activar"),
]
