from datetime import time
from importlib import import_module
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from profesional.models import EstadoProfesional, Profesional
from sucursal.models import EstadoSucursal
from test_utils import create_availability, create_domain, disponibilidad_form_data

from .forms import DisponibilidadForm
from .models import Disponibilidad


class DisponibilidadModelTests(TestCase):
    def test_crea_disponibilidad_valida(self):
        domain = create_domain(prefix="Disp Modelo")

        disponibilidad = create_availability(domain, start=time(9, 0), end=time(17, 0))

        self.assertEqual(disponibilidad.negocio, domain.negocio)
        self.assertEqual(disponibilidad.sucursal, domain.sucursal)
        self.assertEqual(disponibilidad.profesional, domain.profesional)
        self.assertTrue(disponibilidad.activo)
        self.assertEqual(disponibilidad.dias_semana, [disponibilidad.dia_semana])
        self.assertIn("09:00:00-17:00:00", str(disponibilidad))


class DisponibilidadFormTests(TestCase):
    def test_crea_disponibilidad_valida(self):
        domain = create_domain(prefix="Disp Form")

        form = DisponibilidadForm(data=disponibilidad_form_data(domain))

        self.assertTrue(form.is_valid(), form.errors)
        disponibilidad = form.save()
        self.assertEqual(disponibilidad.negocio, domain.negocio)
        self.assertEqual(disponibilidad.dias_semana, [disponibilidad.dia_semana])

    def test_crea_disponibilidad_lunes_a_viernes(self):
        domain = create_domain(prefix="Disp Lunes Viernes")
        data = disponibilidad_form_data(domain, dias_semana=[0, 1, 2, 3, 4])

        form = DisponibilidadForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)
        disponibilidad = form.save()
        self.assertEqual(disponibilidad.dias_semana, [0, 1, 2, 3, 4])
        self.assertEqual(disponibilidad.dia_semana, 0)
        self.assertEqual(disponibilidad.dias_semana_display(), "Lunes a viernes")

    def test_no_permite_dias_semana_vacio(self):
        domain = create_domain(prefix="Disp Sin Dias")
        data = disponibilidad_form_data(domain, dias_semana=[])

        form = DisponibilidadForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("dias_semana", form.errors)

    def test_no_permite_hora_inicio_mayor_o_igual_a_hora_fin(self):
        domain = create_domain(prefix="Disp Horas")

        casos = (
            (time(18, 0), time(9, 0)),
            (time(9, 0), time(9, 0)),
        )
        for hora_inicio, hora_fin in casos:
            with self.subTest(hora_inicio=hora_inicio, hora_fin=hora_fin):
                data = disponibilidad_form_data(
                    domain,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                )
                form = DisponibilidadForm(data=data)

                self.assertFalse(form.is_valid())
                self.assertIn("hora_fin", form.errors)

    def test_no_permite_sucursal_de_otro_negocio(self):
        domain = create_domain(prefix="Disp Negocio")
        otro = create_domain(prefix="Disp Otro")
        data = disponibilidad_form_data(domain)
        data["sucursal"] = otro.sucursal.pk

        form = DisponibilidadForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("sucursal", form.errors)

    def test_no_permite_profesional_de_otro_negocio(self):
        domain = create_domain(prefix="Disp Profesional")
        otro = create_domain(prefix="Disp Otro Profesional")
        data = disponibilidad_form_data(domain)
        data["profesional"] = otro.profesional.pk

        form = DisponibilidadForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_profesional_no_asociado_a_sucursal(self):
        domain = create_domain(prefix="Disp Sin Sucursal")
        profesional = Profesional.objects.create(
            negocio=domain.negocio,
            nombre="Profesional sin",
            apellido="Sucursal",
        )
        data = disponibilidad_form_data(domain)
        data["profesional"] = profesional.pk

        form = DisponibilidadForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_duplicado_exacto(self):
        domain = create_domain(prefix="Disp Duplicada")
        create_availability(domain)

        form = DisponibilidadForm(data=disponibilidad_form_data(domain))

        self.assertFalse(form.is_valid())
        self.assertIn("hora_inicio", form.errors)

    def test_no_permite_duplicado_con_dia_compartido(self):
        domain = create_domain(prefix="Disp Duplicada Multi")
        create_availability(domain, dias_semana=[0, 1, 2, 3, 4])
        data = disponibilidad_form_data(domain, dias_semana=[2])

        form = DisponibilidadForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("hora_inicio", form.errors)

    def test_no_permite_solapamiento_con_dia_compartido(self):
        domain = create_domain(prefix="Disp Solapada Multi")
        create_availability(domain, dias_semana=[0, 1, 2, 3, 4])
        data = disponibilidad_form_data(
            domain,
            dias_semana=[3],
            hora_inicio=time(12, 0),
            hora_fin=time(15, 0),
        )

        form = DisponibilidadForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("hora_inicio", form.errors)

    def test_permite_solapamiento_en_dia_distinto(self):
        domain = create_domain(prefix="Disp Dia Distinto")
        create_availability(domain, dias_semana=[0, 1, 2, 3, 4])
        data = disponibilidad_form_data(
            domain,
            dias_semana=[5],
            hora_inicio=time(12, 0),
            hora_fin=time(15, 0),
        )

        form = DisponibilidadForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_no_permite_sucursal_inactiva_o_que_no_acepta_turnos(self):
        for field, value in (
            ("estado", EstadoSucursal.INACTIVA),
            ("acepta_turnos", False),
        ):
            with self.subTest(field=field):
                domain = create_domain(prefix=f"Disp Sucursal {field}")
                setattr(domain.sucursal, field, value)
                domain.sucursal.save(update_fields=[field, "actualizado_en"])

                form = DisponibilidadForm(data=disponibilidad_form_data(domain))

                self.assertFalse(form.is_valid())
                self.assertIn("sucursal", form.errors)

    def test_no_permite_profesional_inactivo_o_que_no_acepta_turnos(self):
        for field, value in (
            ("estado", EstadoProfesional.INACTIVO),
            ("acepta_turnos", False),
        ):
            with self.subTest(field=field):
                domain = create_domain(prefix=f"Disp Profesional {field}")
                setattr(domain.profesional, field, value)
                domain.profesional.save(update_fields=[field, "actualizado_en"])

                form = DisponibilidadForm(data=disponibilidad_form_data(domain))

                self.assertFalse(form.is_valid())
                self.assertIn("profesional", form.errors)


class DisponibilidadMigrationTests(TestCase):
    def test_migracion_datos_copia_dia_semana_a_lista(self):
        domain = create_domain(prefix="Disp Migracion")
        disponibilidad = create_availability(domain, dia_semana=2)
        Disponibilidad.objects.filter(pk=disponibilidad.pk).update(dias_semana=[])

        migration = import_module("disponibilidad.migrations.0003_migrar_dias_semana")
        migration.migrar_dias_semana(apps, None)

        disponibilidad.refresh_from_db()
        self.assertEqual(disponibilidad.dias_semana, [2])


class CrearUsuariosDemoTests(TestCase):
    def test_crear_usuarios_demo_genera_disponibilidad_lunes_a_viernes(self):
        output = StringIO()

        call_command("crear_usuarios_demo", stdout=output)

        disponibilidad = Disponibilidad.objects.get(
            profesional__slug="profesional-demo",
            sucursal__slug="sucursal-demo",
            hora_inicio=time(9, 0),
            hora_fin=time(18, 0),
        )
        self.assertEqual(disponibilidad.dias_semana, [0, 1, 2, 3, 4])
        total_disponibilidades = Disponibilidad.objects.count()

        call_command("crear_usuarios_demo", stdout=StringIO())

        disponibilidad.refresh_from_db()
        self.assertEqual(disponibilidad.dias_semana, [0, 1, 2, 3, 4])
        self.assertEqual(Disponibilidad.objects.count(), total_disponibilidades)
