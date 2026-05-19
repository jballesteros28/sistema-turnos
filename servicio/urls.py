from django.urls import path

from .views import (
    ServicioActivarView,
    ServicioCreateView,
    ServicioDesactivarView,
    ServicioDetailView,
    ServicioListView,
    ServicioUpdateView,
)

app_name = "servicios"

urlpatterns = [
    path("", ServicioListView.as_view(), name="lista"),
    path("crear/", ServicioCreateView.as_view(), name="crear"),
    path("<int:pk>/", ServicioDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ServicioUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", ServicioDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", ServicioActivarView.as_view(), name="activar"),
]
