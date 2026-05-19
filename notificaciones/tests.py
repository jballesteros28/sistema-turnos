from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from configuracion_negocio.models import ConfiguracionNegocio, PoliticaConfirmacion
from notificaciones.models import (
    EstadoNotificacionEmail,
    NotificacionEmail,
    TipoNotificacionEmail,
)
from notificaciones.services import enviar_email_turno_creado
from test_utils import (
    aware_datetime_for_date,
    create_availability,
    create_domain,
    create_miembro,
    create_user,
    future_date,
    turno_form_data,
)
from turnos.models import EstadoTurno, Turno
from usuarios.models import RolMiembroNegocio


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificacionesEmailTurnoTests(TestCase):
    def setUp(self):
        self.user = create_user(username="notificaciones")

    def test_crear_turno_con_cliente_email_envia_notificacion(self):
        domain, inicio = self._domain_con_permiso(prefix="Email Crear")

        response = self.client.post(
            reverse("turnos:crear"),
            turno_form_data(domain, inicio=inicio),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        notificacion = NotificacionEmail.objects.get()
        self.assertEqual(notificacion.estado, EstadoNotificacionEmail.ENVIADO)
        self.assertEqual(notificacion.tipo, TipoNotificacionEmail.TURNO_CREADO)
        self.assertIn(domain.negocio.nombre, notificacion.asunto)
        self.assertIn("Turno creado", mail.outbox[0].subject)
        self.assertIn(domain.cliente.nombre_visible, mail.outbox[0].body)
        self.assertIn(domain.servicio.nombre, mail.outbox[0].body)
        self.assertIn(domain.profesional.nombre_visible, mail.outbox[0].body)
        self.assertIn(inicio.strftime("%d/%m/%Y"), mail.outbox[0].body)

    def test_crear_turno_con_cliente_sin_email_no_rompe_ni_crea_notificacion(self):
        domain, inicio = self._domain_con_permiso(
            prefix="Email Sin Cliente",
            cliente_kwargs={"email": ""},
        )

        response = self.client.post(
            reverse("turnos:crear"),
            turno_form_data(domain, inicio=inicio),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(NotificacionEmail.objects.count(), 0)

    def test_confirmar_turno_envia_email(self):
        domain, inicio = self._domain_con_permiso(prefix="Email Confirmar")
        turno = self._crear_turno(domain, inicio)

        response = self.client.post(reverse("turnos:confirmar", kwargs={"pk": turno.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        notificacion = NotificacionEmail.objects.get()
        self.assertEqual(notificacion.tipo, TipoNotificacionEmail.TURNO_CONFIRMADO)
        self.assertEqual(notificacion.estado, EstadoNotificacionEmail.ENVIADO)

    def test_cancelar_turno_envia_email(self):
        domain, inicio = self._domain_con_permiso(prefix="Email Cancelar")
        ConfiguracionNegocio.objects.create(
            negocio=domain.negocio,
            permite_cancelacion_online=True,
            tiempo_minimo_cancelacion_minutos=0,
        )
        turno = self._crear_turno(domain, inicio)

        response = self.client.post(
            reverse("turnos:cancelar", kwargs={"pk": turno.pk}),
            {"motivo_cancelacion": "Cambio de agenda"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        notificacion = NotificacionEmail.objects.get()
        self.assertEqual(notificacion.tipo, TipoNotificacionEmail.TURNO_CANCELADO)
        self.assertEqual(notificacion.estado, EstadoNotificacionEmail.ENVIADO)
        self.assertIn("Cambio de agenda", mail.outbox[0].body)

    def test_si_envio_falla_notificacion_queda_fallida(self):
        domain, inicio = self._domain_con_permiso(prefix="Email Falla")
        turno = self._crear_turno(domain, inicio)

        with patch(
            "notificaciones.services.EmailMultiAlternatives.send",
            side_effect=RuntimeError("SMTP caido"),
        ):
            notificacion = enviar_email_turno_creado(turno)

        self.assertIsNotNone(notificacion)
        notificacion.refresh_from_db()
        self.assertEqual(notificacion.estado, EstadoNotificacionEmail.FALLIDO)
        self.assertIn("SMTP caido", notificacion.mensaje_error)

    def test_confirmacion_automatica_no_duplica_emails_al_crear(self):
        domain, inicio = self._domain_con_permiso(prefix="Email Auto")
        ConfiguracionNegocio.objects.create(
            negocio=domain.negocio,
            politica_confirmacion=PoliticaConfirmacion.AUTOMATICA,
            anticipacion_minima_reserva_minutos=0,
            tiempo_minimo_cancelacion_minutos=0,
        )

        response = self.client.post(
            reverse("turnos:crear"),
            turno_form_data(domain, inicio=inicio),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(NotificacionEmail.objects.count(), 1)
        turno = Turno.objects.get(negocio=domain.negocio)
        self.assertEqual(turno.estado, EstadoTurno.CONFIRMADO)
        self.assertIn("Confirmado", mail.outbox[0].body)

    def test_usuario_sin_permiso_no_dispara_email(self):
        domain = create_domain(
            prefix="Email Permiso",
            cliente_kwargs={"email": "cliente-permiso@example.test"},
        )
        fecha = future_date(days=14)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("turnos:crear"),
            turno_form_data(domain, inicio=inicio),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(NotificacionEmail.objects.count(), 0)

    def _domain_con_permiso(self, *, prefix, cliente_kwargs=None):
        cliente_data = {"email": "cliente@example.test"}
        cliente_data.update(cliente_kwargs or {})
        domain = create_domain(prefix=prefix, cliente_kwargs=cliente_data)
        create_miembro(
            self.user,
            domain.negocio,
            rol=RolMiembroNegocio.ADMIN_NEGOCIO,
        )
        self.client.force_login(self.user)
        fecha = future_date(days=12)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)
        return domain, inicio

    def _crear_turno(self, domain, inicio):
        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=domain.profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=domain.servicio.duracion_minutos),
            estado=EstadoTurno.SOLICITADO,
        )


class ProbarEmailCommandTests(TestCase):
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="no-reply@sistema-turnos.local",
    )
    def test_probar_email_envia_mensaje_con_backend_configurado(self):
        salida = StringIO()

        call_command("probar_email", "destino@example.test", stdout=salida)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Prueba de email - Sistema de Turnos", mail.outbox[0].subject)
        self.assertIn("Email de prueba enviado correctamente", salida.getvalue())
