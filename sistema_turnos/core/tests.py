import os
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from sistema_turnos.settings import get_bool_env, get_int_env, get_list_env
from test_utils import create_superuser


class EnvironmentHelperTests(SimpleTestCase):
    def test_get_bool_env_parsea_true_y_false(self):
        with patch.dict(
            os.environ,
            {
                "ST_TRUE": "True",
                "ST_FALSE": "off",
            },
        ):
            self.assertIs(get_bool_env("ST_TRUE"), True)
            self.assertIs(get_bool_env("ST_FALSE", True), False)

    def test_get_bool_env_usa_default_si_el_valor_es_invalido(self):
        with patch.dict(os.environ, {"ST_INVALID": "quizas"}):
            self.assertIs(get_bool_env("ST_INVALID", True), True)

    def test_get_list_env_limpia_espacios_y_valores_vacios(self):
        with patch.dict(os.environ, {"ST_LIST": "localhost, 127.0.0.1, ,example.com"}):
            self.assertEqual(
                get_list_env("ST_LIST"),
                ["localhost", "127.0.0.1", "example.com"],
            )

    def test_get_int_env_usa_default_si_no_es_entero(self):
        with patch.dict(os.environ, {"ST_INT": "abc"}):
            self.assertEqual(get_int_env("ST_INT", 587), 587)


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
