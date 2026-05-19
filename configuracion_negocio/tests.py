from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from negocio.models import Negocio
from test_utils import create_domain, create_miembro, create_user
from usuarios.models import RolMiembroNegocio

from .models import ConfiguracionNegocio, PoliticaConfirmacion


class ConfiguracionNegocioModelTests(TestCase):
    def test_crea_configuracion_valida_con_defaults(self):
        negocio = Negocio.objects.create(
            nombre="Negocio Configurado",
            email_principal="config@example.test",
            telefono_principal="123456",
            ciudad="Cordoba",
            pais="Argentina",
        )

        configuracion = ConfiguracionNegocio.objects.create(negocio=negocio)

        self.assertEqual(str(configuracion), f"Configuracion de {negocio}")
        self.assertEqual(configuracion.negocio, negocio)
        self.assertTrue(configuracion.permite_reserva_online)
        self.assertTrue(configuracion.permite_cancelacion_online)
        self.assertEqual(
            configuracion.politica_confirmacion,
            PoliticaConfirmacion.AUTOMATICA,
        )
        self.assertEqual(configuracion.intervalo_turnos_minutos, 15)
        self.assertEqual(configuracion.buffer_entre_turnos_minutos, 0)
        self.assertFalse(configuracion.permite_turnos_pasados)
        self.assertTrue(configuracion.confirmacion_automatica)
        self.assertTrue(configuracion.permite_cancelacion)

    def test_un_negocio_no_puede_tener_mas_de_una_configuracion(self):
        domain = create_domain(prefix="Config Unica")
        ConfiguracionNegocio.objects.create(negocio=domain.negocio)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ConfiguracionNegocio.objects.create(negocio=domain.negocio)


class ConfiguracionNegocioViewTests(TestCase):
    def test_crud_basico_responde(self):
        domain = create_domain(prefix="Config Vista")
        user = create_user(username="config-admin")
        create_miembro(user, domain.negocio, rol=RolMiembroNegocio.ADMIN_NEGOCIO)
        self.client.force_login(user)
        configuracion = ConfiguracionNegocio.objects.create(negocio=domain.negocio)

        paths = (
            reverse("configuracion_negocio:lista"),
            reverse("configuracion_negocio:detalle", kwargs={"pk": configuracion.pk}),
            reverse("configuracion_negocio:crear"),
            reverse("configuracion_negocio:editar", kwargs={"pk": configuracion.pk}),
        )

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
