from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from negocio.models import Negocio

from .forms import ServicioForm
from .models import EstadoServicio, Servicio


class ServicioQuerySetMixin:
    model = Servicio

    def get_queryset(self):
        return Servicio.objects.select_related("negocio")


class ServicioListView(ServicioQuerySetMixin, ListView):
    template_name = "servicios/servicio_list.html"
    context_object_name = "servicios"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(nombre__icontains=self.query)
                | Q(descripcion__icontains=self.query)
                | Q(categoria__icontains=self.query)
                | Q(negocio__nombre__icontains=self.query)
            )

        estados_validos = {value for value, _label in EstadoServicio.choices}
        if self.estado in estados_validos:
            queryset = queryset.filter(estado=self.estado)

        if self.negocio_id.isdigit():
            queryset = queryset.filter(negocio_id=self.negocio_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["estado_actual"] = self.estado
        context["negocio_actual"] = self.negocio_id
        context["estados"] = EstadoServicio.choices
        context["negocios"] = Negocio.objects.order_by("nombre")
        return context


class ServicioDetailView(ServicioQuerySetMixin, DetailView):
    template_name = "servicios/servicio_detail.html"
    context_object_name = "servicio"


class ServicioCreateView(ServicioQuerySetMixin, CreateView):
    form_class = ServicioForm
    template_name = "servicios/servicio_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo servicio"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Servicio creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("servicios:detalle", kwargs={"pk": self.object.pk})


class ServicioUpdateView(ServicioQuerySetMixin, UpdateView):
    form_class = ServicioForm
    template_name = "servicios/servicio_form.html"
    context_object_name = "servicio"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar servicio"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Servicio actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("servicios:detalle", kwargs={"pk": self.object.pk})


class ServicioDesactivarView(ServicioQuerySetMixin, View):
    template_name = "servicios/servicio_confirm_desactivar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"servicio": self.get_object()})

    def post(self, request, *args, **kwargs):
        servicio = self.get_object()
        servicio.estado = EstadoServicio.INACTIVO
        servicio.save(update_fields=["estado", "actualizado_en"])
        messages.success(request, "Servicio desactivado correctamente.")
        return redirect("servicios:detalle", pk=servicio.pk)


class ServicioActivarView(ServicioQuerySetMixin, View):
    def post(self, request, *args, **kwargs):
        servicio = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        servicio.estado = EstadoServicio.ACTIVO
        servicio.save(update_fields=["estado", "actualizado_en"])
        messages.success(request, "Servicio activado correctamente.")
        return redirect("servicios:detalle", pk=servicio.pk)
