from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from negocio.models import Negocio

from .forms import SucursalForm
from .models import EstadoSucursal, Sucursal


class SucursalQuerySetMixin:
    model = Sucursal

    def get_queryset(self):
        return Sucursal.objects.select_related("negocio")


class SucursalListView(SucursalQuerySetMixin, ListView):
    template_name = "sucursales/sucursal_list.html"
    context_object_name = "sucursales"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(nombre__icontains=self.query)
                | Q(direccion__icontains=self.query)
                | Q(ciudad__icontains=self.query)
                | Q(pais__icontains=self.query)
                | Q(email__icontains=self.query)
                | Q(telefono__icontains=self.query)
                | Q(whatsapp__icontains=self.query)
                | Q(negocio__nombre__icontains=self.query)
            )

        estados_validos = {value for value, _label in EstadoSucursal.choices}
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
        context["estados"] = EstadoSucursal.choices
        context["negocios"] = Negocio.objects.order_by("nombre")
        return context


class SucursalDetailView(SucursalQuerySetMixin, DetailView):
    template_name = "sucursales/sucursal_detail.html"
    context_object_name = "sucursal"


class SucursalCreateView(SucursalQuerySetMixin, CreateView):
    form_class = SucursalForm
    template_name = "sucursales/sucursal_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nueva sucursal"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Sucursal creada correctamente.")
        return response

    def get_success_url(self):
        return reverse("sucursales:detalle", kwargs={"pk": self.object.pk})


class SucursalUpdateView(SucursalQuerySetMixin, UpdateView):
    form_class = SucursalForm
    template_name = "sucursales/sucursal_form.html"
    context_object_name = "sucursal"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar sucursal"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Sucursal actualizada correctamente.")
        return response

    def get_success_url(self):
        return reverse("sucursales:detalle", kwargs={"pk": self.object.pk})


class SucursalDesactivarView(SucursalQuerySetMixin, View):
    template_name = "sucursales/sucursal_confirm_desactivar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"sucursal": self.get_object()})

    def post(self, request, *args, **kwargs):
        sucursal = self.get_object()
        sucursal.estado = EstadoSucursal.INACTIVA
        sucursal.acepta_turnos = False
        sucursal.fecha_cierre = timezone.now()
        sucursal.save(
            update_fields=[
                "estado",
                "acepta_turnos",
                "fecha_cierre",
                "actualizado_en",
            ]
        )
        messages.success(request, "Sucursal desactivada correctamente.")
        return redirect("sucursales:detalle", pk=sucursal.pk)


class SucursalActivarView(SucursalQuerySetMixin, View):
    def post(self, request, *args, **kwargs):
        sucursal = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        sucursal.estado = EstadoSucursal.ACTIVA
        sucursal.acepta_turnos = True
        sucursal.fecha_cierre = None
        sucursal.motivo_cierre = ""
        sucursal.save(
            update_fields=[
                "estado",
                "acepta_turnos",
                "fecha_cierre",
                "motivo_cierre",
                "actualizado_en",
            ]
        )
        messages.success(request, "Sucursal activada correctamente.")
        return redirect("sucursales:detalle", pk=sucursal.pk)
