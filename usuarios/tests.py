from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from configuracion_negocio.models import ConfiguracionNegocio
from profesional.models import Profesional
from test_utils import (
    TEST_PASSWORD,
    aware_datetime_for_date,
    create_domain,
    create_miembro,
    create_superuser,
    create_user,
    future_date,
    turno_form_data,
)
from turnos.forms import TurnoForm
from turnos.models import EstadoTurno, Turno

from .models import MiembroNegocio, RolMiembroNegocio


class AutenticacionPermisosTests(TestCase):
    def setUp(self):
        self.domain_a = create_domain(prefix="Permisos A")
        self.domain_b = create_domain(prefix="Permisos B")
        self.fecha = future_date(days=40)
        self.turno_a = self._crear_turno(self.domain_a, 10)
        self.turno_b = self._crear_turno(self.domain_b, 11)

    def test_anonimo_redirige_a_login_en_vistas_internas(self):
        for path in ("/dashboard/", "/turnos/", "/agenda/turnos/"):
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith("/accounts/login/"))
                self.assertIn(f"next={path}", response["Location"])

    def test_login_funciona(self):
        create_user(username="login-ok")

        response = self.client.post(
            "/accounts/login/",
            {"username": "login-ok", "password": TEST_PASSWORD},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dashboard/")

    def test_miembro_negocio_se_crea_correctamente(self):
        user = create_user(username="miembro")

        miembro = create_miembro(
            user,
            self.domain_a.negocio,
            rol=RolMiembroNegocio.ADMIN_NEGOCIO,
        )

        self.assertEqual(miembro.user, user)
        self.assertEqual(miembro.negocio, self.domain_a.negocio)
        self.assertEqual(miembro.rol, RolMiembroNegocio.ADMIN_NEGOCIO)
        self.assertTrue(miembro.activo)

    def test_usuario_con_negocio_a_ve_a_y_no_ve_b(self):
        user = self._login_con_membresia(self.domain_a)

        response = self.client.get(reverse("negocios:lista"))

        negocios = list(response.context["negocios"])
        self.assertIn(self.domain_a.negocio, negocios)
        self.assertNotIn(self.domain_b.negocio, negocios)
        self.assertEqual(user.membresias_negocio.count(), 1)

    def test_usuario_con_negocio_a_no_ve_turnos_de_negocio_b(self):
        self._login_con_membresia(self.domain_a)

        response = self.client.get(reverse("turnos:lista"))

        turnos = list(response.context["turnos"])
        self.assertNotIn(self.turno_b, turnos)

    def test_dashboard_filtra_por_negocios_permitidos(self):
        self._login_con_membresia(self.domain_a)

        response = self.client.get(reverse("core:dashboard"))

        metricas = {
            card["label"]: card["value"] for card in response.context["metric_cards"]
        }
        self.assertEqual(metricas["Negocios activos"], 1)
        self.assertEqual(metricas["Turnos solicitados"], 1)

    def test_turnos_list_filtra_por_negocios_permitidos(self):
        self._login_con_membresia(self.domain_a)

        response = self.client.get(reverse("turnos:lista"))

        turnos = list(response.context["turnos"])
        self.assertIn(self.turno_a, turnos)
        self.assertNotIn(self.turno_b, turnos)

    def test_agenda_diaria_filtra_por_negocios_permitidos(self):
        self._login_con_membresia(self.domain_a)

        response = self.client.get(
            reverse("agenda:turnos"),
            {"fecha": self.fecha.isoformat()},
        )

        turnos = list(response.context["turnos"])
        self.assertEqual(turnos, [self.turno_a])

    def test_formulario_turno_no_permite_entidades_de_otro_negocio(self):
        user = self._login_con_membresia(self.domain_a)
        data = turno_form_data(
            self.domain_a,
            inicio=aware_datetime_for_date(self.fecha, 12, 0),
            sucursal=self.domain_b.sucursal,
        )

        form = TurnoForm(data=data, user=user)

        self.assertFalse(form.is_valid())
        self.assertIn("sucursal", form.errors)

    def test_acceso_directo_a_detalle_de_otro_negocio_devuelve_404(self):
        self._login_con_membresia(self.domain_a)

        response = self.client.get(
            reverse("turnos:detalle", kwargs={"pk": self.turno_b.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_rol_profesional_ve_solo_sus_turnos(self):
        profesional_user = create_user(username="profesional")
        otro_profesional = Profesional.objects.create(
            negocio=self.domain_a.negocio,
            nombre="Otro",
            apellido="Profesional",
        )
        otro_profesional.sucursales.add(self.domain_a.sucursal)
        otro_profesional.servicios.add(self.domain_a.servicio)
        turno_otro_profesional = self._crear_turno(
            self.domain_a,
            12,
            profesional=otro_profesional,
        )
        create_miembro(
            profesional_user,
            self.domain_a.negocio,
            rol=RolMiembroNegocio.PROFESIONAL,
            profesional=self.domain_a.profesional,
        )
        self.client.force_login(profesional_user)

        response = self.client.get(reverse("turnos:lista"))

        turnos = list(response.context["turnos"])
        self.assertIn(self.turno_a, turnos)
        self.assertNotIn(turno_otro_profesional, turnos)
        self.assertNotIn(self.turno_b, turnos)

    def test_admin_negocio_ve_todo_dentro_de_su_negocio(self):
        otro_profesional = Profesional.objects.create(
            negocio=self.domain_a.negocio,
            nombre="Admin ve",
            apellido="Todo",
        )
        otro_profesional.sucursales.add(self.domain_a.sucursal)
        otro_profesional.servicios.add(self.domain_a.servicio)
        turno_mismo_negocio = self._crear_turno(
            self.domain_a,
            13,
            profesional=otro_profesional,
        )
        self._login_con_membresia(self.domain_a, rol=RolMiembroNegocio.ADMIN_NEGOCIO)

        response = self.client.get(reverse("turnos:lista"))

        turnos = list(response.context["turnos"])
        self.assertIn(self.turno_a, turnos)
        self.assertIn(turno_mismo_negocio, turnos)
        self.assertNotIn(self.turno_b, turnos)

    def test_usuario_sin_membresia_no_ve_datos_operativos(self):
        user = create_user(username="sin-membresia")
        self.client.force_login(user)

        response = self.client.get(reverse("turnos:lista"))

        self.assertEqual(list(response.context["turnos"]), [])

    def test_superuser_ve_todo(self):
        self.client.force_login(create_superuser(username="root"))

        response = self.client.get(reverse("turnos:lista"))

        turnos = list(response.context["turnos"])
        self.assertIn(self.turno_a, turnos)
        self.assertIn(self.turno_b, turnos)

    def _login_con_membresia(self, domain, *, rol=RolMiembroNegocio.ADMIN_NEGOCIO):
        user = create_user(username=f"user-{domain.negocio.pk}-{rol}")
        create_miembro(
            user,
            domain.negocio,
            rol=rol,
            profesional=domain.profesional
            if rol == RolMiembroNegocio.PROFESIONAL
            else None,
        )
        self.client.force_login(user)
        return user

    def _crear_turno(self, domain, hour, *, profesional=None):
        inicio = aware_datetime_for_date(self.fecha, hour, 0)
        profesional = profesional or domain.profesional
        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=domain.servicio.duracion_minutos),
            estado=EstadoTurno.SOLICITADO,
        )


class AuditoriaRolesPermisosTests(TestCase):
    def setUp(self):
        self.domain_a = create_domain(prefix="Auditoria A")
        self.domain_b = create_domain(prefix="Auditoria B")
        ConfiguracionNegocio.objects.create(negocio=self.domain_a.negocio)
        ConfiguracionNegocio.objects.create(negocio=self.domain_b.negocio)
        self.fecha = future_date(days=55)
        self.turno_a = self._crear_turno(self.domain_a, 10)
        self.turno_b = self._crear_turno(self.domain_b, 11)
        self.otro_profesional_a = Profesional.objects.create(
            negocio=self.domain_a.negocio,
            nombre="Otro",
            apellido="Profesional",
        )
        self.otro_profesional_a.sucursales.add(self.domain_a.sucursal)
        self.otro_profesional_a.servicios.add(self.domain_a.servicio)
        self.turno_otro_profesional_a = self._crear_turno(
            self.domain_a,
            12,
            profesional=self.otro_profesional_a,
        )

        self.superuser = create_superuser(username="audit-root")
        self.superadmin = create_user(username="audit-superadmin")
        create_miembro(
            self.superadmin,
            self.domain_a.negocio,
            rol=RolMiembroNegocio.SUPERADMIN,
        )
        self.admin_negocio = create_user(username="audit-admin")
        create_miembro(
            self.admin_negocio,
            self.domain_a.negocio,
            rol=RolMiembroNegocio.ADMIN_NEGOCIO,
        )
        self.recepcionista = create_user(username="audit-recepcion")
        create_miembro(
            self.recepcionista,
            self.domain_a.negocio,
            rol=RolMiembroNegocio.RECEPCIONISTA,
        )
        self.profesional_user = create_user(username="audit-profesional")
        create_miembro(
            self.profesional_user,
            self.domain_a.negocio,
            rol=RolMiembroNegocio.PROFESIONAL,
            profesional=self.domain_a.profesional,
        )
        self.sin_membresia = create_user(username="audit-sin-membresia")

    def test_superuser_ve_dashboard_global_y_link_admin(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("core:dashboard"))

        metricas = {
            card["label"]: card["value"] for card in response.context["metric_cards"]
        }
        self.assertEqual(metricas["Negocios activos"], 2)
        self.assertEqual(metricas["Turnos solicitados"], 3)
        self.assertContains(response, 'href="/admin/"')

    def test_superadmin_ve_todos_los_negocios_y_puede_crear_negocio(self):
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("negocios:lista"))
        negocios = list(response.context["negocios"])

        self.assertIn(self.domain_a.negocio, negocios)
        self.assertIn(self.domain_b.negocio, negocios)
        self.assertEqual(self.client.get(reverse("negocios:crear")).status_code, 200)

    def test_admin_negocio_solo_ve_su_negocio(self):
        self.client.force_login(self.admin_negocio)

        response = self.client.get(reverse("negocios:lista"))
        negocios = list(response.context["negocios"])

        self.assertIn(self.domain_a.negocio, negocios)
        self.assertNotIn(self.domain_b.negocio, negocios)

    def test_admin_negocio_no_accede_a_objeto_de_otro_negocio(self):
        self.client.force_login(self.admin_negocio)

        response = self.client.get(
            reverse("sucursales:detalle", kwargs={"pk": self.domain_b.sucursal.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_recepcionista_accede_a_clientes_turnos_y_no_configuracion(self):
        self.client.force_login(self.recepcionista)

        self.assertEqual(self.client.get(reverse("clientes:lista")).status_code, 200)
        self.assertEqual(self.client.get(reverse("turnos:lista")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("configuracion_negocio:lista")).status_code,
            403,
        )

    def test_recepcionista_ve_catalogos_sin_acciones_de_gestion_sensible(self):
        self.client.force_login(self.recepcionista)

        response = self.client.get(reverse("servicios:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.domain_a.servicio.nombre)
        self.assertNotContains(response, reverse("servicios:crear"))
        self.assertNotContains(
            response,
            reverse("servicios:editar", kwargs={"pk": self.domain_a.servicio.pk}),
        )

    def test_profesional_ve_solo_sus_turnos(self):
        self.client.force_login(self.profesional_user)

        response = self.client.get(reverse("turnos:lista"))
        turnos = list(response.context["turnos"])

        self.assertIn(self.turno_a, turnos)
        self.assertNotIn(self.turno_otro_profesional_a, turnos)
        self.assertNotIn(self.turno_b, turnos)

    def test_profesional_no_accede_a_turno_de_otro_profesional(self):
        self.client.force_login(self.profesional_user)

        response = self.client.get(
            reverse("turnos:detalle", kwargs={"pk": self.turno_otro_profesional_a.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_profesional_no_abre_configuracion_ni_formulario_de_turno(self):
        self.client.force_login(self.profesional_user)

        self.assertEqual(
            self.client.get(reverse("configuracion_negocio:lista")).status_code,
            403,
        )
        self.assertEqual(self.client.get(reverse("turnos:crear")).status_code, 403)

    def test_profesional_no_ve_botones_operativos_indebidos(self):
        self.client.force_login(self.profesional_user)

        response = self.client.get(reverse("turnos:lista"))

        self.assertNotContains(response, reverse("turnos:crear"))
        self.assertNotContains(
            response,
            reverse("turnos:editar", kwargs={"pk": self.turno_a.pk}),
        )
        self.assertContains(
            response,
            reverse("turnos:detalle", kwargs={"pk": self.turno_a.pk}),
        )

    def test_usuario_sin_membresia_recibe_mensaje_claro_en_dashboard(self):
        self.client.force_login(self.sin_membresia)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No tenés negocios asignados. Contactá a un administrador.",
        )
        self.assertNotContains(response, 'href="/clientes/"')
        self.assertNotContains(response, 'href="/turnos/"')

    def test_usuario_sin_membresia_no_accede_a_datos_por_url_directa(self):
        self.client.force_login(self.sin_membresia)

        response = self.client.get(
            reverse("clientes:detalle", kwargs={"pk": self.domain_a.cliente.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_navegacion_oculta_links_no_permitidos_por_rol(self):
        self.client.force_login(self.recepcionista)
        recepcion_response = self.client.get(reverse("core:dashboard"))

        self.assertNotContains(recepcion_response, 'href="/configuracion/"')
        self.assertNotContains(recepcion_response, 'href="/admin/"')

        self.client.force_login(self.profesional_user)
        profesional_response = self.client.get(reverse("core:dashboard"))

        self.assertNotContains(profesional_response, 'href="/negocios/"')
        self.assertNotContains(profesional_response, 'href="/configuracion/"')
        self.assertContains(profesional_response, 'href="/turnos/"')

    def test_formularios_no_muestran_negocios_fuera_del_alcance(self):
        self.client.force_login(self.admin_negocio)

        response = self.client.get(reverse("clientes:crear"))
        negocios = list(response.context["form"].fields["negocio"].queryset)

        self.assertIn(self.domain_a.negocio, negocios)
        self.assertNotIn(self.domain_b.negocio, negocios)

    def _crear_turno(self, domain, hour, *, profesional=None):
        inicio = aware_datetime_for_date(self.fecha, hour, 0)
        profesional = profesional or domain.profesional
        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=domain.servicio.duracion_minutos),
            estado=EstadoTurno.SOLICITADO,
        )
