from datetime import timedelta

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from clientes.models import Cliente
from configuracion_negocio.models import get_configuracion_turnos
from disponibilidad.models import Disponibilidad
from negocio.models import Negocio
from profesional.models import Profesional
from servicio.models import Servicio
from sistema_turnos.view_utils import get_query_id, get_query_initial
from sucursal.models import Sucursal
from usuarios.mixins import (
    GestionOperacionFormRequiredMixin,
    GestionOperacionObjectRequiredMixin,
    LoginRequiredUserFormMixin,
)
from usuarios.permissions import (
    filtrar_por_negocios_permitidos,
    filtrar_turnos_por_usuario,
    get_negocios_permitidos,
    get_profesionales_permitidos_para_turnos,
)

from .forms import TurnoForm
from .models import EstadoTurno, Turno


class TurnoQuerySetMixin(LoginRequiredUserFormMixin):
    model = Turno

    def get_queryset(self):
        queryset = Turno.objects.select_related(
            "negocio",
            "sucursal",
            "cliente",
            "profesional",
            "servicio",
        )
        return filtrar_turnos_por_usuario(queryset, self.request.user)


class TurnoListView(TurnoQuerySetMixin, ListView):
    template_name = "turnos/turno_list.html"
    context_object_name = "turnos"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        self.query = self.request.GET.get("q", "").strip()
        self.negocio_id = self.request.GET.get("negocio", "").strip()
        self.sucursal_id = self.request.GET.get("sucursal", "").strip()
        self.profesional_id = self.request.GET.get("profesional", "").strip()
        self.cliente_id = self.request.GET.get("cliente", "").strip()
        self.servicio_id = self.request.GET.get("servicio", "").strip()
        self.fecha = self.request.GET.get("fecha", "").strip()
        self.estado = self.request.GET.get("estado", "").strip()

        if self.query:
            queryset = queryset.filter(
                Q(negocio__nombre__icontains=self.query)
                | Q(sucursal__nombre__icontains=self.query)
                | Q(cliente__nombre__icontains=self.query)
                | Q(cliente__apellido__icontains=self.query)
                | Q(cliente__nombre_visible__icontains=self.query)
                | Q(profesional__nombre__icontains=self.query)
                | Q(profesional__apellido__icontains=self.query)
                | Q(profesional__nombre_visible__icontains=self.query)
                | Q(servicio__nombre__icontains=self.query)
            )

        if self.negocio_id.isdigit():
            queryset = queryset.filter(negocio_id=self.negocio_id)

        if self.sucursal_id.isdigit():
            queryset = queryset.filter(sucursal_id=self.sucursal_id)

        if self.profesional_id.isdigit():
            queryset = queryset.filter(profesional_id=self.profesional_id)

        if self.cliente_id.isdigit():
            queryset = queryset.filter(cliente_id=self.cliente_id)

        if self.servicio_id.isdigit():
            queryset = queryset.filter(servicio_id=self.servicio_id)

        fecha = parse_date(self.fecha)
        if fecha:
            queryset = queryset.filter(fecha_hora_inicio__date=fecha)

        estados_validos = {value for value, _label in EstadoTurno.choices}
        if self.estado in estados_validos:
            queryset = queryset.filter(estado=self.estado)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["negocio_actual"] = self.negocio_id
        context["sucursal_actual"] = self.sucursal_id
        context["profesional_actual"] = self.profesional_id
        context["cliente_actual"] = self.cliente_id
        context["servicio_actual"] = self.servicio_id
        context["fecha_actual"] = self.fecha
        context["estado_actual"] = self.estado
        context["negocios"] = get_negocios_permitidos(self.request.user).order_by("nombre")
        context["sucursales"] = filtrar_por_negocios_permitidos(
            Sucursal.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "nombre",
        )
        context["profesionales"] = get_profesionales_permitidos_para_turnos(
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "apellido",
            "nombre",
        )
        context["clientes"] = filtrar_por_negocios_permitidos(
            Cliente.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "apellido",
            "nombre",
        )
        context["servicios"] = filtrar_por_negocios_permitidos(
            Servicio.objects.select_related("negocio"),
            self.request.user,
        ).order_by(
            "negocio__nombre",
            "nombre",
        )
        context["estados"] = EstadoTurno.choices
        return context


class TurnoDetailView(TurnoQuerySetMixin, DetailView):
    template_name = "turnos/turno_detail.html"
    context_object_name = "turno"


class TurnoCreateView(
    GestionOperacionFormRequiredMixin,
    TurnoQuerySetMixin,
    CreateView,
):
    form_class = TurnoForm
    template_name = "turnos/turno_form.html"

    def get_initial(self):
        return get_query_initial(
            self.request,
            "negocio",
            "sucursal",
            "cliente",
            "profesional",
            "servicio",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Nuevo turno"
        context["avisos_base"] = self._get_avisos_base()
        return context

    def _get_avisos_base(self):
        avisos = []
        negocio_id = get_query_id(self.request, "negocio")

        if not get_negocios_permitidos(self.request.user).exists():
            return ["Primero debes crear un negocio para continuar."]

        if negocio_id:
            if not filtrar_por_negocios_permitidos(
                Sucursal.objects.filter(negocio_id=negocio_id),
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear una sucursal para este negocio.")
            if not filtrar_por_negocios_permitidos(
                Cliente.objects.filter(negocio_id=negocio_id),
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear un cliente para este negocio.")
            if not get_profesionales_permitidos_para_turnos(self.request.user).filter(
                negocio_id=negocio_id,
            ).exists():
                avisos.append("Primero debes crear un profesional para este negocio.")
            if not filtrar_por_negocios_permitidos(
                Servicio.objects.filter(negocio_id=negocio_id),
                self.request.user,
            ).exists():
                avisos.append("Primero debes crear un servicio para este negocio.")
            if not filtrar_por_negocios_permitidos(
                Disponibilidad.objects.filter(negocio_id=negocio_id, activo=True),
                self.request.user,
            ).exists():
                avisos.append(
                    "Primero debes cargar disponibilidad para poder crear turnos."
                )
        else:
            if not filtrar_por_negocios_permitidos(Sucursal.objects, self.request.user).exists():
                avisos.append("Primero debes crear una sucursal para continuar.")
            if not filtrar_por_negocios_permitidos(Cliente.objects, self.request.user).exists():
                avisos.append("Primero debes crear un cliente para continuar.")
            if not get_profesionales_permitidos_para_turnos(self.request.user).exists():
                avisos.append("Primero debes crear un profesional para continuar.")
            if not filtrar_por_negocios_permitidos(Servicio.objects, self.request.user).exists():
                avisos.append("Primero debes crear un servicio para continuar.")
            if not filtrar_por_negocios_permitidos(
                Disponibilidad.objects.filter(activo=True),
                self.request.user,
            ).exists():
                avisos.append(
                    "Primero debes cargar disponibilidad para poder crear turnos."
                )

        return avisos

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Turno creado correctamente.")
        return response

    def get_success_url(self):
        return reverse("turnos:detalle", kwargs={"pk": self.object.pk})


class TurnoUpdateView(
    GestionOperacionObjectRequiredMixin,
    TurnoQuerySetMixin,
    UpdateView,
):
    form_class = TurnoForm
    template_name = "turnos/turno_form.html"
    context_object_name = "turno"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Editar turno"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Turno actualizado correctamente.")
        return response

    def get_success_url(self):
        return reverse("turnos:detalle", kwargs={"pk": self.object.pk})


class TurnoCancelarView(
    GestionOperacionObjectRequiredMixin,
    TurnoQuerySetMixin,
    View,
):
    template_name = "turnos/turno_confirm_cancelar.html"

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        turno = self.get_object()
        error = self._get_error_cancelacion(turno)
        if error:
            messages.error(request, error)
            return redirect("turnos:detalle", pk=turno.pk)
        return render(request, self.template_name, {"turno": turno})

    def post(self, request, *args, **kwargs):
        turno = self.get_object()
        error = self._get_error_cancelacion(turno)
        if error:
            messages.error(request, error)
            return redirect("turnos:detalle", pk=turno.pk)

        turno.estado = EstadoTurno.CANCELADO
        turno.cancelado_en = timezone.now()
        turno.motivo_cancelacion = request.POST.get("motivo_cancelacion", "").strip()
        turno.save(
            update_fields=[
                "estado",
                "cancelado_en",
                "motivo_cancelacion",
                "actualizado_en",
            ]
        )
        messages.success(request, "Turno cancelado correctamente.")
        return redirect("turnos:detalle", pk=turno.pk)

    def _get_error_cancelacion(self, turno):
        configuracion = get_configuracion_turnos(turno.negocio)
        if not configuracion.permite_cancelacion:
            return "Este negocio no permite cancelar turnos."

        tiempo_minimo = configuracion.tiempo_minimo_cancelacion_minutos
        if tiempo_minimo and turno.fecha_hora_inicio - timezone.now() < timedelta(
            minutes=tiempo_minimo,
        ):
            if tiempo_minimo % 60 == 0:
                tiempo = f"{tiempo_minimo // 60} horas"
            else:
                tiempo = f"{tiempo_minimo} minutos"
            return f"La cancelacion debe realizarse al menos {tiempo} antes del turno."

        return ""


class TurnoCambiarEstadoView(
    GestionOperacionObjectRequiredMixin,
    TurnoQuerySetMixin,
    View,
):
    estado = None
    mensaje = ""

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        turno = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        turno.estado = self.estado
        update_fields = ["estado", "actualizado_en"]

        if self.estado == EstadoTurno.CONFIRMADO:
            turno.confirmado_en = timezone.now()
            update_fields.append("confirmado_en")

        turno.save(update_fields=update_fields)
        messages.success(request, self.mensaje)
        return redirect("turnos:detalle", pk=turno.pk)


class TurnoConfirmarView(TurnoCambiarEstadoView):
    estado = EstadoTurno.CONFIRMADO
    mensaje = "Turno confirmado correctamente."


class TurnoCompletarView(TurnoCambiarEstadoView):
    estado = EstadoTurno.COMPLETADO
    mensaje = "Turno marcado como completado."


class TurnoAusenteView(TurnoCambiarEstadoView):
    estado = EstadoTurno.AUSENTE
    mensaje = "Turno marcado como ausente."
