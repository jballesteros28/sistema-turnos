from django.urls import path

from .views import (
    NegocioActivarView,
    NegocioCreateView,
    NegocioDesactivarView,
    NegocioDetailView,
    NegocioListView,
    NegocioUpdateView,
)

app_name = "negocios"

urlpatterns = [
    path("", NegocioListView.as_view(), name="lista"),
    path("crear/", NegocioCreateView.as_view(), name="crear"),
    path("<int:pk>/", NegocioDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", NegocioUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", NegocioDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", NegocioActivarView.as_view(), name="activar"),
]
