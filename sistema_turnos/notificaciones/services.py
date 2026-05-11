from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EstadoNotificacionEmail, NotificacionEmail, TipoNotificacionEmail


def enviar_email_turno_creado(turno):
    return _enviar_email_turno(
        turno,
        tipo=TipoNotificacionEmail.TURNO_CREADO,
        asunto=f"Turno creado - {turno.negocio.nombre}",
        template_base="turno_creado",
    )


def enviar_email_turno_confirmado(turno):
    return _enviar_email_turno(
        turno,
        tipo=TipoNotificacionEmail.TURNO_CONFIRMADO,
        asunto=f"Turno confirmado - {turno.negocio.nombre}",
        template_base="turno_confirmado",
    )


def enviar_email_turno_cancelado(turno, motivo=None):
    contexto_extra = {"motivo_cancelacion": motivo or turno.motivo_cancelacion}
    return _enviar_email_turno(
        turno,
        tipo=TipoNotificacionEmail.TURNO_CANCELADO,
        asunto=f"Turno cancelado - {turno.negocio.nombre}",
        template_base="turno_cancelado",
        contexto_extra=contexto_extra,
    )


def enviar_email_turno_completado(turno):
    return _enviar_email_turno(
        turno,
        tipo=TipoNotificacionEmail.TURNO_COMPLETADO,
        asunto=f"Turno completado - {turno.negocio.nombre}",
        template_base="turno_completado",
    )


def enviar_email_turno_ausente(turno):
    return _enviar_email_turno(
        turno,
        tipo=TipoNotificacionEmail.TURNO_AUSENTE,
        asunto=f"Ausencia registrada - {turno.negocio.nombre}",
        template_base="turno_ausente",
    )


def enviar_notificacion_email(
    *,
    destinatario_email,
    destinatario_nombre="",
    tipo,
    asunto,
    template_base,
    contexto,
    negocio=None,
    turno=None,
):
    if not destinatario_email:
        return None

    notificacion = NotificacionEmail.objects.create(
        negocio=negocio,
        turno=turno,
        destinatario_email=destinatario_email,
        destinatario_nombre=destinatario_nombre,
        tipo=tipo,
        asunto=asunto,
    )

    try:
        texto = render_to_string(
            f"notificaciones/emails/{template_base}.txt",
            contexto,
        )
        html = render_to_string(
            f"notificaciones/emails/{template_base}.html",
            contexto,
        )
        email = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario_email],
        )
        email.attach_alternative(html, "text/html")
        enviados = email.send(fail_silently=False)
        if enviados:
            notificacion.estado = EstadoNotificacionEmail.ENVIADO
            notificacion.enviado_en = timezone.now()
            notificacion.mensaje_error = ""
        else:
            notificacion.estado = EstadoNotificacionEmail.FALLIDO
            notificacion.mensaje_error = "El backend de email no envio el mensaje."
    except Exception as exc:
        notificacion.estado = EstadoNotificacionEmail.FALLIDO
        notificacion.mensaje_error = str(exc)

    notificacion.save(
        update_fields=[
            "estado",
            "mensaje_error",
            "enviado_en",
            "actualizado_en",
        ]
    )
    return notificacion


def _enviar_email_turno(turno, *, tipo, asunto, template_base, contexto_extra=None):
    destinatario_email = turno.cliente.email.strip()
    if not destinatario_email:
        return None

    contexto = _get_contexto_turno(turno)
    contexto.update(contexto_extra or {})
    return enviar_notificacion_email(
        negocio=turno.negocio,
        turno=turno,
        destinatario_email=destinatario_email,
        destinatario_nombre=turno.cliente.nombre_visible,
        tipo=tipo,
        asunto=asunto,
        template_base=template_base,
        contexto=contexto,
    )


def _get_contexto_turno(turno):
    return {
        "turno": turno,
        "cliente": turno.cliente,
        "cliente_nombre": turno.cliente.nombre_visible,
        "negocio": turno.negocio,
        "negocio_nombre": turno.negocio.nombre,
        "servicio": turno.servicio,
        "profesional": turno.profesional,
        "sucursal": turno.sucursal,
        "fecha_hora": timezone.localtime(turno.fecha_hora_inicio),
        "fecha_hora_fin": timezone.localtime(turno.fecha_hora_fin),
        "estado": turno.get_estado_display(),
        "telefono_contacto": _get_telefono_contacto(turno),
        "whatsapp_contacto": _get_whatsapp_contacto(turno),
    }


def _get_telefono_contacto(turno):
    return turno.sucursal.telefono or turno.negocio.telefono_principal


def _get_whatsapp_contacto(turno):
    return turno.sucursal.whatsapp or turno.negocio.whatsapp_principal
