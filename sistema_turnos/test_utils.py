from datetime import datetime, time, timedelta
from itertools import count
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.utils import timezone

from clientes.models import Cliente
from disponibilidad.models import Disponibilidad
from negocio.models import Negocio
from profesional.models import Profesional
from servicio.models import Servicio
from sucursal.models import Sucursal
from usuarios.models import MiembroNegocio, RolMiembroNegocio


_sequence = count(1)
TEST_PASSWORD = "clave-segura-123"


def create_user(*, username=None, password=TEST_PASSWORD, **kwargs):
    suffix = next(_sequence)
    if username is None:
        username = f"usuario{suffix}"

    data = {
        "username": username,
        "email": f"{username}@example.test",
    }
    data.update(kwargs)
    return get_user_model().objects.create_user(password=password, **data)


def create_superuser(*, username=None, password=TEST_PASSWORD, **kwargs):
    suffix = next(_sequence)
    if username is None:
        username = f"superusuario{suffix}"

    data = {
        "username": username,
        "email": f"{username}@example.test",
    }
    data.update(kwargs)
    return get_user_model().objects.create_superuser(password=password, **data)


def create_miembro(
    user,
    negocio,
    *,
    rol=RolMiembroNegocio.ADMIN_NEGOCIO,
    profesional=None,
    activo=True,
):
    return MiembroNegocio.objects.create(
        user=user,
        negocio=negocio,
        rol=rol,
        profesional=profesional,
        activo=activo,
    )


def create_domain(
    *,
    prefix="Test",
    negocio_kwargs=None,
    sucursal_kwargs=None,
    cliente_kwargs=None,
    servicio_kwargs=None,
    profesional_kwargs=None,
    link_profesional=True,
):
    suffix = next(_sequence)

    negocio_data = {
        "nombre": f"{prefix} Negocio {suffix}",
        "email_principal": f"negocio{suffix}@example.test",
        "telefono_principal": f"1000{suffix}",
        "ciudad": "Cordoba",
        "pais": "Argentina",
    }
    negocio_data.update(negocio_kwargs or {})
    negocio = Negocio.objects.create(**negocio_data)

    sucursal_data = {
        "negocio": negocio,
        "nombre": f"{prefix} Sucursal {suffix}",
        "direccion": "Av. Siempre Viva 123",
        "ciudad": "Cordoba",
        "pais": "Argentina",
    }
    sucursal_data.update(sucursal_kwargs or {})
    sucursal = Sucursal.objects.create(**sucursal_data)

    cliente_data = {
        "negocio": negocio,
        "nombre": f"Cliente {suffix}",
        "apellido": "Prueba",
        "telefono": f"2000{suffix}",
    }
    cliente_data.update(cliente_kwargs or {})
    cliente = Cliente.objects.create(**cliente_data)

    servicio_data = {
        "negocio": negocio,
        "nombre": f"Servicio {suffix}",
        "duracion_minutos": 60,
        "precio": 1000,
    }
    servicio_data.update(servicio_kwargs or {})
    servicio = Servicio.objects.create(**servicio_data)

    profesional_data = {
        "negocio": negocio,
        "nombre": f"Profesional {suffix}",
        "apellido": "Prueba",
    }
    profesional_data.update(profesional_kwargs or {})
    profesional = Profesional.objects.create(**profesional_data)

    if link_profesional:
        profesional.sucursales.add(sucursal)
        profesional.servicios.add(servicio)

    return SimpleNamespace(
        negocio=negocio,
        sucursal=sucursal,
        cliente=cliente,
        servicio=servicio,
        profesional=profesional,
    )


def future_date(days=7):
    return timezone.localdate() + timedelta(days=days)


def aware_datetime_for_date(date_value, hour=10, minute=0):
    current_timezone = timezone.get_current_timezone()
    return timezone.make_aware(
        datetime.combine(date_value, time(hour, minute)),
        current_timezone,
    )


def future_datetime(days=7, hour=10, minute=0):
    return aware_datetime_for_date(future_date(days), hour, minute)


def datetime_local_value(value):
    return timezone.localtime(value).strftime("%Y-%m-%dT%H:%M")


def time_value(value):
    return value.strftime("%H:%M")


def create_availability(domain, *, date_value=None, start=time(9, 0), end=time(18, 0), **kwargs):
    if date_value is None:
        date_value = future_date()

    data = {
        "negocio": domain.negocio,
        "sucursal": domain.sucursal,
        "profesional": domain.profesional,
        "dia_semana": date_value.weekday(),
        "hora_inicio": start,
        "hora_fin": end,
    }
    data.update(kwargs)
    return Disponibilidad.objects.create(**data)


def disponibilidad_form_data(
    domain,
    *,
    dia_semana=None,
    hora_inicio=time(9, 0),
    hora_fin=time(18, 0),
    fecha_desde="",
    fecha_hasta="",
    activo=True,
):
    if dia_semana is None:
        dia_semana = future_date().weekday()

    return {
        "negocio": domain.negocio.pk,
        "sucursal": domain.sucursal.pk,
        "profesional": domain.profesional.pk,
        "dia_semana": dia_semana,
        "hora_inicio": time_value(hora_inicio),
        "hora_fin": time_value(hora_fin),
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "activo": "on" if activo else "",
    }


def excepcion_form_data(
    domain,
    *,
    tipo,
    titulo="Bloqueo",
    inicio=None,
    fin=None,
    sucursal=None,
    profesional=None,
    bloquea_turnos=True,
    activo=True,
):
    if inicio is None:
        inicio = future_datetime(hour=12)
    if fin is None:
        fin = inicio + timedelta(hours=1)

    return {
        "negocio": domain.negocio.pk,
        "sucursal": "" if sucursal is None else sucursal.pk,
        "profesional": "" if profesional is None else profesional.pk,
        "tipo": tipo,
        "titulo": titulo,
        "descripcion": "",
        "fecha_hora_inicio": datetime_local_value(inicio),
        "fecha_hora_fin": datetime_local_value(fin),
        "bloquea_turnos": "on" if bloquea_turnos else "",
        "activo": "on" if activo else "",
    }


def turno_form_data(
    domain,
    *,
    inicio=None,
    negocio=None,
    sucursal=None,
    cliente=None,
    profesional=None,
    servicio=None,
    origen="admin",
    notas="",
):
    if inicio is None:
        inicio = future_datetime()

    return {
        "negocio": (negocio or domain.negocio).pk,
        "sucursal": (sucursal or domain.sucursal).pk,
        "cliente": (cliente or domain.cliente).pk,
        "profesional": (profesional or domain.profesional).pk,
        "servicio": (servicio or domain.servicio).pk,
        "fecha_hora_inicio": datetime_local_value(inicio),
        "origen": origen,
        "notas": notas,
    }
