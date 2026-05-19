from django.test import TestCase

from test_utils import create_domain

from .models import EstadoCliente


class ClienteModelTests(TestCase):
    def test_crea_cliente_valido_con_defaults_y_relacion(self):
        domain = create_domain(prefix="Cliente")

        self.assertEqual(str(domain.cliente), domain.cliente.nombre_visible)
        self.assertEqual(domain.cliente.negocio, domain.negocio)
        self.assertEqual(domain.cliente.estado, EstadoCliente.ACTIVO)
        self.assertTrue(domain.cliente.acepta_recordatorios)
        self.assertEqual(
            domain.cliente.nombre_visible,
            f"{domain.cliente.nombre} {domain.cliente.apellido}",
        )
