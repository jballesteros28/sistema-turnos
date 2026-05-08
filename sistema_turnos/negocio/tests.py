from django.test import TestCase

from .models import EstadoNegocio, Idioma, Moneda, Negocio, TipoNegocio


class NegocioModelTests(TestCase):
    def test_crea_negocio_valido_con_defaults_y_slug(self):
        negocio = Negocio.objects.create(
            nombre="Barberia Norte",
            email_principal="hola@barberia.test",
            telefono_principal="123456",
            ciudad="Cordoba",
            pais="Argentina",
        )

        self.assertEqual(str(negocio), "Barberia Norte")
        self.assertEqual(negocio.slug, "barberia-norte")
        self.assertEqual(negocio.nombre_visible, "Barberia Norte")
        self.assertEqual(negocio.estado, EstadoNegocio.ACTIVO)
        self.assertEqual(negocio.tipo_negocio, TipoNegocio.OTRO)
        self.assertEqual(negocio.moneda, Moneda.ARS)
        self.assertEqual(negocio.idioma, Idioma.ES)
