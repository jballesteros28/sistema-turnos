from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from sistema_turnos.view_utils import get_query_initial
from usuarios.mixins import (
    GestionNegocioFormRequiredMixin,
    GestionNegocioObjectRequiredMixin,
    GestionNegocioRequiredMixin,
    LoginRequiredUserFormMixin,
)
from usuarios.permissions import filtrar_por_negocios_gestionables, get_negocios_gestionables

from .forms import ConfiguracionNegocioForm
from .models import ConfiguracionNegocio


class ConfiguracionNegocioQuerySetMixin(LoginRequiredUserFormMixin):
    model = ConfiguracionNegocio

    def get_queryset(self):
        queryset = ConfiguracionNegocio.objects.select_related("negocio")
        return filtrar_por_negocios_gestionables(queryset, self.request.user)


class ConfiguracionNegocioListView(
    GestionNegocioRequiredMixin,
    ConfiguracionNegocioQuerySetMixin,
    ListView,
):
    template_name = "configuracion/configuracion_list.html"
    context_object_name = "configuraciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(negocio__nombre__icontains=self.query)
                | Q(negocio__nombre_visible__icontains=self.query)
                | Q(negocio__email_principal__icontains=self.query)
            )

        if self.negocio_id.isdigit():
            queryset = queryset.filter(negocio_id=self.negocio_id)

        return queryset.order_by("negocio__nombre")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["negocio_actual"] = self.negocio_id
        context["negocios"] = get_negocios_gestionables(self.request.user).order_by("nombre")
        return context


class ConfiguracionNegocioDetailView(
    GestionNegocioRequiredMixin,
    ConfiguracionNegocioQuerySetMixin,
    DetailView,
):
    template_name = "configuracion/configuracion_detail.html"
    context_object_name = "configuracion"


class ConfiguracionNegocioCreateView(
    GestionNegocioRequiredMixin,
    GestionNegocioFormRequiredMixin,
    ConfiguracionNegocioQuerySetMixin,
    CreateView,
):
    form_class = ConfiguracionNegocioForm
    template_name = "configuracion/configuracion_form.html"

    def dispatch(self, request, *args, **kwargs):
        negocio_id = request.GET.get("negocio", "").strip()
        if negocio_id.isdigit():
            configuracion = self.get_queryset().filter(negocio_id=negocio_id).first()
            if configuracion:
                return redirect("configuracion_negocio:editar", pk=configuracion.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return get_query_initial(self.request, "negocio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nueva configuracion"
        context["avisos_base"] = []
        if not get_negocios_gestionables(self.request.user).exists():
            context["avisos_base"].append("Primero debes crear un negocio para continuar.")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Configuracion creada correctamente.")
        return response

    def get_success_url(self):
        return reverse("configuracion_negocio:detalle", kwargs={"pk": self.object.pk})


class ConfiguracionNegocioUpdateView(
    GestionNegocioRequiredMixin,
    GestionNegocioObjectRequiredMixin,
    ConfiguracionNegocioQuerySetMixin,
    UpdateView,
):
    form_class = ConfiguracionNegocioForm
    template_name = "configuracion/configuracion_form.html"
    context_object_name = "configuracion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar configuracion"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Configuracion actualizada correctamente.")
        return response

    def get_success_url(self):
        return reverse("configuracion_negocio:detalle", kwargs={"pk": self.object.pk})
