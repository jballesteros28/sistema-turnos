import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from clientes.models import Cliente
from configuracion_negocio.models import ConfiguracionNegocio
from disponibilidad.models import Disponibilidad
from negocio.models import Negocio
from profesional.models import Profesional
from servicio.models import Servicio
from sucursal.models import Sucursal
from usuarios.models import MiembroNegocio


class CrearSuperuserRenderCommandTests(TestCase):
    def test_crea_superuser_si_env_vars_existen(self):
        salida = StringIO()

        with patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": "render-admin",
                "DJANGO_SUPERUSER_EMAIL": "admin@example.test",
                "DJANGO_SUPERUSER_PASSWORD": "clave-render-test",
            },
        ):
            call_command("crear_superuser_render", stdout=salida)

        user = get_user_model().objects.get(username="render-admin")
        self.assertEqual(user.email, "admin@example.test")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertNotIn("clave-render-test", salida.getvalue())

    def test_no_duplica_superuser_existente(self):
        User = get_user_model()
        User.objects.create_superuser(
            username="render-admin",
            email="admin@example.test",
            password="clave-original",
        )

        with patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": "render-admin",
                "DJANGO_SUPERUSER_EMAIL": "admin@example.test",
                "DJANGO_SUPERUSER_PASSWORD": "clave-render-test",
            },
        ):
            call_command("crear_superuser_render", stdout=StringIO())
            call_command("crear_superuser_render", stdout=StringIO())

        self.assertEqual(User.objects.filter(username="render-admin").count(), 1)

    def test_no_falla_si_faltan_env_vars(self):
        salida = StringIO()

        with patch.dict(
            os.environ,
            {
                "DJANGO_SUPERUSER_USERNAME": "",
                "DJANGO_SUPERUSER_EMAIL": "",
                "DJANGO_SUPERUSER_PASSWORD": "",
            },
        ):
            call_command("crear_superuser_render", stdout=salida)

        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("no creado", salida.getvalue())


class CrearUsuariosDemoRenderSafeCommandTests(TestCase):
    def test_render_safe_no_crea_demo_si_env_lo_desactiva(self):
        salida = StringIO()

        with patch.dict(os.environ, {"CREATE_DEMO_USERS": "False"}):
            call_command("crear_usuarios_demo", "--render-safe", stdout=salida)

        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Negocio.objects.count(), 0)
        self.assertIn("CREATE_DEMO_USERS", salida.getvalue())

    def test_render_safe_crea_demo_sin_duplicar(self):
        with patch.dict(os.environ, {"CREATE_DEMO_USERS": "True"}):
            call_command("crear_usuarios_demo", "--render-safe", stdout=StringIO())
            counts = self._counts()
            call_command("crear_usuarios_demo", "--render-safe", stdout=StringIO())

        self.assertEqual(self._counts(), counts)
        self.assertEqual(
            get_user_model().objects.filter(username="superuser").count(),
            1,
        )
        self.assertEqual(Negocio.objects.filter(slug="negocio-demo").count(), 1)
        self.assertEqual(MiembroNegocio.objects.count(), 4)

    def _counts(self):
        return {
            "users": get_user_model().objects.count(),
            "negocios": Negocio.objects.count(),
            "sucursales": Sucursal.objects.count(),
            "servicios": Servicio.objects.count(),
            "profesionales": Profesional.objects.count(),
            "clientes": Cliente.objects.count(),
            "disponibilidades": Disponibilidad.objects.count(),
            "configuraciones": ConfiguracionNegocio.objects.count(),
            "membresias": MiembroNegocio.objects.count(),
        }
