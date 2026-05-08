from django.test import TestCase

from test_utils import create_superuser


class BasicViewStatusTests(TestCase):
    def setUp(self):
        self.client.force_login(create_superuser())

    def test_vistas_principales_responden_200(self):
        paths = (
            "/dashboard/",
            "/negocios/",
            "/sucursales/",
            "/clientes/",
            "/servicios/",
            "/profesionales/",
            "/agenda/disponibilidades/",
            "/agenda/excepciones/",
            "/turnos/",
            "/agenda/turnos/",
            "/configuracion/",
        )

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)

    def test_raiz_redirige_a_dashboard(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dashboard/")
