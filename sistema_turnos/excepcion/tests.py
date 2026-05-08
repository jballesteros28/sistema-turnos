from datetime import timedelta

from django.test import TestCase

from profesional.models import Profesional
from test_utils import create_domain, excepcion_form_data, future_datetime

from .forms import ExcepcionAgendaForm
from .models import ExcepcionAgenda, TipoExcepcion


class ExcepcionAgendaModelTests(TestCase):
    def test_crea_excepcion_valida(self):
        domain = create_domain(prefix="Exc Modelo")
        inicio = future_datetime(hour=13)
        excepcion = ExcepcionAgenda.objects.create(
            negocio=domain.negocio,
            titulo="Feriado local",
            tipo=TipoExcepcion.FERIADO,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(hours=4),
        )

        self.assertEqual(excepcion.negocio, domain.negocio)
        self.assertTrue(excepcion.activo)
        self.assertTrue(excepcion.bloquea_turnos)
        self.assertIn("Feriado local", str(excepcion))


class ExcepcionAgendaFormTests(TestCase):
    def test_crea_excepcion_valida_a_nivel_negocio(self):
        domain = create_domain(prefix="Exc Negocio")

        form = ExcepcionAgendaForm(
            data=excepcion_form_data(domain, tipo=TipoExcepcion.CIERRE_NEGOCIO)
        )

        self.assertTrue(form.is_valid(), form.errors)
        excepcion = form.save()
        self.assertIsNone(excepcion.sucursal)
        self.assertIsNone(excepcion.profesional)

    def test_crea_excepcion_valida_a_nivel_sucursal(self):
        domain = create_domain(prefix="Exc Sucursal")

        form = ExcepcionAgendaForm(
            data=excepcion_form_data(
                domain,
                tipo=TipoExcepcion.CIERRE_SUCURSAL,
                sucursal=domain.sucursal,
            )
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sucursal, domain.sucursal)

    def test_crea_excepcion_valida_a_nivel_profesional(self):
        domain = create_domain(prefix="Exc Profesional")

        form = ExcepcionAgendaForm(
            data=excepcion_form_data(
                domain,
                tipo=TipoExcepcion.AUSENCIA_PROFESIONAL,
                sucursal=domain.sucursal,
                profesional=domain.profesional,
            )
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().profesional, domain.profesional)

    def test_no_permite_fecha_hora_mal_ordenada(self):
        domain = create_domain(prefix="Exc Fechas")
        inicio = future_datetime(hour=15)

        for fin in (inicio - timedelta(minutes=30), inicio):
            with self.subTest(fin=fin):
                data = excepcion_form_data(
                    domain,
                    tipo=TipoExcepcion.CIERRE_NEGOCIO,
                    inicio=inicio,
                    fin=fin,
                )
                form = ExcepcionAgendaForm(data=data)

                self.assertFalse(form.is_valid())
                self.assertIn("fecha_hora_fin", form.errors)

    def test_no_permite_sucursal_de_otro_negocio(self):
        domain = create_domain(prefix="Exc Negocio Sucursal")
        otro = create_domain(prefix="Exc Otro Sucursal")
        data = excepcion_form_data(
            domain,
            tipo=TipoExcepcion.CIERRE_SUCURSAL,
            sucursal=otro.sucursal,
        )

        form = ExcepcionAgendaForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("sucursal", form.errors)

    def test_no_permite_profesional_de_otro_negocio(self):
        domain = create_domain(prefix="Exc Negocio Profesional")
        otro = create_domain(prefix="Exc Otro Profesional")
        data = excepcion_form_data(
            domain,
            tipo=TipoExcepcion.AUSENCIA_PROFESIONAL,
            profesional=otro.profesional,
        )

        form = ExcepcionAgendaForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_profesional_no_asociado_a_sucursal(self):
        domain = create_domain(prefix="Exc Sin Sucursal")
        profesional = Profesional.objects.create(
            negocio=domain.negocio,
            nombre="Profesional",
            apellido="Sin Sucursal",
        )
        data = excepcion_form_data(
            domain,
            tipo=TipoExcepcion.AUSENCIA_PROFESIONAL,
            sucursal=domain.sucursal,
            profesional=profesional,
        )

        form = ExcepcionAgendaForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_alcance_incoherente(self):
        domain = create_domain(prefix="Exc Alcance")

        casos = (
            (TipoExcepcion.CIERRE_SUCURSAL, "sucursal"),
            (TipoExcepcion.AUSENCIA_PROFESIONAL, "profesional"),
        )
        for tipo, field in casos:
            with self.subTest(tipo=tipo):
                form = ExcepcionAgendaForm(data=excepcion_form_data(domain, tipo=tipo))

                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_no_permite_duplicado_exacto(self):
        domain = create_domain(prefix="Exc Duplicada")
        inicio = future_datetime(hour=12)
        ExcepcionAgenda.objects.create(
            negocio=domain.negocio,
            tipo=TipoExcepcion.CIERRE_NEGOCIO,
            titulo="Cierre",
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(hours=1),
        )
        data = excepcion_form_data(
            domain,
            tipo=TipoExcepcion.CIERRE_NEGOCIO,
            titulo="Otro titulo",
            inicio=inicio,
            fin=inicio + timedelta(hours=1),
        )

        form = ExcepcionAgendaForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)
