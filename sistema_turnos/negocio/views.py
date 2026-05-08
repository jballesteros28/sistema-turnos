from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from usuarios.mixins import (
    GestionNegocioObjectRequiredMixin,
    LoginRequiredUserFormMixin,
    SuperadminRequiredMixin,
)
from usuarios.permissions import get_negocios_permitidos

from .forms import NegocioForm
from .models import EstadoNegocio, Negocio, TipoNegocio


class NegocioQuerySetMixin(LoginRequiredUserFormMixin):
    model = Negocio

    def get_queryset(self):
        return get_negocios_permitidos(self.request.user)


class NegocioListView(NegocioQuerySetMixin, ListView):
    template_name = "negocios/negocio_list.html"
    context_object_name = "negocios"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()
        self.tipo_negocio = self.request.GET.get("tipo_negocio", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(nombre__icontains=self.query)
                | Q(nombre_visible__icontains=self.query)
                | Q(email_principal__icontains=self.query)
                | Q(telefono_principal__icontains=self.query)
                | Q(whatsapp_principal__icontains=self.query)
                | Q(ciudad__icontains=self.query)
                | Q(pais__icontains=self.query)
            )

        estados_validos = {value for value, _label in EstadoNegocio.choices}
        if self.estado in estados_validos:
            queryset = queryset.filter(estado=self.estado)

        tipos_validos = {value for value, _label in TipoNegocio.choices}
        if self.tipo_negocio in tipos_validos:
            queryset = queryset.filter(tipo_negocio=self.tipo_negocio)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["estado_actual"] = self.estado
        context["tipo_actual"] = self.tipo_negocio
        context["estados"] = EstadoNegocio.choices
        context["tipos_negocio"] = TipoNegocio.choices
        return context


class NegocioDetailView(NegocioQuerySetMixin, DetailView):
    template_name = "negocios/negocio_detail.html"
    context_object_name = "negocio"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["configuracion"] = getattr(self.object, "configuracion", None)
        return context


class NegocioCreateView(SuperadminRequiredMixin, NegocioQuerySetMixin, CreateView):
    form_class = NegocioForm
    template_name = "negocios/negocio_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo negocio"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Negocio creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("negocios:detalle", kwargs={"pk": self.object.pk})


class NegocioUpdateView(
    GestionNegocioObjectRequiredMixin,
    NegocioQuerySetMixin,
    UpdateView,
):
    form_class = NegocioForm
    template_name = "negocios/negocio_form.html"
    context_object_name = "negocio"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar negocio"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Negocio actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("negocios:detalle", kwargs={"pk": self.object.pk})


class NegocioDesactivarView(
    GestionNegocioObjectRequiredMixin,
    NegocioQuerySetMixin,
    View,
):
    template_name = "negocios/negocio_confirm_desactivar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"negocio": self.get_object()})

    def post(self, request, *args, **kwargs):
        negocio = self.get_object()
        negocio.estado = EstadoNegocio.INACTIVO
        negocio.fecha_baja = timezone.now()
        negocio.save(update_fields=["estado", "fecha_baja", "actualizado_en"])
        messages.success(request, "Negocio desactivado correctamente.")
        return redirect("negocios:detalle", pk=negocio.pk)


class NegocioActivarView(
    GestionNegocioObjectRequiredMixin,
    NegocioQuerySetMixin,
    View,
):
    def post(self, request, *args, **kwargs):
        negocio = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        negocio.estado = EstadoNegocio.ACTIVO
        negocio.fecha_baja = None
        negocio.motivo_baja = ""
        negocio.save(
            update_fields=["estado", "fecha_baja", "motivo_baja", "actualizado_en"]
        )
        messages.success(request, "Negocio activado correctamente.")
        return redirect("negocios:detalle", pk=negocio.pk)
