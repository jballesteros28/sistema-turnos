from datetime import time

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
        self.assertIn("09:00:00-17:00:00", str(disponibilidad))


class DisponibilidadFormTests(TestCase):
    def test_crea_disponibilidad_valida(self):
        domain = create_domain(prefix="Disp Form")

        form = DisponibilidadForm(data=disponibilidad_form_data(domain))

        self.assertTrue(form.is_valid(), form.errors)
        disponibilidad = form.save()
        self.assertEqual(disponibilidad.negocio, domain.negocio)

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
