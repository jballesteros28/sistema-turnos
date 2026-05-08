from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from negocio.models import Negocio
from profesional.models import Profesional
from sucursal.models import Sucursal
from turnos.models import EstadoTurno, Turno
from usuarios.permissions import (
    filtrar_por_negocios_permitidos,
    filtrar_turnos_por_usuario,
    get_negocios_permitidos,
    get_profesionales_permitidos_para_turnos,
)


class AgendaDiariaView(LoginRequiredMixin, TemplateView):
    template_name = "agenda/turnos/agenda_diaria.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date, fecha_invalida = self._get_selected_date()
        negocio_id = self._get_numeric_filter("negocio")
        sucursal_id = self._get_numeric_filter("sucursal")
        profesional_id = self._get_numeric_filter("profesional")
        estado = self._get_estado_filter()

        turnos = filtrar_turnos_por_usuario(
            self._get_turnos(selected_date),
            self.request.user,
        )
        if negocio_id:
            turnos = turnos.filter(negocio_id=negocio_id)
        if sucursal_id:
            turnos = turnos.filter(sucursal_id=sucursal_id)
        if profesional_id:
            turnos = turnos.filter(profesional_id=profesional_id)
        if estado:
            turnos = turnos.filter(estado=estado)

        context.update(
            {
                "fecha_seleccionada": selected_date,
                "fecha_actual": selected_date.isoformat(),
                "fecha_invalida": fecha_invalida,
                "turnos": turnos,
                "negocios": get_negocios_permitidos(self.request.user).order_by("nombre"),
                "sucursales": filtrar_por_negocios_permitidos(
                    Sucursal.objects.select_related("negocio"),
                    self.request.user,
                ).order_by(
                    "negocio__nombre",
                    "nombre",
                ),
                "profesionales": get_profesionales_permitidos_para_turnos(
                    self.request.user,
                ).order_by(
                    "negocio__nombre",
                    "apellido",
                    "nombre",
                ),
                "estados": EstadoTurno.choices,
                "negocio_actual": negocio_id,
                "sucursal_actual": sucursal_id,
                "profesional_actual": profesional_id,
                "estado_actual": estado,
                "hay_negocios": get_negocios_permitidos(self.request.user).exists(),
                "hay_profesionales": get_profesionales_permitidos_para_turnos(
                    self.request.user,
                ).exists(),
                "dia_anterior_url": self._build_day_url(
                    selected_date - timedelta(days=1),
                    negocio_id,
                    sucursal_id,
                    profesional_id,
                    estado,
                ),
                "hoy_url": self._build_day_url(
                    timezone.localdate(),
                    negocio_id,
                    sucursal_id,
                    profesional_id,
                    estado,
                ),
                "dia_siguiente_url": self._build_day_url(
                    selected_date + timedelta(days=1),
                    negocio_id,
                    sucursal_id,
                    profesional_id,
                    estado,
                ),
            }
        )
        return context

    def _get_selected_date(self):
        raw_fecha = self.request.GET.get("fecha", "").strip()
        if not raw_fecha:
            return timezone.localdate(), False

        parsed_date = parse_date(raw_fecha)
        if parsed_date:
            return parsed_date, False

        return timezone.localdate(), True

    def _get_numeric_filter(self, name):
        value = self.request.GET.get(name, "").strip()
        if value.isdigit():
            return value
        return ""

    def _get_estado_filter(self):
        value = self.request.GET.get("estado", "").strip()
        estados_validos = {estado for estado, _label in EstadoTurno.choices}
        if value in estados_validos:
            return value
        return ""

    def _get_turnos(self, selected_date):
        current_timezone = timezone.get_current_timezone()
        day_start = timezone.make_aware(
            datetime.combine(selected_date, time.min),
            current_timezone,
        )
        next_day_start = timezone.make_aware(
            datetime.combine(selected_date + timedelta(days=1), time.min),
            current_timezone,
        )
        return (
            Turno.objects.select_related(
                "negocio",
                "sucursal",
                "cliente",
                "profesional",
                "servicio",
            )
            .filter(
                fecha_hora_inicio__gte=day_start,
                fecha_hora_inicio__lt=next_day_start,
            )
            .order_by(
                "fecha_hora_inicio",
                "profesional__apellido",
                "profesional__nombre",
            )
        )

    def _build_day_url(
        self,
        selected_date,
        negocio_id,
        sucursal_id,
        profesional_id,
        estado,
    ):
        params = {"fecha": selected_date.isoformat()}
        if negocio_id:
            params["negocio"] = negocio_id
        if sucursal_id:
            params["sucursal"] = sucursal_id
        if profesional_id:
            params["profesional"] = profesional_id
        if estado:
            params["estado"] = estado

        return f"{reverse('agenda:turnos')}?{urlencode(params)}"
