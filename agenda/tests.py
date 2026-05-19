from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from profesional.models import Profesional
from test_utils import (
    aware_datetime_for_date,
    create_domain,
    create_miembro,
    create_superuser,
    create_user,
    future_date,
)
from turnos.models import EstadoTurno, Turno
from usuarios.models import RolMiembroNegocio


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


class AgendaSemanalViewTests(TestCase):
    def setUp(self):
        self.superuser = create_superuser(username="agenda-semanal-root")
        self.domain = create_domain(prefix="Agenda Semanal")
        self.otro = create_domain(prefix="Agenda Semanal Otro")
        self.fecha = future_date(days=30)
        self.inicio_semana = self.fecha - timedelta(days=self.fecha.weekday())
        self.otra_fecha_semana = self.inicio_semana + timedelta(days=2)
        self.fecha_fuera_semana = self.inicio_semana + timedelta(days=7)
        self.turno = self._crear_turno(
            self.domain,
            self.fecha,
            10,
            EstadoTurno.SOLICITADO,
        )
        self.turno_otro = self._crear_turno(
            self.otro,
            self.otra_fecha_semana,
            11,
            EstadoTurno.CONFIRMADO,
        )
        self.turno_fuera_semana = self._crear_turno(
            self.domain,
            self.fecha_fuera_semana,
            10,
            EstadoTurno.SOLICITADO,
        )

    def test_requiere_login(self):
        response = self.client.get("/agenda/semanal/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/accounts/login/"))
        self.assertIn("next=/agenda/semanal/", response["Location"])

    def test_responde_200_con_usuario_autorizado(self):
        self.client.force_login(self.superuser)

        response = self.client.get("/agenda/semanal/")

        self.assertEqual(response.status_code, 200)

    def test_si_no_se_pasa_fecha_usa_semana_actual(self):
        self.client.force_login(self.superuser)
        hoy = timezone.localdate()
        inicio_semana = hoy - timedelta(days=hoy.weekday())

        response = self.client.get("/agenda/semanal/")

        self.assertEqual(response.context["fecha_seleccionada"], hoy)
        self.assertEqual(response.context["inicio_semana"], inicio_semana)
        self.assertEqual(response.context["fin_semana"], inicio_semana + timedelta(days=6))
        self.assertFalse(response.context["fecha_invalida"])

    def test_fecha_valida_calcula_semana_lunes_a_domingo(self):
        self.client.force_login(self.superuser)

        response = self.client.get("/agenda/semanal/", {"fecha": "2026-05-20"})

        self.assertEqual(response.context["fecha_seleccionada"], date(2026, 5, 20))
        self.assertEqual(response.context["inicio_semana"], date(2026, 5, 18))
        self.assertEqual(response.context["fin_semana"], date(2026, 5, 24))

    def test_fecha_invalida_no_rompe_y_vuelve_a_semana_actual(self):
        self.client.force_login(self.superuser)
        hoy = timezone.localdate()

        response = self.client.get("/agenda/semanal/", {"fecha": "fecha-rara"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["fecha_invalida"])
        self.assertEqual(response.context["fecha_seleccionada"], hoy)

    def test_filtra_por_negocio(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            "/agenda/semanal/",
            {"fecha": self.fecha.isoformat(), "negocio": self.domain.negocio.pk},
        )

        turnos = self._turnos_context(response)
        self.assertIn(self.turno, turnos)
        self.assertNotIn(self.turno_otro, turnos)
        self.assertNotIn(self.turno_fuera_semana, turnos)

    def test_filtra_por_sucursal(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            "/agenda/semanal/",
            {"fecha": self.fecha.isoformat(), "sucursal": self.otro.sucursal.pk},
        )

        turnos = self._turnos_context(response)
        self.assertEqual(turnos, [self.turno_otro])

    def test_filtra_por_profesional(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            "/agenda/semanal/",
            {"fecha": self.fecha.isoformat(), "profesional": self.domain.profesional.pk},
        )

        turnos = self._turnos_context(response)
        self.assertEqual(turnos, [self.turno])

    def test_filtra_por_estado(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            "/agenda/semanal/",
            {"fecha": self.fecha.isoformat(), "estado": EstadoTurno.CONFIRMADO},
        )

        turnos = self._turnos_context(response)
        self.assertEqual(turnos, [self.turno_otro])

    def test_profesional_ve_solo_sus_turnos(self):
        profesional_user = create_user(username="agenda-semanal-profesional")
        otro_profesional = Profesional.objects.create(
            negocio=self.domain.negocio,
            nombre="Otro",
            apellido="Profesional",
        )
        otro_profesional.sucursales.add(self.domain.sucursal)
        otro_profesional.servicios.add(self.domain.servicio)
        turno_otro_profesional = self._crear_turno(
            self.domain,
            self.otra_fecha_semana,
            12,
            EstadoTurno.SOLICITADO,
            profesional=otro_profesional,
        )
        create_miembro(
            profesional_user,
            self.domain.negocio,
            rol=RolMiembroNegocio.PROFESIONAL,
            profesional=self.domain.profesional,
        )
        self.client.force_login(profesional_user)

        response = self.client.get("/agenda/semanal/", {"fecha": self.fecha.isoformat()})

        turnos = self._turnos_context(response)
        self.assertIn(self.turno, turnos)
        self.assertNotIn(turno_otro_profesional, turnos)
        self.assertNotIn(self.turno_otro, turnos)

    def test_usuario_sin_membresia_no_ve_datos_operativos(self):
        user = create_user(username="agenda-semanal-sin-membresia")
        self.client.force_login(user)

        response = self.client.get("/agenda/semanal/", {"fecha": self.fecha.isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._turnos_context(response), [])
        self.assertFalse(response.context["hay_negocios"])

    def test_link_de_detalle_existe_para_turno_visible(self):
        self.client.force_login(self.superuser)

        response = self.client.get("/agenda/semanal/", {"fecha": self.fecha.isoformat()})

        self.assertContains(
            response,
            reverse("turnos:detalle", kwargs={"pk": self.turno.pk}),
        )

    def _turnos_context(self, response):
        return [
            turno
            for dia in response.context["dias_semana"]
            for turno in dia["turnos"]
        ]

    def _crear_turno(self, domain, date_value, hour, estado, *, profesional=None):
        inicio = aware_datetime_for_date(date_value, hour, 0)
        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=profesional or domain.profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=domain.servicio.duracion_minutos),
            estado=estado,
        )
