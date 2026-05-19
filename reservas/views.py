from datetime import datetime, timedelta

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from configuracion_negocio.models import get_configuracion_turnos
from negocio.models import EstadoNegocio, Negocio
from turnos.models import Turno

from .forms import DatosClienteReservaForm, SeleccionTurnoForm
from .services import (
    ReservaDuplicadaReciente,
    ReservaNoDisponible,
    buscar_slot_disponible,
    calcular_slots_disponibles,
    crear_turno_online,
    email_estado,
    email_enviado,
    get_profesionales_publicos,
    get_servicios_publicos,
    get_sucursales_publicas,
    negocio_permite_reserva_online,
)


def negocio_publico(request, negocio_slug):
    negocio = _get_negocio_publico(negocio_slug)
    sucursales = get_sucursales_publicas(negocio)
    servicios = get_servicios_publicos(negocio)
    return render(
        request,
        "reservas/negocio_publico.html",
        {
            "negocio": negocio,
            "sucursales": sucursales[:3],
            "servicios": servicios[:4],
            "hay_sucursales": sucursales.exists(),
            "hay_servicios": servicios.exists(),
        },
    )


def seleccionar_turno(request, negocio_slug):
    negocio = _get_negocio_publico(negocio_slug)
    form = SeleccionTurnoForm(negocio, request.GET or None)
    slots = []
    busqueda_realizada = bool(request.GET)
    hay_sucursales = form.fields["sucursal"].queryset.exists()
    hay_servicios = form.fields["servicio"].queryset.exists()
    hay_profesionales = form.fields["profesional"].queryset.exists()
    if not hay_profesionales and not form.is_bound:
        hay_profesionales = get_profesionales_publicos(negocio).exists()

    if busqueda_realizada and form.is_valid():
        slots = calcular_slots_disponibles(
            negocio=negocio,
            sucursal=form.cleaned_data["sucursal"],
            servicio=form.cleaned_data["servicio"],
            fecha=form.cleaned_data["fecha"],
            profesional=form.cleaned_data.get("profesional"),
        )

    return render(
        request,
        "reservas/seleccionar_turno.html",
        {
            "negocio": negocio,
            "form": form,
            "slots": slots,
            "busqueda_realizada": busqueda_realizada,
            "hay_sucursales": hay_sucursales,
            "hay_servicios": hay_servicios,
            "hay_profesionales": hay_profesionales,
        },
    )


def confirmar_reserva(request, negocio_slug):
    negocio = _get_negocio_publico(negocio_slug)
    seleccion = _get_seleccion_slot(
        negocio,
        request.POST if request.method == "POST" else request.GET,
        validar_disponibilidad=request.method != "POST",
    )

    if seleccion is None:
        return _render_no_disponible(request, negocio)

    if request.method == "POST":
        form = DatosClienteReservaForm(request.POST)
        if form.is_valid():
            try:
                turno, notificacion = crear_turno_online(
                    negocio=negocio,
                    sucursal=seleccion["sucursal"],
                    servicio=seleccion["servicio"],
                    profesional=seleccion["profesional"],
                    inicio=seleccion["slot"]["fecha_hora_inicio"],
                    datos_cliente=form.cleaned_data,
                )
            except ReservaNoDisponible:
                return _render_no_disponible(request, negocio)
            except ReservaDuplicadaReciente:
                form.add_error(
                    None,
                    (
                        "Ya recibimos una reserva igual hace unos minutos. "
                        "Si necesitas ayuda, comunicate con el negocio."
                    ),
                )
            else:
                request.session["reserva_exitosa_turno_id"] = turno.pk
                request.session["reserva_email_enviado"] = email_enviado(notificacion)
                request.session["reserva_email_estado"] = email_estado(notificacion)
                return redirect("reservas:reserva_exitosa", negocio_slug=negocio.slug)
    else:
        form = DatosClienteReservaForm()

    estado_esperado = _get_estado_esperado_reserva(negocio)
    return render(
        request,
        "reservas/confirmar_reserva.html",
        {
            "negocio": negocio,
            "form": form,
            "estado_esperado": estado_esperado,
            **seleccion,
        },
    )


def reserva_exitosa(request, negocio_slug):
    negocio = _get_negocio_publico(negocio_slug)
    turno = None
    turno_id = request.session.get("reserva_exitosa_turno_id")

    if turno_id:
        turno = (
            Turno.objects.select_related(
                "negocio",
                "sucursal",
                "cliente",
                "profesional",
                "servicio",
            )
            .filter(pk=turno_id, negocio=negocio)
            .first()
        )

    return render(
        request,
        "reservas/reserva_exitosa.html",
        {
            "negocio": negocio,
            "turno": turno,
            "email_enviado": request.session.get("reserva_email_enviado", False),
            "email_estado": request.session.get("reserva_email_estado", "sin_email"),
        },
    )


def _get_negocio_publico(negocio_slug):
    negocio = get_object_or_404(
        Negocio,
        slug=negocio_slug,
        estado=EstadoNegocio.ACTIVO,
    )
    if not negocio_permite_reserva_online(negocio):
        raise Http404("El negocio no permite reservas online.")
    return negocio


def _get_seleccion_slot(negocio, data, *, validar_disponibilidad=True):
    sucursal = get_sucursales_publicas(negocio).filter(pk=data.get("sucursal")).first()
    servicio = get_servicios_publicos(negocio).filter(pk=data.get("servicio")).first()
    inicio = _parse_inicio(data.get("inicio"))

    if sucursal is None or servicio is None or inicio is None:
        return None

    profesional_id = data.get("profesional")
    if not profesional_id:
        return None

    profesional = (
        sucursal.profesionales.filter(
            pk=profesional_id,
            negocio=negocio,
            servicios=servicio,
            estado="activo",
            acepta_turnos=True,
            visible_en_reserva_online=True,
        )
        .distinct()
        .first()
    )
    if profesional is None:
        return None

    slot = buscar_slot_disponible(
        negocio=negocio,
        sucursal=sucursal,
        servicio=servicio,
        profesional=profesional,
        inicio=inicio,
    )
    if slot is None and validar_disponibilidad:
        return None
    if slot is None:
        slot = _build_slot_no_verificado(inicio, servicio, profesional)

    return {
        "sucursal": sucursal,
        "servicio": servicio,
        "profesional": profesional,
        "slot": slot,
    }


def _parse_inicio(value):
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is None:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M")
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())

    return parsed.replace(second=0, microsecond=0)


def _build_slot_no_verificado(inicio, servicio, profesional):
    fin = inicio + timedelta(minutes=servicio.duracion_minutos)
    return {
        "fecha_hora_inicio": inicio,
        "fecha_hora_fin": fin,
        "profesional": profesional,
        "label_hora": timezone.localtime(inicio).strftime("%H:%M"),
        "label_fin": timezone.localtime(fin).strftime("%H:%M"),
        "value_inicio": timezone.localtime(inicio).strftime("%Y-%m-%dT%H:%M"),
    }


def _render_no_disponible(request, negocio):
    return render(
        request,
        "reservas/reserva_no_disponible.html",
        {"negocio": negocio},
        status=409,
    )


def _get_estado_esperado_reserva(negocio):
    configuracion = get_configuracion_turnos(negocio)
    if configuracion.confirmacion_automatica:
        return "Confirmado"
    return "Solicitado"
