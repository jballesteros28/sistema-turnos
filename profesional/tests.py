from django.test import TestCase

from test_utils import create_domain

from .models import EstadoProfesional, TipoProfesional


class ProfesionalModelTests(TestCase):
    def test_crea_profesional_valido_con_defaults_y_relaciones(self):
        domain = create_domain(prefix="Profesional")

        self.assertEqual(str(domain.profesional), domain.profesional.nombre_visible)
        self.assertEqual(domain.profesional.negocio, domain.negocio)
        self.assertEqual(domain.profesional.estado, EstadoProfesional.ACTIVO)
        self.assertEqual(domain.profesional.tipo_profesional, TipoProfesional.OTRO)
        self.assertTrue(domain.profesional.acepta_turnos)
        self.assertIn(domain.sucursal, domain.profesional.sucursales.all())
        self.assertIn(domain.servicio, domain.profesional.servicios.all())
