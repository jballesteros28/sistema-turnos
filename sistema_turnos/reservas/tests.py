from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from clientes.models import Cliente
from configuracion_negocio.models import ConfiguracionNegocio, PoliticaConfirmacion
from excepcion.models import ExcepcionAgenda, TipoExcepcion
from negocio.models import EstadoNegocio
from notificaciones.models import EstadoNotificacionEmail, NotificacionEmail
from profesional.models import Profesional
from servicio.models import EstadoServicio
from test_utils import (
    aware_datetime_for_date,
    create_availability,
    create_domain,
    create_miembro,
    create_user,
    datetime_local_value,
    future_date,
)
from turnos.models import EstadoTurno, OrigenTurno, Turno
from usuarios.models import RolMiembroNegocio

from .forms import SeleccionTurnoForm
from .services import calcular_slots_disponibles


class ReservaPublicaOnlineTests(TestCase):
    def setUp(self):
        self.domain = create_domain(
            prefix="Reserva Publica",
            servicio_kwargs={"duracion_minutos": 60},
        )
        ConfiguracionNegocio.objects.create(
            negocio=self.domain.negocio,
            politica_confirmacion=PoliticaConfirmacion.MANUAL,
            anticipacion_minima_reserva_minutos=0,
            anticipacion_maxima_reserva_dias=60,
            intervalo_turnos_minutos=30,
        )
        self.fecha = self._fecha_con_weekday(2)
        self.inicio = aware_datetime_for_date(self.fecha, 9, 0)
        create_availability(
            self.domain,
            date_value=self.fecha,
            dias_semana=[0, 1, 2, 3, 4],
        )

    def test_pagina_publica_de_negocio_activo_responde_200(self):
        response = self.client.get(self._url_publica())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.domain.negocio.nombre_visible)

    def test_negocio_inactivo_no_permite_reserva(self):
        self.domain.negocio.estado = EstadoNegocio.INACTIVO
        self.domain.negocio.save(update_fields=["estado", "actualizado_en"])

        response = self.client.get(self._url_publica())

        self.assertEqual(response.status_code, 404)

    def test_seleccion_de_turno_muestra_slots_validos(self):
        response = self.client.get(self._url_turno(), self._seleccion_params())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "09:00")
        self.assertTrue(response.context["slots"])

    def test_disponibilidad_lunes_a_viernes_permite_slot_miercoles(self):
        slots = self._slots(self.fecha)

        self.assertTrue(self._contiene_hora(slots, "09:00"))

    def test_disponibilidad_lunes_a_viernes_no_permite_slot_sabado(self):
        sabado = self._fecha_con_weekday(5)

        slots = self._slots(sabado)

        self.assertEqual(slots, [])

    def test_slots_bloqueados_por_excepcion_no_aparecen(self):
        ExcepcionAgenda.objects.create(
            negocio=self.domain.negocio,
            tipo=TipoExcepcion.CIERRE_NEGOCIO,
            titulo="Cierre",
            fecha_hora_inicio=self.inicio,
            fecha_hora_fin=self.inicio + timedelta(hours=2),
        )

        slots = self._slots(self.fecha)

        self.assertFalse(self._contiene_hora(slots, "09:00"))

    def test_slots_ocupados_por_turno_activo_no_aparecen(self):
        self._crear_turno(self.inicio, estado=EstadoTurno.CONFIRMADO)

        slots = self._slots(self.fecha)

        self.assertFalse(self._contiene_hora(slots, "09:00"))

    def test_servicio_inactivo_no_aparece(self):
        self.domain.servicio.estado = EstadoServicio.INACTIVO
        self.domain.servicio.save(update_fields=["estado", "actualizado_en"])

        form = SeleccionTurnoForm(self.domain.negocio)

        self.assertNotIn(self.domain.servicio, form.fields["servicio"].queryset)

    def test_profesional_no_visible_online_no_aparece(self):
        self.domain.profesional.visible_en_reserva_online = False
        self.domain.profesional.save(
            update_fields=["visible_en_reserva_online", "actualizado_en"],
        )

        form = SeleccionTurnoForm(
            self.domain.negocio,
            data=self._seleccion_params(),
        )

        self.assertNotIn(self.domain.profesional, form.fields["profesional"].queryset)

    def test_profesional_no_asociado_a_sucursal_no_aparece(self):
        profesional = Profesional.objects.create(
            negocio=self.domain.negocio,
            nombre="Sin",
            apellido="Sucursal",
        )
        profesional.servicios.add(self.domain.servicio)

        form = SeleccionTurnoForm(
            self.domain.negocio,
            data=self._seleccion_params(),
        )

        self.assertNotIn(profesional, form.fields["profesional"].queryset)

    def test_confirmar_reserva_crea_cliente_si_no_existe(self):
        self._post_reserva(email="nuevo@example.test")

        self.assertTrue(
            Cliente.objects.filter(
                negocio=self.domain.negocio,
                email="nuevo@example.test",
            ).exists()
        )

    def test_confirmar_reserva_reutiliza_cliente_existente(self):
        cliente = Cliente.objects.create(
            negocio=self.domain.negocio,
            nombre="Cliente",
            apellido="Existente",
            email="existente@example.test",
        )

        self._post_reserva(email="existente@example.test")

        self.assertEqual(
            Cliente.objects.filter(
                negocio=self.domain.negocio,
                email="existente@example.test",
            ).count(),
            1,
        )
        self.assertEqual(Turno.objects.get().cliente, cliente)

    def test_confirmar_reserva_crea_turno_online(self):
        response = self._post_reserva(email="online@example.test")
        turno = Turno.objects.get()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(turno.origen, OrigenTurno.ONLINE)
        self.assertEqual(turno.estado, EstadoTurno.SOLICITADO)

    def test_formulario_publico_rechaza_honeypot_completo(self):
        response = self._post_reserva(
            email="bot@example.test",
            extra={"website": "https://spam.example.test"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pudimos procesar la reserva")
        self.assertEqual(Turno.objects.count(), 0)
        self.assertFalse(
            Cliente.objects.filter(
                negocio=self.domain.negocio,
                email="bot@example.test",
            ).exists()
        )

    def test_reserva_publica_duplicada_reciente_se_bloquea(self):
        primera = self._post_reserva(email="duplicada@example.test")
        segunda = self._post_reserva(email="duplicada@example.test")

        self.assertEqual(primera.status_code, 302)
        self.assertEqual(segunda.status_code, 200)
        self.assertContains(segunda, "Ya recibimos una reserva igual")
        self.assertEqual(Turno.objects.count(), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_confirmar_reserva_envia_email(self):
        self._post_reserva(email="mail@example.test")

        notificacion = NotificacionEmail.objects.get()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(notificacion.estado, EstadoNotificacionEmail.ENVIADO)

    def test_si_envio_falla_reserva_publica_no_se_rompe_y_avisa(self):
        with patch(
            "notificaciones.services.EmailMultiAlternatives.send",
            side_effect=RuntimeError("SMTP caido"),
        ):
            response = self._post_reserva(email="fallo-email@example.test")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Turno.objects.count(), 1)
        notificacion = NotificacionEmail.objects.get()
        self.assertEqual(notificacion.estado, EstadoNotificacionEmail.FALLIDO)
        self.assertIn("SMTP caido", notificacion.mensaje_error)

        response = self.client.get(response["Location"])
        self.assertContains(
            response,
            "La reserva fue creada, pero no pudimos enviar el email de confirmacion.",
        )

    def test_si_slot_deja_de_estar_disponible_no_crea_turno(self):
        self._crear_turno(self.inicio, estado=EstadoTurno.SOLICITADO)

        response = self._post_reserva(email="tarde@example.test")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Turno.objects.count(), 1)
        self.assertFalse(
            Cliente.objects.filter(
                negocio=self.domain.negocio,
                email="tarde@example.test",
            ).exists()
        )

    def test_pagina_publica_no_requiere_login(self):
        response = self.client.get(self._url_turno())

        self.assertEqual(response.status_code, 200)

    def test_link_publico_aparece_en_detalle_de_negocio_para_usuario_autorizado(self):
        user = create_user(username="admin-reserva")
        create_miembro(
            user,
            self.domain.negocio,
            rol=RolMiembroNegocio.ADMIN_NEGOCIO,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("negocios:detalle", kwargs={"pk": self.domain.negocio.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self._url_publica())
        self.assertContains(response, "Copiar link de reserva")

    def test_backoffice_sigue_requiriendo_login(self):
        for path in ("/dashboard/", "/turnos/", "/agenda/turnos/"):
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith("/accounts/login/"))

    def _url_publica(self):
        return reverse(
            "reservas:negocio_publico",
            kwargs={"negocio_slug": self.domain.negocio.slug},
        )

    def _url_turno(self):
        return reverse(
            "reservas:seleccionar_turno",
            kwargs={"negocio_slug": self.domain.negocio.slug},
        )

    def _url_confirmar(self):
        return reverse(
            "reservas:confirmar_reserva",
            kwargs={"negocio_slug": self.domain.negocio.slug},
        )

    def _seleccion_params(self, fecha=None):
        return {
            "sucursal": self.domain.sucursal.pk,
            "servicio": self.domain.servicio.pk,
            "fecha": (fecha or self.fecha).isoformat(),
        }

    def _post_reserva(self, *, email, extra=None):
        data = {
            "sucursal": self.domain.sucursal.pk,
            "servicio": self.domain.servicio.pk,
            "profesional": self.domain.profesional.pk,
            "inicio": datetime_local_value(self.inicio),
            "nombre": "Ana",
            "apellido": "Reserva",
            "email": email,
            "telefono": "3515551234",
            "observaciones": "Prefiere puntualidad",
        }
        data.update(extra or {})
        return self.client.post(self._url_confirmar(), data)

    def _slots(self, fecha):
        return calcular_slots_disponibles(
            negocio=self.domain.negocio,
            sucursal=self.domain.sucursal,
            servicio=self.domain.servicio,
            fecha=fecha,
            profesional=self.domain.profesional,
        )

    def _contiene_hora(self, slots, label_hora):
        return any(slot["label_hora"] == label_hora for slot in slots)

    def _crear_turno(self, inicio, *, estado):
        return Turno.objects.create(
            negocio=self.domain.negocio,
            sucursal=self.domain.sucursal,
            cliente=self.domain.cliente,
            profesional=self.domain.profesional,
            servicio=self.domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=self.domain.servicio.duracion_minutos),
            estado=estado,
        )

    def _fecha_con_weekday(self, weekday):
        fecha = future_date(days=10)
        while fecha.weekday() != weekday:
            fecha += timedelta(days=1)
        return fecha
