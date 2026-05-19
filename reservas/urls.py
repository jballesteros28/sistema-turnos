from django.urls import path

from . import views


app_name = "reservas"

urlpatterns = [
    path(
        "reservar/<slug:negocio_slug>/",
        views.negocio_publico,
        name="negocio_publico",
    ),
    path(
        "reservar/<slug:negocio_slug>/turno/",
        views.seleccionar_turno,
        name="seleccionar_turno",
    ),
    path(
        "reservar/<slug:negocio_slug>/confirmar/",
        views.confirmar_reserva,
        name="confirmar_reserva",
    ),
    path(
        "reservar/<slug:negocio_slug>/exito/",
        views.reserva_exitosa,
        name="reserva_exitosa",
    ),
]
