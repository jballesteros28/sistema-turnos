from django.urls import path

from .views import (
    ConfiguracionNegocioCreateView,
    ConfiguracionNegocioDetailView,
    ConfiguracionNegocioListView,
    ConfiguracionNegocioUpdateView,
)


app_name = "configuracion_negocio"

urlpatterns = [
    path("", ConfiguracionNegocioListView.as_view(), name="lista"),
    path("crear/", ConfiguracionNegocioCreateView.as_view(), name="crear"),
    path("<int:pk>/", ConfiguracionNegocioDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ConfiguracionNegocioUpdateView.as_view(), name="editar"),
]
