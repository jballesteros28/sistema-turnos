from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from negocio.models import Negocio
from sucursal.models import Sucursal

from .forms import ProfesionalForm
from .models import EstadoProfesional, Profesional


class ProfesionalQuerySetMixin:
    model = Profesional

    def get_queryset(self):
        return Profesional.objects.select_related("negocio").prefetch_related(
            "sucursales",
            "servicios",
        )


class ProfesionalListView(ProfesionalQuerySetMixin, ListView):
    template_name = "profesionales/profesional_list.html"
    context_object_name = "profesionales"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()
        self.sucursal_id = self.request.GET.get("sucursal", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(nombre__icontains=self.query)
                | Q(apellido__icontains=self.query)
                | Q(nombre_visible__icontains=self.query)
                | Q(especialidad__icontains=self.query)
                | Q(matricula__icontains=self.query)
                | Q(email__icontains=self.query)
                | Q(telefono__icontains=self.query)
                | Q(whatsapp__icontains=self.query)
                | Q(negocio__nombre__icontains=self.query)
                | Q(servicios__nombre__icontains=self.query)
            ).distinct()

        estados_validos = {value for value, _label in EstadoProfesional.choices}
        if self.estado in estados_validos:
            queryset = queryset.filter(estado=self.estado)

        if self.negocio_id.isdigit():
            queryset = queryset.filter(negocio_id=self.negocio_id)

        if self.sucursal_id.isdigit():
            queryset = queryset.filter(sucursales__id=self.sucursal_id).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["estado_actual"] = self.estado
        context["negocio_actual"] = self.negocio_id
        context["sucursal_actual"] = self.sucursal_id
        context["estados"] = EstadoProfesional.choices
        context["negocios"] = Negocio.objects.order_by("nombre")
        context["sucursales"] = Sucursal.objects.select_related("negocio").order_by(
            "negocio__nombre",
            "nombre",
        )
        return context


class ProfesionalDetailView(ProfesionalQuerySetMixin, DetailView):
    template_name = "profesionales/profesional_detail.html"
    context_object_name = "profesional"


class ProfesionalCreateView(ProfesionalQuerySetMixin, CreateView):
    form_class = ProfesionalForm
    template_name = "profesionales/profesional_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo profesional"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Profesional creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("profesionales:detalle", kwargs={"pk": self.object.pk})


class ProfesionalUpdateView(ProfesionalQuerySetMixin, UpdateView):
    form_class = ProfesionalForm
    template_name = "profesionales/profesional_form.html"
    context_object_name = "profesional"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar profesional"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Profesional actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("profesionales:detalle", kwargs={"pk": self.object.pk})


class ProfesionalDesactivarView(ProfesionalQuerySetMixin, View):
    template_name = "profesionales/profesional_confirm_desactivar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"profesional": self.get_object()})

    def post(self, request, *args, **kwargs):
        profesional = self.get_object()
        profesional.estado = EstadoProfesional.INACTIVO
        profesional.acepta_turnos = False
        profesional.save(update_fields=["estado", "acepta_turnos", "actualizado_en"])
        messages.success(request, "Profesional desactivado correctamente.")
        return redirect("profesionales:detalle", pk=profesional.pk)


class ProfesionalActivarView(ProfesionalQuerySetMixin, View):
    def post(self, request, *args, **kwargs):
        profesional = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        profesional.estado = EstadoProfesional.ACTIVO
        profesional.acepta_turnos = True
        profesional.save(update_fields=["estado", "acepta_turnos", "actualizado_en"])
        messages.success(request, "Profesional activado correctamente.")
        return redirect("profesionales:detalle", pk=profesional.pk)
