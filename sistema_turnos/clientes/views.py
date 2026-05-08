from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from negocio.models import Negocio
from sistema_turnos.view_utils import get_query_initial
from usuarios.mixins import (
    GestionOperacionFormRequiredMixin,
    GestionOperacionObjectRequiredMixin,
    LoginRequiredUserFormMixin,
)
from usuarios.permissions import filtrar_por_negocios_permitidos, get_negocios_permitidos

from .forms import ClienteForm
from .models import Cliente, EstadoCliente


class ClienteQuerySetMixin(LoginRequiredUserFormMixin):
    model = Cliente

    def get_queryset(self):
        queryset = Cliente.objects.select_related("negocio")
        return filtrar_por_negocios_permitidos(queryset, self.request.user)


class ClienteListView(ClienteQuerySetMixin, ListView):
    template_name = "clientes/lista.html"
    context_object_name = "clientes"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(nombre__icontains=self.query)
                | Q(apellido__icontains=self.query)
                | Q(nombre_visible__icontains=self.query)
                | Q(email__icontains=self.query)
                | Q(telefono__icontains=self.query)
                | Q(whatsapp__icontains=self.query)
                | Q(numero_documento__icontains=self.query)
                | Q(negocio__nombre__icontains=self.query)
            )

        estados_validos = {value for value, _label in EstadoCliente.choices}
        if self.estado in estados_validos:
            queryset = queryset.filter(estado=self.estado)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["estado_actual"] = self.estado
        context["estados"] = EstadoCliente.choices
        return context


class ClienteDetailView(ClienteQuerySetMixin, DetailView):
    template_name = "clientes/detalle.html"
    context_object_name = "cliente"


class ClienteCreateView(
    GestionOperacionFormRequiredMixin,
    ClienteQuerySetMixin,
    CreateView,
):
    form_class = ClienteForm
    template_name = "clientes/formulario.html"

    def get_initial(self):
        return get_query_initial(self.request, "negocio")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo cliente"
        context["avisos_base"] = []
        if not get_negocios_permitidos(self.request.user).exists():
            context["avisos_base"].append("Primero debes crear un negocio para continuar.")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Cliente creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("clientes:detalle", kwargs={"pk": self.object.pk})


class ClienteUpdateView(
    GestionOperacionObjectRequiredMixin,
    ClienteQuerySetMixin,
    UpdateView,
):
    form_class = ClienteForm
    template_name = "clientes/formulario.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar cliente"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Cliente actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("clientes:detalle", kwargs={"pk": self.object.pk})


class ClienteDesactivarView(
    GestionOperacionObjectRequiredMixin,
    ClienteQuerySetMixin,
    View,
):
    template_name = "clientes/confirmar_desactivacion.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"cliente": self.get_object()})

    def post(self, request, *args, **kwargs):
        cliente = self.get_object()
        cliente.estado = EstadoCliente.INACTIVO
        cliente.save(update_fields=["estado", "actualizado_en"])
        messages.success(request, "Cliente desactivado correctamente.")
        return redirect("clientes:detalle", pk=cliente.pk)


class ClienteActivarView(
    GestionOperacionObjectRequiredMixin,
    ClienteQuerySetMixin,
    View,
):
    def post(self, request, *args, **kwargs):
        cliente = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        cliente.estado = EstadoCliente.ACTIVO
        cliente.save(update_fields=["estado", "actualizado_en"])
        messages.success(request, "Cliente activado correctamente.")
        return redirect("clientes:detalle", pk=cliente.pk)
