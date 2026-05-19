from django.test import TestCase

from test_utils import create_domain

from .models import EstadoSucursal


class SucursalModelTests(TestCase):
    def test_crea_sucursal_valida_con_defaults_y_relacion(self):
        domain = create_domain(prefix="Sucursal")

        self.assertEqual(str(domain.sucursal), f"{domain.negocio.nombre} - {domain.sucursal.nombre}")
        self.assertEqual(domain.sucursal.negocio, domain.negocio)
        self.assertEqual(domain.sucursal.estado, EstadoSucursal.ACTIVA)
        self.assertTrue(domain.sucursal.acepta_turnos)
        self.assertEqual(domain.sucursal.slug, domain.sucursal.nombre.lower().replace(" ", "-"))
        self.assertEqual(domain.sucursal.zona_horaria, domain.negocio.zona_horaria)
