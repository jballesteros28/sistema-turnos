from django.test import TestCase

from test_utils import create_domain

from .models import EstadoServicio


class ServicioModelTests(TestCase):
    def test_crea_servicio_valido_con_defaults_y_relacion(self):
        domain = create_domain(prefix="Servicio")

        self.assertEqual(str(domain.servicio), domain.servicio.nombre)
        self.assertEqual(domain.servicio.negocio, domain.negocio)
        self.assertEqual(domain.servicio.estado, EstadoServicio.ACTIVO)
        self.assertEqual(domain.servicio.duracion_minutos, 60)
        self.assertEqual(domain.servicio.precio, 1000)
        self.assertTrue(domain.servicio.visible_en_reserva_online)
