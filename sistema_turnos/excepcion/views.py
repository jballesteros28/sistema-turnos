from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from negocio.models import Negocio
from profesional.models import Profesional
from sistema_turnos.view_utils import get_query_initial
from sucursal.models import Sucursal
from usuarios.mixins import (
    GestionOperacionFormRequiredMixin,
    GestionOperacionObjectRequiredMixin,
    LoginRequiredUserFormMixin,
)
from usuarios.permissions import filtrar_por_negocios_permitidos, get_negocios_permitidos

from .forms import ExcepcionAgendaForm
from .models import ExcepcionAgenda, TipoExcepcion


ESTADOS_EXCEPCION = (
    ("activa", "Activa"),
    ("inactiva", "Inactiva"),
)


class ExcepcionAgendaQuerySetMixin(LoginRequiredUserFormMixin):
    model = ExcepcionAgenda

    def get_queryset(self):
        queryset = ExcepcionAgenda.objects.select_related(
            "negocio",
            "sucursal",
            "profesional",
        )
        return filtrar_por_negocios_permitidos(queryset, self.request.user)


class ExcepcionAgendaListView(ExcepcionAgendaQuerySetMixin, ListView):
    template_name = "agenda/excepciones/excepcion_list.html"
    context_object_name = "excepciones"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()
        self.sucursal_id = self.request.GET.get("sucursal", "").strip()
        self.profesional_id = self.request.GET.get("profesional", "").strip()
        self.tipo = self.request.GET.get("tipo", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()
        self.fecha = self.request.GET.get("fecha", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(titulo__icontains=self.query)
                | Q(descripcion__icontains=self.query)
                | Q(negocio__nombre__icontains=self.query)
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

        tipos_validos = {value for value, _label in TipoExcepcion.choices}
        if self.tipo in tipos_validos:
            queryset = queryset.filter(tipo=self.tipo)

        if self.estado == "activa":
            queryset = queryset.filter(activo=True)
        elif self.estado == "inactiva":
            queryset = queryset.filter(activo=False)

        fecha = parse_date(self.fecha)
        if fecha:
            queryset = queryset.filter(
                fecha_hora_inicio__date__lte=fecha,
                fecha_hora_fin__date__gte=fecha,
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["negocio_actual"] = self.negocio_id
        context["sucursal_actual"] = self.sucursal_id
        context["profesional_actual"] = self.profesional_id
        context["tipo_actual"] = self.tipo
        context["estado_actual"] = self.estado
        context["fecha_actual"] = self.fecha
        context["negocios"] = get_negocios_permitidos(self.request.user).order_by("nombre")
        context["sucursales"] = filtrar_por_negocios_permitidos(
            Sucursal.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "nombre",
        )
        context["profesionales"] = filtrar_por_negocios_permitidos(
            Profesional.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "apellido",
            "nombre",
        )
        context["tipos"] = TipoExcepcion.choices
        context["estados"] = ESTADOS_EXCEPCION
        return context


class ExcepcionAgendaDetailView(ExcepcionAgendaQuerySetMixin, DetailView):
    template_name = "agenda/excepciones/excepcion_detail.html"
    context_object_name = "excepcion"


class ExcepcionAgendaCreateView(
    GestionOperacionFormRequiredMixin,
    ExcepcionAgendaQuerySetMixin,
    CreateView,
):
    form_class = ExcepcionAgendaForm
    template_name = "agenda/excepciones/excepcion_form.html"

    def get_initial(self):
        return get_query_initial(self.request, "negocio", "sucursal", "profesional")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nueva excepcion"
        context["avisos_base"] = []
        if not get_negocios_permitidos(self.request.user).exists():
            context["avisos_base"].append("Primero debes crear un negocio para continuar.")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Excepcion creada correctamente.")
        return response

    def get_success_url(self):
        return reverse("excepciones:detalle", kwargs={"pk": self.object.pk})


class ExcepcionAgendaUpdateView(
    GestionOperacionObjectRequiredMixin,
    ExcepcionAgendaQuerySetMixin,
    UpdateView,
):
    form_class = ExcepcionAgendaForm
    template_name = "agenda/excepciones/excepcion_form.html"
    context_object_name = "excepcion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar excepcion"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Excepcion actualizada correctamente.")
        return response

    def get_success_url(self):
        return reverse("excepciones:detalle", kwargs={"pk": self.object.pk})


class ExcepcionAgendaDesactivarView(
    GestionOperacionObjectRequiredMixin,
    ExcepcionAgendaQuerySetMixin,
    View,
):
    template_name = "agenda/excepciones/excepcion_confirm_desactivar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"excepcion": self.get_object()})

    def post(self, request, *args, **kwargs):
        excepcion = self.get_object()
        excepcion.activo = False
        excepcion.save(update_fields=["activo", "actualizado_en"])
        messages.success(request, "Excepcion desactivada correctamente.")
        return redirect("excepciones:detalle", pk=excepcion.pk)


class ExcepcionAgendaActivarView(
    GestionOperacionObjectRequiredMixin,
    ExcepcionAgendaQuerySetMixin,
    View,
):
    def post(self, request, *args, **kwargs):
        excepcion = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        excepcion.activo = True
        excepcion.save(update_fields=["activo", "actualizado_en"])
        messages.success(request, "Excepcion activada correctamente.")
        return redirect("excepciones:detalle", pk=excepcion.pk)
