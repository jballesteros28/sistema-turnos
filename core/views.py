from datetime import datetime, time, timedelta

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from clientes.models import Cliente, EstadoCliente
from configuracion_negocio.models import ConfiguracionNegocio
from disponibilidad.models import Disponibilidad
from excepcion.models import ExcepcionAgenda
from negocio.models import EstadoNegocio
from profesional.models import EstadoProfesional, Profesional
from servicio.models import EstadoServicio, Servicio
from sucursal.models import EstadoSucursal, Sucursal
from turnos.models import EstadoTurno, Turno
from reservas.services import negocio_permite_reserva_online
from usuarios.permissions import (
    filtrar_por_negocios_gestionables,
    filtrar_por_negocios_operacion,
    filtrar_turnos_por_usuario,
    get_negocios_permitidos,
    get_negocios_visibles,
    get_permisos_ui,
    usuario_tiene_membresias,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        current_timezone = timezone.get_current_timezone()
        today_start = timezone.make_aware(
            datetime.combine(today, time.min),
            current_timezone,
        )
        tomorrow_start = timezone.make_aware(
            datetime.combine(tomorrow, time.min),
            current_timezone,
        )

        turnos = Turno.objects.select_related(
            "negocio",
            "sucursal",
            "cliente",
            "profesional",
            "servicio",
        )
        turnos = filtrar_turnos_por_usuario(turnos, user)
        turnos_hoy = turnos.filter(
            fecha_hora_inicio__gte=today_start,
            fecha_hora_inicio__lt=tomorrow_start,
        ).order_by("fecha_hora_inicio")
        permisos = get_permisos_ui(user)
        negocios = get_negocios_permitidos(user)
        negocios_visibles = get_negocios_visibles(user)
        sucursales = filtrar_por_negocios_operacion(Sucursal.objects, user)
        clientes = filtrar_por_negocios_operacion(Cliente.objects, user)
        servicios = filtrar_por_negocios_operacion(Servicio.objects, user)
        profesionales = filtrar_por_negocios_operacion(Profesional.objects, user)
        disponibilidades = filtrar_por_negocios_operacion(Disponibilidad.objects, user)
        excepciones = filtrar_por_negocios_operacion(ExcepcionAgenda.objects, user)
        configuraciones = filtrar_por_negocios_gestionables(
            ConfiguracionNegocio.objects,
            user,
        )

        metric_cards = []
        if permisos["puede_ver_negocios"]:
            metric_cards.append(
                {
                    "label": "Negocios activos",
                    "value": negocios_visibles.filter(estado=EstadoNegocio.ACTIVO).count(),
                    "url": reverse("negocios:lista"),
                }
            )
        if permisos["puede_ver_catalogos"]:
            metric_cards.extend(
                [
                    {
                        "label": "Sucursales activas",
                        "value": sucursales.filter(estado=EstadoSucursal.ACTIVA).count(),
                        "url": reverse("sucursales:lista"),
                    },
                    {
                        "label": "Servicios activos",
                        "value": servicios.filter(estado=EstadoServicio.ACTIVO).count(),
                        "url": reverse("servicios:lista"),
                    },
                    {
                        "label": "Profesionales activos",
                        "value": profesionales.filter(
                            estado=EstadoProfesional.ACTIVO,
                        ).count(),
                        "url": reverse("profesionales:lista"),
                    },
                ]
            )
        if permisos["puede_ver_clientes"]:
            metric_cards.append(
                {
                    "label": "Clientes activos",
                    "value": clientes.filter(estado=EstadoCliente.ACTIVO).count(),
                    "url": reverse("clientes:lista"),
                }
            )
        if permisos["puede_ver_disponibilidades"]:
            metric_cards.append(
                {
                    "label": "Disponibilidades activas",
                    "value": disponibilidades.filter(activo=True).count(),
                    "url": reverse("disponibilidades:lista"),
                }
            )
        if permisos["puede_ver_excepciones"]:
            metric_cards.append(
                {
                    "label": "Excepciones activas",
                    "value": excepciones.filter(activo=True).count(),
                    "url": reverse("excepciones:lista"),
                }
            )
        if permisos["puede_ver_turnos"]:
            metric_cards.extend(
                [
                    {
                        "label": "Turnos de hoy",
                        "value": turnos_hoy.count(),
                        "url": reverse("turnos:lista"),
                    },
                    {
                        "label": "Turnos solicitados",
                        "value": turnos.filter(estado=EstadoTurno.SOLICITADO).count(),
                        "url": reverse("turnos:lista"),
                    },
                    {
                        "label": "Turnos confirmados",
                        "value": turnos.filter(estado=EstadoTurno.CONFIRMADO).count(),
                        "url": reverse("turnos:lista"),
                    },
                ]
            )
        if permisos["puede_ver_configuracion"]:
            metric_cards.append(
                {
                    "label": "Configuraciones",
                    "value": configuraciones.count(),
                    "url": reverse("configuracion_negocio:lista"),
                }
            )

        quick_actions = []
        if permisos["puede_crear_negocios"]:
            quick_actions.append(
                {"label": "Nuevo negocio", "url": reverse("negocios:crear")}
            )
        if permisos["puede_gestionar_negocios"]:
            quick_actions.extend(
                [
                    {"label": "Nueva sucursal", "url": reverse("sucursales:crear")},
                    {"label": "Nuevo servicio", "url": reverse("servicios:crear")},
                    {
                        "label": "Nuevo profesional",
                        "url": reverse("profesionales:crear"),
                    },
                ]
            )
        if permisos["puede_gestionar_operacion"]:
            quick_actions.extend(
                [
                    {"label": "Nuevo cliente", "url": reverse("clientes:crear")},
                    {
                        "label": "Nueva disponibilidad",
                        "url": reverse("disponibilidades:crear"),
                    },
                    {
                        "label": "Nueva excepcion",
                        "url": reverse("excepciones:crear"),
                    },
                    {"label": "Nuevo turno", "url": reverse("turnos:crear")},
                ]
            )
        if permisos["puede_ver_configuracion"]:
            quick_actions.append(
                {
                    "label": "Configuraciones",
                    "url": reverse("configuracion_negocio:lista"),
                }
            )

        reserva_publica_links = []
        for negocio in negocios.filter(estado=EstadoNegocio.ACTIVO).order_by(
            "nombre_visible",
            "nombre",
        )[:6]:
            if not negocio_permite_reserva_online(negocio):
                continue
            path = reverse(
                "reservas:negocio_publico",
                kwargs={"negocio_slug": negocio.slug},
            )
            reserva_publica_links.append(
                {
                    "negocio": negocio,
                    "path": path,
                    "url": self.request.build_absolute_uri(path),
                }
            )

        context.update(
            {
                "today": today,
                "metric_cards": metric_cards,
                "turnos_hoy": turnos_hoy[:10],
                "proximos_turnos": turnos.filter(
                    fecha_hora_inicio__gte=tomorrow_start,
                ).order_by("fecha_hora_inicio")[:10],
                "hay_negocios": negocios.exists(),
                "usuario_sin_negocios": not usuario_tiene_membresias(user),
                "quick_actions": quick_actions,
                "reserva_publica_links": reserva_publica_links,
            }
        )
        return context
