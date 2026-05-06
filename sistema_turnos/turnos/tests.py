from datetime import datetime, time, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from clientes.models import Cliente
from configuracion_negocio.models import ConfiguracionNegocio
from disponibilidad.models import DiaSemana, Disponibilidad
from excepcion.models import ExcepcionAgenda, TipoExcepcion
from negocio.models import Negocio
from profesional.models import Profesional
from servicio.models import Servicio
from sucursal.models import Sucursal
from turnos.models import EstadoTurno, Turno


class DominioTurnosTest(TestCase):
    def setUp(self):
        self.negocio = Negocio.objects.create(
            nombre="Barberia Norte",
            email_principal="hola@barberianorte.test",
            telefono_principal="111111111",
            ciudad="Cordoba",
            pais="Argentina",
        )
        self.configuracion = ConfiguracionNegocio.objects.create(negocio=self.negocio)
        self.sucursal = Sucursal.objects.create(
            negocio=self.negocio,
            nombre="Casa central",
            direccion="Av. Siempre Viva 123",
            ciudad="Cordoba",
            pais="Argentina",
            es_principal=True,
        )
        self.cliente = Cliente.objects.create(
            negocio=self.negocio,
            nombre="Juan",
            apellido="Perez",
            telefono="222222222",
        )
        self.servicio = Servicio.objects.create(
            negocio=self.negocio,
            nombre="Corte clasico",
            duracion_minutos=30,
            precio=8000,
        )
        self.profesional = Profesional.objects.create(
            negocio=self.negocio,
            nombre="Ana",
            apellido="Gomez",
        )
        self.profesional.sucursales.add(self.sucursal)
        self.profesional.servicios.add(self.servicio)

    def test_crea_nucleo_del_dominio(self):
        Disponibilidad.objects.create(
            negocio=self.negocio,
            sucursal=self.sucursal,
            profesional=self.profesional,
            dia_semana=DiaSemana.JUEVES,
            hora_inicio=time(9, 0),
            hora_fin=time(18, 0),
        )
        ExcepcionAgenda.objects.create(
            negocio=self.negocio,
            profesional=self.profesional,
            tipo=TipoExcepcion.AUSENCIA_PROFESIONAL,
            titulo="Capacitacion",
            fecha_hora_inicio=self._aware(2026, 5, 7, 13, 0),
            fecha_hora_fin=self._aware(2026, 5, 7, 14, 0),
        )
        turno = Turno.objects.create(
            negocio=self.negocio,
            sucursal=self.sucursal,
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            fecha_hora_inicio=self._aware(2026, 5, 7, 10, 0),
            fecha_hora_fin=self._aware(2026, 5, 7, 10, 30),
            estado=EstadoTurno.CONFIRMADO,
        )

        self.assertEqual(self.negocio.sucursales.count(), 1)
        self.assertEqual(self.negocio.profesionales.count(), 1)
        self.assertEqual(self.negocio.clientes.count(), 1)
        self.assertEqual(self.negocio.servicios.count(), 1)
        self.assertEqual(self.negocio.disponibilidades.count(), 1)
        self.assertEqual(self.negocio.excepciones.count(), 1)
        self.assertEqual(self.negocio.turnos.count(), 1)
        self.assertEqual(self.negocio.configuracion, self.configuracion)
        self.assertEqual(turno.duracion_minutos, self.servicio.duracion_minutos)

    def test_no_permite_turno_con_fin_antes_de_inicio(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Turno.objects.create(
                    negocio=self.negocio,
                    sucursal=self.sucursal,
                    cliente=self.cliente,
                    profesional=self.profesional,
                    servicio=self.servicio,
                    fecha_hora_inicio=self._aware(2026, 5, 7, 10, 30),
                    fecha_hora_fin=self._aware(2026, 5, 7, 10, 0),
                )

    def test_no_permite_doble_turno_activo_con_mismo_inicio_y_profesional(self):
        inicio = self._aware(2026, 5, 7, 10, 0)
        Turno.objects.create(
            negocio=self.negocio,
            sucursal=self.sucursal,
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=30),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Turno.objects.create(
                    negocio=self.negocio,
                    sucursal=self.sucursal,
                    cliente=self.cliente,
                    profesional=self.profesional,
                    servicio=self.servicio,
                    fecha_hora_inicio=inicio,
                    fecha_hora_fin=inicio + timedelta(minutes=30),
                )

    def _aware(self, year, month, day, hour, minute):
        return timezone.make_aware(datetime(year, month, day, hour, minute))
