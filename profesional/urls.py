from django.urls import path

from .views import (
    ProfesionalActivarView,
    ProfesionalCreateView,
    ProfesionalDesactivarView,
    ProfesionalDetailView,
    ProfesionalListView,
    ProfesionalUpdateView,
)

app_name = "profesionales"

urlpatterns = [
    path("", ProfesionalListView.as_view(), name="lista"),
    path("crear/", ProfesionalCreateView.as_view(), name="crear"),
    path("<int:pk>/", ProfesionalDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", ProfesionalUpdateView.as_view(), name="editar"),
    path("<int:pk>/desactivar/", ProfesionalDesactivarView.as_view(), name="desactivar"),
    path("<int:pk>/activar/", ProfesionalActivarView.as_view(), name="activar"),
]
