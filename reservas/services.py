from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from clientes.models import Cliente
from configuracion_negocio.models import get_configuracion_turnos
from disponibilidad.models import Disponibilidad
from excepcion.models import ExcepcionAgenda
from negocio.models import EstadoNegocio
from notificaciones.models import EstadoNotificacionEmail
from notificaciones.services import enviar_email_turno_creado
from profesional.models import EstadoProfesional, Profesional
from servicio.models import EstadoServicio, Servicio
from sucursal.models import EstadoSucursal, Sucursal
from turnos.forms import ESTADOS_TURNO_ACTIVOS, TurnoForm
from turnos.models import OrigenTurno, Turno


class ReservaNoDisponible(Exception):
    pass


class ReservaDuplicadaReciente(Exception):
    pass


def negocio_permite_reserva_online(negocio):
    if not negocio or negocio.estado != EstadoNegocio.ACTIVO:
        return False

    configuracion = get_configuracion_turnos(negocio)
    return getattr(configuracion, "permite_reserva_online", True)


def get_sucursales_publicas(negocio):
    return Sucursal.objects.filter(
        negocio=negocio,
        estado=EstadoSucursal.ACTIVA,
        acepta_turnos=True,
    ).order_by("-es_principal", "nombre")


def get_servicios_publicos(negocio):
    return Servicio.objects.filter(
        negocio=negocio,
        estado=EstadoServicio.ACTIVO,
        visible_en_reserva_online=True,
    ).order_by("orden_visualizacion", "nombre")


def get_profesionales_publicos(negocio, *, sucursal=None, servicio=None):
    profesionales = Profesional.objects.filter(
        negocio=negocio,
        estado=EstadoProfesional.ACTIVO,
        acepta_turnos=True,
        visible_en_reserva_online=True,
    )

    if sucursal is not None:
        profesionales = profesionales.filter(sucursales=sucursal)

    if servicio is not None:
        profesionales = profesionales.filter(servicios=servicio)

    return profesionales.distinct().order_by(
        "orden_visualizacion",
        "apellido",
        "nombre",
    )


def calcular_slots_disponibles(
    negocio,
    sucursal,
    servicio,
    fecha,
    profesional=None,
):
    if not _entidades_publicas_validas(
        negocio=negocio,
        sucursal=sucursal,
        servicio=servicio,
        profesional=profesional,
    ):
        return []

    profesionales = get_profesionales_publicos(
        negocio,
        sucursal=sucursal,
        servicio=servicio,
    )
    if profesional is not None:
        profesionales = profesionales.filter(pk=profesional.pk)

    profesionales = list(profesionales)
    if not profesionales:
        return []

    configuracion = get_configuracion_turnos(negocio)
    duracion = timedelta(minutes=servicio.duracion_minutos)
    paso = timedelta(minutes=_get_intervalo_slots(negocio, servicio))
    dia_semana = fecha.weekday()
    slots = []
    slots_vistos = set()

    disponibilidades = (
        Disponibilidad.objects.select_related("profesional")
        .filter(
            negocio=negocio,
            sucursal=sucursal,
            profesional__in=profesionales,
            activo=True,
        )
        .filter(
            Q(fecha_desde__isnull=True) | Q(fecha_desde__lte=fecha),
            Q(fecha_hasta__isnull=True) | Q(fecha_hasta__gte=fecha),
        )
        .order_by("hora_inicio", "profesional__orden_visualizacion", "profesional__apellido")
    )

    for disponibilidad in disponibilidades:
        if not disponibilidad.incluye_dia(dia_semana):
            continue

        ventana_inicio = _aware_datetime(fecha, disponibilidad.hora_inicio)
        ventana_fin = _aware_datetime(fecha, disponibilidad.hora_fin)
        ultimo_inicio = ventana_fin - duracion
        inicio = ventana_inicio

        while inicio <= ultimo_inicio:
            fin = inicio + duracion
            clave = (disponibilidad.profesional_id, inicio)

            if clave not in slots_vistos and _slot_es_disponible(
                negocio=negocio,
                sucursal=sucursal,
                profesional=disponibilidad.profesional,
                inicio=inicio,
                fin=fin,
                configuracion=configuracion,
            ):
                slots_vistos.add(clave)
                slots.append(
                    _build_slot(
                        inicio=inicio,
                        fin=fin,
                        profesional=disponibilidad.profesional,
                    )
                )

            inicio += paso

    return sorted(
        slots,
        key=lambda slot: (
            slot["fecha_hora_inicio"],
            slot["profesional"].orden_visualizacion,
            slot["profesional"].apellido,
            slot["profesional"].nombre,
        ),
    )


def buscar_slot_disponible(negocio, sucursal, servicio, profesional, inicio):
    inicio_valor = _datetime_local_value(inicio)
    slots = calcular_slots_disponibles(
        negocio,
        sucursal,
        servicio,
        timezone.localtime(inicio).date(),
        profesional=profesional,
    )
    for slot in slots:
        if (
            slot["profesional"].pk == profesional.pk
            and slot["value_inicio"] == inicio_valor
        ):
            return slot
    return None


def crear_turno_online(
    *,
    negocio,
    sucursal,
    servicio,
    profesional,
    inicio,
    datos_cliente,
):
    try:
        with transaction.atomic():
            if _hay_reserva_duplicada_reciente(
                negocio=negocio,
                servicio=servicio,
                inicio=inicio,
                datos_cliente=datos_cliente,
            ):
                raise ReservaDuplicadaReciente(
                    "Ya existe una reserva reciente con esos datos."
                )

            slot = buscar_slot_disponible(
                negocio,
                sucursal,
                servicio,
                profesional,
                inicio,
            )
            if slot is None:
                raise ReservaNoDisponible("El horario ya no esta disponible.")

            cliente = obtener_o_crear_cliente_online(negocio, datos_cliente)
            form = TurnoForm(
                data={
                    "negocio": negocio.pk,
                    "sucursal": sucursal.pk,
                    "cliente": cliente.pk,
                    "profesional": profesional.pk,
                    "servicio": servicio.pk,
                    "fecha_hora_inicio": slot["value_inicio"],
                    "origen": OrigenTurno.ONLINE,
                    "notas": datos_cliente.get("observaciones", ""),
                }
            )
            if not form.is_valid():
                raise ReservaNoDisponible(form.errors.as_text())

            turno = form.save()
            notificacion = enviar_email_turno_creado(turno)
            return turno, notificacion
    except IntegrityError as exc:
        raise ReservaNoDisponible("El horario ya fue reservado.") from exc


def obtener_o_crear_cliente_online(negocio, datos_cliente):
    email = datos_cliente.get("email", "").strip().lower()
    telefono = datos_cliente.get("telefono", "").strip()
    cliente = None

    if email:
        cliente = Cliente.objects.filter(negocio=negocio, email__iexact=email).first()
    if cliente is None and telefono:
        cliente = Cliente.objects.filter(negocio=negocio, telefono=telefono).first()

    if cliente is not None:
        campos_actualizados = []
        for campo in ("nombre", "apellido"):
            valor = datos_cliente.get(campo, "").strip()
            if valor and not getattr(cliente, campo):
                setattr(cliente, campo, valor)
                campos_actualizados.append(campo)
        if email and not cliente.email:
            cliente.email = email
            campos_actualizados.append("email")
        if telefono and not cliente.telefono:
            cliente.telefono = telefono
            campos_actualizados.append("telefono")
        if campos_actualizados:
            campos_actualizados.append("actualizado_en")
            cliente.save(update_fields=campos_actualizados)
        return cliente

    nombre = datos_cliente.get("nombre", "").strip()
    apellido = datos_cliente.get("apellido", "").strip()
    return Cliente.objects.create(
        negocio=negocio,
        nombre=nombre,
        apellido=apellido,
        nombre_visible=f"{nombre} {apellido}".strip(),
        slug=_generar_slug_cliente(negocio, nombre, apellido),
        email=email,
        telefono=telefono,
    )


def email_enviado(notificacion):
    return (
        notificacion is not None
        and notificacion.estado == EstadoNotificacionEmail.ENVIADO
    )


def email_estado(notificacion):
    if notificacion is None:
        return "sin_email"
    if email_enviado(notificacion):
        return "enviado"
    return "fallido"


def _hay_reserva_duplicada_reciente(*, negocio, servicio, inicio, datos_cliente):
    minutos = getattr(settings, "RESERVA_PUBLICA_DUPLICADO_MINUTOS", 10)
    try:
        minutos = int(minutos)
    except (TypeError, ValueError):
        minutos = 10

    email = datos_cliente.get("email", "").strip().lower()
    telefono = datos_cliente.get("telefono", "").strip()
    contacto_filter = Q()
    if email:
        contacto_filter |= Q(cliente__email__iexact=email)
    if telefono:
        contacto_filter |= Q(cliente__telefono=telefono)
    if not contacto_filter:
        return False

    inicio = _ensure_aware(inicio).replace(second=0, microsecond=0)
    creado_desde = timezone.now() - timedelta(minutes=max(1, minutos))
    return (
        Turno.objects.filter(
            negocio=negocio,
            servicio=servicio,
            fecha_hora_inicio=inicio,
            origen=OrigenTurno.ONLINE,
            creado_en__gte=creado_desde,
        )
        .filter(contacto_filter)
        .exists()
    )


def _entidades_publicas_validas(*, negocio, sucursal, servicio, profesional=None):
    if not negocio_permite_reserva_online(negocio):
        return False

    if (
        sucursal is None
        or not get_sucursales_publicas(negocio).filter(pk=sucursal.pk).exists()
    ):
        return False

    if (
        servicio is None
        or not get_servicios_publicos(negocio).filter(pk=servicio.pk).exists()
    ):
        return False

    if profesional is not None:
        return get_profesionales_publicos(
            negocio,
            sucursal=sucursal,
            servicio=servicio,
        ).filter(pk=profesional.pk).exists()

    return True


def _slot_es_disponible(*, negocio, sucursal, profesional, inicio, fin, configuracion):
    if _slot_fuera_de_ventana(inicio, fin, configuracion):
        return False

    if _slot_tiene_excepcion(
        negocio=negocio,
        sucursal=sucursal,
        profesional=profesional,
        inicio=inicio,
        fin=fin,
    ):
        return False

    if _slot_tiene_solapamiento(
        profesional=profesional,
        inicio=inicio,
        fin=fin,
        configuracion=configuracion,
    ):
        return False

    return True


def _slot_fuera_de_ventana(inicio, fin, configuracion):
    inicio = _ensure_aware(inicio)
    fin = _ensure_aware(fin)
    ahora = timezone.now()

    if inicio <= ahora:
        return True

    if timezone.localtime(inicio).date() != timezone.localtime(fin).date():
        return True

    anticipacion_minima = configuracion.anticipacion_minima_reserva_minutos
    if anticipacion_minima and inicio < ahora + timedelta(minutes=anticipacion_minima):
        return True

    anticipacion_maxima = configuracion.anticipacion_maxima_reserva_dias
    if anticipacion_maxima and inicio > ahora + timedelta(days=anticipacion_maxima):
        return True

    return False


def _slot_tiene_excepcion(*, negocio, sucursal, profesional, inicio, fin):
    return ExcepcionAgenda.objects.filter(
        negocio=negocio,
        activo=True,
        bloquea_turnos=True,
        fecha_hora_inicio__lt=fin,
        fecha_hora_fin__gt=inicio,
    ).filter(
        Q(sucursal__isnull=True, profesional__isnull=True)
        | Q(sucursal=sucursal, profesional__isnull=True)
        | Q(profesional=profesional)
    ).exists()


def _slot_tiene_solapamiento(*, profesional, inicio, fin, configuracion):
    buffer_minutos = configuracion.buffer_entre_turnos_minutos or 0
    buffer_delta = timedelta(minutes=buffer_minutos)
    return Turno.objects.filter(
        profesional=profesional,
        estado__in=ESTADOS_TURNO_ACTIVOS,
        fecha_hora_inicio__lt=fin + buffer_delta,
        fecha_hora_fin__gt=inicio - buffer_delta,
    ).exists()


def _get_intervalo_slots(negocio, servicio):
    try:
        intervalo = negocio.configuracion.intervalo_turnos_minutos
    except ObjectDoesNotExist:
        intervalo = servicio.duracion_minutos or 30

    return max(1, intervalo or servicio.duracion_minutos or 30)


def _build_slot(*, inicio, fin, profesional):
    return {
        "fecha_hora_inicio": inicio,
        "fecha_hora_fin": fin,
        "profesional": profesional,
        "label_hora": timezone.localtime(inicio).strftime("%H:%M"),
        "label_fin": timezone.localtime(fin).strftime("%H:%M"),
        "value_inicio": _datetime_local_value(inicio),
    }


def _aware_datetime(fecha, hora):
    return timezone.make_aware(
        datetime.combine(fecha, hora),
        timezone.get_current_timezone(),
    )


def _ensure_aware(value):
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def _datetime_local_value(value):
    return timezone.localtime(_ensure_aware(value)).strftime("%Y-%m-%dT%H:%M")


def _generar_slug_cliente(negocio, nombre, apellido):
    base = slugify(f"{nombre} {apellido}".strip()) or "cliente"
    candidato = base
    contador = 2

    while Cliente.objects.filter(negocio=negocio, slug=candidato).exists():
        candidato = f"{base}-{contador}"
        contador += 1

    return candidato
