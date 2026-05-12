from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from profesional.models import Profesional
from sistema_turnos.view_utils import get_query_id, get_query_initial
from sucursal.models import Sucursal
from usuarios.mixins import (
    GestionOperacionFormRequiredMixin,
    GestionOperacionObjectRequiredMixin,
    GestionOperacionRequiredMixin,
    LoginRequiredUserFormMixin,
)
from usuarios.permissions import filtrar_por_negocios_operacion, get_negocios_operacion

from .forms import DisponibilidadForm
from .models import DiaSemana, Disponibilidad


ESTADOS_DISPONIBILIDAD = (
    ("activa", "Activa"),
    ("inactiva", "Inactiva"),
)


class DisponibilidadQuerySetMixin(LoginRequiredUserFormMixin):
    model = Disponibilidad

    def get_queryset(self):
        queryset = Disponibilidad.objects.select_related(
            "negocio",
            "sucursal",
            "profesional",
        )
        return filtrar_por_negocios_operacion(queryset, self.request.user)


class DisponibilidadListView(DisponibilidadQuerySetMixin, ListView):
    template_name = "agenda/disponibilidades/disponibilidad_list.html"
    context_object_name = "disponibilidades"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()
        self.sucursal_id = self.request.GET.get("sucursal", "").strip()
        self.profesional_id = self.request.GET.get("profesional", "").strip()
        self.dia_semana = self.request.GET.get("dia_semana", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(negocio__nombre__icontains=self.query)
                | Q(sucursal__nombre__icontains=self.query)
                | Q(profesional__nombre__icontains=self.query)
                | Q(profesional__apellido__icontains=self.query)
                | Q(profesional__nombre_visible__icontains=self.query)
            )

        if self.negocio_id.isdigit():
            queryset = queryset.filter(negocio_id=self.negocio_id)

        if self.sucursal_id.isdigit():
            queryset = queryset.filter(sucursal_id=self.sucursal_id)

        if self.profesional_id.isdigit():
            queryset = queryset.filter(profesional_id=self.profesional_id)

        dias_validos = {str(value) for value, _label in DiaSemana.choices}
        if self.dia_semana in dias_validos:
            dia_semana = int(self.dia_semana)
            ids = [
                disponibilidad.pk
                for disponibilidad in queryset
                if disponibilidad.incluye_dia(dia_semana)
            ]
            queryset = queryset.filter(pk__in=ids)

        if self.estado == "activa":
            queryset = queryset.filter(activo=True)
        elif self.estado == "inactiva":
            queryset = queryset.filter(activo=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["negocio_actual"] = self.negocio_id
        context["sucursal_actual"] = self.sucursal_id
        context["profesional_actual"] = self.profesional_id
        context["dia_actual"] = self.dia_semana
        context["estado_actual"] = self.estado
        context["negocios"] = get_negocios_operacion(self.request.user).order_by("nombre")
        context["sucursales"] = filtrar_por_negocios_operacion(
            Sucursal.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "nombre",
        )
        context["profesionales"] = filtrar_por_negocios_operacion(
            Profesional.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "apellido",
            "nombre",
        )
        context["dias_semana"] = DiaSemana.choices
        context["estados"] = ESTADOS_DISPONIBILIDAD
        return context


class DisponibilidadDetailView(DisponibilidadQuerySetMixin, DetailView):
    template_name = "agenda/disponibilidades/disponibilidad_detail.html"
    context_object_name = "disponibilidad"


class DisponibilidadCreateView(
    GestionOperacionRequiredMixin,
    GestionOperacionFormRequiredMixin,
    DisponibilidadQuerySetMixin,
    CreateView,
):
    form_class = DisponibilidadForm
    template_name = "agenda/disponibilidades/disponibilidad_form.html"

    def get_initial(self):
        return get_query_initial(self.request, "negocio", "sucursal", "profesional")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nueva disponibilidad"
        context["avisos_base"] = self._get_avisos_base()
        return context

    def _get_avisos_base(self):
        avisos = []
        negocio_id = get_query_id(self.request, "negocio")

        if not get_negocios_operacion(self.request.user).exists():
            return ["Primero debes crear un negocio para continuar."]

        if negocio_id:
            if not filtrar_por_negocios_operacion(
                Sucursal.objects.filter(negocio_id=negocio_id),
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear una sucursal para este negocio.")
            if not filtrar_por_negocios_operacion(
                Profesional.objects.filter(negocio_id=negocio_id),
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear un profesional para este negocio.")
        else:
            if not filtrar_por_negocios_operacion(
                Sucursal.objects,
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear una sucursal para continuar.")
            if not filtrar_por_negocios_operacion(
                Profesional.objects,
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear un profesional para continuar.")

        return avisos

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Disponibilidad creada correctamente.")
        return response

    def get_success_url(self):
        return reverse("disponibilidades:detalle", kwargs={"pk": self.object.pk})


class DisponibilidadUpdateView(
    GestionOperacionObjectRequiredMixin,
    DisponibilidadQuerySetMixin,
    UpdateView,
):
    form_class = DisponibilidadForm
    template_name = "agenda/disponibilidades/disponibilidad_form.html"
    context_object_name = "disponibilidad"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar disponibilidad"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Disponibilidad actualizada correctamente.")
        return response

    def get_success_url(self):
        return reverse("disponibilidades:detalle", kwargs={"pk": self.object.pk})


class DisponibilidadDesactivarView(
    GestionOperacionObjectRequiredMixin,
    DisponibilidadQuerySetMixin,
    View,
):
    template_name = "agenda/disponibilidades/disponibilidad_confirm_desactivar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"disponibilidad": self.get_object()})

    def post(self, request, *args, **kwargs):
        disponibilidad = self.get_object()
        disponibilidad.activo = False
        disponibilidad.save(update_fields=["activo", "actualizado_en"])
        messages.success(request, "Disponibilidad desactivada correctamente.")
        return redirect("disponibilidades:detalle", pk=disponibilidad.pk)


class DisponibilidadActivarView(
    GestionOperacionObjectRequiredMixin,
    DisponibilidadQuerySetMixin,
    View,
):
    def post(self, request, *args, **kwargs):
        disponibilidad = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        disponibilidad.activo = True
        disponibilidad.save(update_fields=["activo", "actualizado_en"])
        messages.success(request, "Disponibilidad activada correctamente.")
        return redirect("disponibilidades:detalle", pk=disponibilidad.pk)
