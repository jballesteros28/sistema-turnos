from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from test_utils import create_domain, create_superuser, aware_datetime_for_date, future_date
from turnos.models import EstadoTurno, Turno


class AgendaDiariaViewTests(TestCase):
    def setUp(self):
        self.client.force_login(create_superuser())
        self.domain = create_domain(prefix="Agenda")
        self.otro = create_domain(prefix="Agenda Otro")
        self.fecha = future_date(days=30)
        self.otra_fecha = self.fecha + timedelta(days=1)
        self.turno = self._crear_turno(self.domain, self.fecha, 10, EstadoTurno.SOLICITADO)
        self.turno_otro = self._crear_turno(
            self.otro,
            self.fecha,
            11,
            EstadoTurno.CONFIRMADO,
        )
        self.turno_otra_fecha = self._crear_turno(
            self.domain,
            self.otra_fecha,
            10,
            EstadoTurno.SOLICITADO,
        )

    def test_responde_200(self):
        response = self.client.get("/agenda/turnos/")

        self.assertEqual(response.status_code, 200)

    def test_si_no_se_pasa_fecha_usa_el_dia_actual(self):
        response = self.client.get("/agenda/turnos/")

        self.assertEqual(response.context["fecha_seleccionada"], timezone.localdate())
        self.assertEqual(response.context["fecha_actual"], timezone.localdate().isoformat())
        self.assertFalse(response.context["fecha_invalida"])

    def test_filtra_por_fecha_valida(self):
        response = self.client.get("/agenda/turnos/", {"fecha": self.fecha.isoformat()})

        turnos = list(response.context["turnos"])
        self.assertIn(self.turno, turnos)
        self.assertIn(self.turno_otro, turnos)
        self.assertNotIn(self.turno_otra_fecha, turnos)

    def test_fecha_invalida_no_rompe_y_vuelve_al_dia_actual(self):
        response = self.client.get("/agenda/turnos/", {"fecha": "fecha-rara"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["fecha_invalida"])
        self.assertEqual(response.context["fecha_seleccionada"], timezone.localdate())

    def test_filtra_por_negocio(self):
        response = self.client.get(
            "/agenda/turnos/",
            {"fecha": self.fecha.isoformat(), "negocio": self.domain.negocio.pk},
        )

        turnos = list(response.context["turnos"])
        self.assertEqual(turnos, [self.turno])

    def test_filtra_por_sucursal(self):
        response = self.client.get(
            "/agenda/turnos/",
            {"fecha": self.fecha.isoformat(), "sucursal": self.otro.sucursal.pk},
        )

        turnos = list(response.context["turnos"])
        self.assertEqual(turnos, [self.turno_otro])

    def test_filtra_por_profesional(self):
        response = self.client.get(
            "/agenda/turnos/",
            {"fecha": self.fecha.isoformat(), "profesional": self.domain.profesional.pk},
        )

        turnos = list(response.context["turnos"])
        self.assertEqual(turnos, [self.turno])

    def test_filtra_por_estado(self):
        response = self.client.get(
            "/agenda/turnos/",
            {"fecha": self.fecha.isoformat(), "estado": EstadoTurno.CONFIRMADO},
        )

        turnos = list(response.context["turnos"])
        self.assertEqual(turnos, [self.turno_otro])

    def test_no_rompe_si_no_hay_turnos(self):
        Turno.objects.all().delete()

        response = self.client.get("/agenda/turnos/", {"fecha": self.fecha.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["turnos"]), [])

    def _crear_turno(self, domain, date_value, hour, estado):
        inicio = aware_datetime_for_date(date_value, hour, 0)
        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=domain.profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=domain.servicio.duracion_minutos),
            estado=estado,
        )
