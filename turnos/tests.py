from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import EstadoCliente
from configuracion_negocio.models import ConfiguracionNegocio, PoliticaConfirmacion
from excepcion.models import ExcepcionAgenda, TipoExcepcion
from profesional.models import EstadoProfesional, Profesional
from servicio.models import EstadoServicio, Servicio
from sucursal.models import EstadoSucursal
from test_utils import (
    create_availability,
    create_domain,
    create_miembro,
    create_user,
    future_date,
    aware_datetime_for_date,
    turno_form_data,
)
from usuarios.models import RolMiembroNegocio

from .forms import TurnoForm
from .models import EstadoTurno, Turno


class TurnoFormTests(TestCase):
    def setUp(self):
        self.domain = create_domain(prefix="Turno")
        self.fecha = future_date(days=10)
        self.inicio = aware_datetime_for_date(self.fecha, 10, 0)
        create_availability(self.domain, date_value=self.fecha)

    def test_crea_turno_valido_dentro_de_disponibilidad(self):
        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertTrue(form.is_valid(), form.errors)
        turno = form.save()
        self.assertEqual(turno.negocio, self.domain.negocio)
        self.assertEqual(turno.estado, EstadoTurno.SOLICITADO)
        self.assertIn(str(self.domain.cliente), str(turno))
        self.assertIn(str(self.domain.profesional), str(turno))

    def test_fecha_hora_fin_se_calcula_segun_duracion_del_servicio(self):
        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertTrue(form.is_valid(), form.errors)
        turno = form.save()
        self.assertEqual(
            turno.fecha_hora_fin,
            self.inicio + timedelta(minutes=self.domain.servicio.duracion_minutos),
        )
        self.assertEqual(turno.duracion_minutos, self.domain.servicio.duracion_minutos)

    def test_no_permite_turno_fuera_de_disponibilidad(self):
        inicio = aware_datetime_for_date(self.fecha, 8, 0)

        form = TurnoForm(data=turno_form_data(self.domain, inicio=inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_no_permite_turno_sobre_excepcion_activa_de_negocio(self):
        self._crear_excepcion(tipo=TipoExcepcion.CIERRE_NEGOCIO)

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_no_permite_turno_sobre_excepcion_activa_de_sucursal(self):
        self._crear_excepcion(
            tipo=TipoExcepcion.CIERRE_SUCURSAL,
            sucursal=self.domain.sucursal,
        )

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_no_permite_turno_sobre_excepcion_activa_de_profesional(self):
        self._crear_excepcion(
            tipo=TipoExcepcion.AUSENCIA_PROFESIONAL,
            profesional=self.domain.profesional,
        )

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_permite_turno_si_la_excepcion_esta_inactiva(self):
        self._crear_excepcion(tipo=TipoExcepcion.CIERRE_NEGOCIO, activo=False)

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertTrue(form.is_valid(), form.errors)

    def test_no_permite_sucursal_de_otro_negocio(self):
        otro = create_domain(prefix="Turno Otro Sucursal")
        data = turno_form_data(self.domain, inicio=self.inicio, sucursal=otro.sucursal)

        form = TurnoForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("sucursal", form.errors)

    def test_no_permite_cliente_de_otro_negocio(self):
        otro = create_domain(prefix="Turno Otro Cliente")
        data = turno_form_data(self.domain, inicio=self.inicio, cliente=otro.cliente)

        form = TurnoForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("cliente", form.errors)

    def test_no_permite_profesional_de_otro_negocio(self):
        otro = create_domain(prefix="Turno Otro Profesional")
        data = turno_form_data(
            self.domain,
            inicio=self.inicio,
            profesional=otro.profesional,
        )

        form = TurnoForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_servicio_de_otro_negocio(self):
        otro = create_domain(prefix="Turno Otro Servicio")
        data = turno_form_data(self.domain, inicio=self.inicio, servicio=otro.servicio)

        form = TurnoForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("servicio", form.errors)

    def test_no_permite_profesional_no_asociado_a_sucursal(self):
        profesional = Profesional.objects.create(
            negocio=self.domain.negocio,
            nombre="Sin",
            apellido="Sucursal",
        )
        profesional.servicios.add(self.domain.servicio)
        data = turno_form_data(self.domain, inicio=self.inicio, profesional=profesional)

        form = TurnoForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_profesional_que_no_presta_el_servicio(self):
        servicio = Servicio.objects.create(
            negocio=self.domain.negocio,
            nombre="Servicio no prestado",
            duracion_minutos=60,
            precio=1000,
        )
        data = turno_form_data(self.domain, inicio=self.inicio, servicio=servicio)

        form = TurnoForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("servicio", form.errors)

    def test_no_permite_servicio_inactivo(self):
        self.domain.servicio.estado = EstadoServicio.INACTIVO
        self.domain.servicio.save(update_fields=["estado", "actualizado_en"])

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("servicio", form.errors)

    def test_no_permite_cliente_inactivo(self):
        self.domain.cliente.estado = EstadoCliente.INACTIVO
        self.domain.cliente.save(update_fields=["estado", "actualizado_en"])

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("cliente", form.errors)

    def test_no_permite_profesional_inactivo(self):
        self.domain.profesional.estado = EstadoProfesional.INACTIVO
        self.domain.profesional.save(update_fields=["estado", "actualizado_en"])

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_profesional_que_no_acepta_turnos(self):
        self.domain.profesional.acepta_turnos = False
        self.domain.profesional.save(update_fields=["acepta_turnos", "actualizado_en"])

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("profesional", form.errors)

    def test_no_permite_sucursal_inactiva(self):
        self.domain.sucursal.estado = EstadoSucursal.INACTIVA
        self.domain.sucursal.save(update_fields=["estado", "actualizado_en"])

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("sucursal", form.errors)

    def test_no_permite_sucursal_que_no_acepta_turnos(self):
        self.domain.sucursal.acepta_turnos = False
        self.domain.sucursal.save(update_fields=["acepta_turnos", "actualizado_en"])

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("sucursal", form.errors)

    def test_no_permite_solapamiento_parcial(self):
        self._crear_turno(inicio=self.inicio, fin=self.inicio + timedelta(hours=1))
        inicio_solapado = aware_datetime_for_date(self.fecha, 10, 30)

        form = TurnoForm(data=turno_form_data(self.domain, inicio=inicio_solapado))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_no_permite_mismo_horario_exacto_si_el_turno_existente_esta_activo(self):
        self._crear_turno(inicio=self.inicio, estado=EstadoTurno.CONFIRMADO)

        form = TurnoForm(data=turno_form_data(self.domain, inicio=self.inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_permite_mismo_horario_si_el_turno_existente_no_esta_activo(self):
        estados_no_activos = (
            EstadoTurno.CANCELADO,
            EstadoTurno.COMPLETADO,
            EstadoTurno.AUSENTE,
        )
        for estado in estados_no_activos:
            with self.subTest(estado=estado):
                domain = create_domain(prefix=f"Turno {estado}")
                fecha = future_date(days=12)
                inicio = aware_datetime_for_date(fecha, 10, 0)
                create_availability(domain, date_value=fecha)
                self._crear_turno(domain=domain, inicio=inicio, estado=estado)

                form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

                self.assertTrue(form.is_valid(), form.errors)

    def test_permite_turno_miercoles_en_disponibilidad_lunes_a_viernes(self):
        domain = create_domain(prefix="Turno Miercoles")
        fecha = self._fecha_con_weekday(2)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha, dias_semana=[0, 1, 2, 3, 4])

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertTrue(form.is_valid(), form.errors)

    def test_no_permite_turno_sabado_fuera_de_lunes_a_viernes(self):
        domain = create_domain(prefix="Turno Sabado")
        fecha = self._fecha_con_weekday(5)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha, dias_semana=[0, 1, 2, 3, 4])

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def _crear_excepcion(self, *, tipo, sucursal=None, profesional=None, activo=True):
        return ExcepcionAgenda.objects.create(
            negocio=self.domain.negocio,
            sucursal=sucursal,
            profesional=profesional,
            tipo=tipo,
            titulo="Bloqueo de prueba",
            fecha_hora_inicio=self.inicio - timedelta(minutes=30),
            fecha_hora_fin=self.inicio + timedelta(minutes=90),
            activo=activo,
        )

    def _crear_turno(self, *, domain=None, inicio=None, fin=None, estado=EstadoTurno.SOLICITADO):
        if domain is None:
            domain = self.domain
        if inicio is None:
            inicio = self.inicio
        if fin is None:
            fin = inicio + timedelta(minutes=domain.servicio.duracion_minutos)

        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=domain.profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=fin,
            estado=estado,
        )

    def _fecha_con_weekday(self, weekday):
        fecha = future_date(days=10)
        while fecha.weekday() != weekday:
            fecha += timedelta(days=1)
        return fecha


class ConfiguracionAplicadaTurnoFormTests(TestCase):
    def test_si_no_hay_configuracion_usa_defaults_seguros(self):
        domain = create_domain(prefix="Turno Sin Config")
        fecha = future_date(days=3)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertTrue(form.is_valid(), form.errors)
        turno = form.save()
        self.assertEqual(turno.estado, EstadoTurno.SOLICITADO)
        self.assertIsNone(turno.confirmado_en)

    def test_anticipacion_minima_bloquea_turno_demasiado_cercano(self):
        domain = self._domain_configurado(
            anticipacion_minima_reserva_minutos=7 * 24 * 60,
        )
        fecha = future_date(days=2)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_anticipacion_maxima_bloquea_turno_demasiado_lejano(self):
        domain = self._domain_configurado(anticipacion_maxima_reserva_dias=5)
        fecha = future_date(days=6)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_buffer_entre_turnos_bloquea_turnos_pegados(self):
        domain = self._domain_configurado(buffer_entre_turnos_minutos=10)
        fecha = future_date(days=4)
        inicio_existente = aware_datetime_for_date(fecha, 10, 0)
        inicio_nuevo = aware_datetime_for_date(fecha, 11, 0)
        create_availability(domain, date_value=fecha)
        self._crear_turno_directo(domain, inicio_existente)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio_nuevo))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_confirmacion_automatica_crea_turno_confirmado(self):
        domain = self._domain_configurado(
            politica_confirmacion=PoliticaConfirmacion.AUTOMATICA,
        )
        fecha = future_date(days=5)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertTrue(form.is_valid(), form.errors)
        turno = form.save()
        self.assertEqual(turno.estado, EstadoTurno.CONFIRMADO)
        self.assertIsNotNone(turno.confirmado_en)

    def test_sin_confirmacion_automatica_crea_turno_solicitado(self):
        domain = self._domain_configurado(
            politica_confirmacion=PoliticaConfirmacion.MANUAL,
        )
        fecha = future_date(days=5)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertTrue(form.is_valid(), form.errors)
        turno = form.save()
        self.assertEqual(turno.estado, EstadoTurno.SOLICITADO)
        self.assertIsNone(turno.confirmado_en)

    def test_permite_turnos_pasados_false_bloquea_pasado(self):
        domain = self._domain_configurado(permite_turnos_pasados=False)
        fecha = timezone.localdate() - timedelta(days=1)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertFalse(form.is_valid())
        self.assertIn("fecha_hora_inicio", form.errors)

    def test_permite_turnos_pasados_true_permite_pasado(self):
        domain = self._domain_configurado(permite_turnos_pasados=True)
        fecha = timezone.localdate() - timedelta(days=1)
        inicio = aware_datetime_for_date(fecha, 10, 0)
        create_availability(domain, date_value=fecha)

        form = TurnoForm(data=turno_form_data(domain, inicio=inicio))

        self.assertTrue(form.is_valid(), form.errors)

    def _domain_configurado(self, **config_kwargs):
        domain = create_domain(
            prefix="Turno Config",
            servicio_kwargs={"duracion_minutos": 60},
        )
        data = {
            "negocio": domain.negocio,
            "politica_confirmacion": PoliticaConfirmacion.MANUAL,
            "anticipacion_minima_reserva_minutos": 0,
            "anticipacion_maxima_reserva_dias": 30,
            "tiempo_minimo_cancelacion_minutos": 0,
        }
        data.update(config_kwargs)
        ConfiguracionNegocio.objects.create(**data)
        return domain

    def _crear_turno_directo(self, domain, inicio, estado=EstadoTurno.SOLICITADO):
        return Turno.objects.create(
            negocio=domain.negocio,
            sucursal=domain.sucursal,
            cliente=domain.cliente,
            profesional=domain.profesional,
            servicio=domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=domain.servicio.duracion_minutos),
            estado=estado,
        )


class TurnoEstadoViewsTests(TestCase):
    def setUp(self):
        self.domain = create_domain(prefix="Estado Turno")
        self.user = create_user(username="estado-turnos")
        create_miembro(
            self.user,
            self.domain.negocio,
            rol=RolMiembroNegocio.ADMIN_NEGOCIO,
        )
        self.client.force_login(self.user)
        self.fecha = future_date(days=20)
        create_availability(self.domain, date_value=self.fecha)

    def test_acciones_de_estado(self):
        casos = (
            ("turnos:confirmar", EstadoTurno.CONFIRMADO),
            ("turnos:completar", EstadoTurno.COMPLETADO),
            ("turnos:ausente", EstadoTurno.AUSENTE),
            ("turnos:cancelar", EstadoTurno.CANCELADO),
        )

        for index, (url_name, estado_esperado) in enumerate(casos, start=10):
            with self.subTest(url_name=url_name):
                turno = self._crear_turno(index)
                response = self.client.post(
                    reverse(url_name, kwargs={"pk": turno.pk}),
                    {"motivo_cancelacion": "No asiste"},
                )
                turno.refresh_from_db()

                self.assertEqual(response.status_code, 302)
                self.assertEqual(turno.estado, estado_esperado)
                if estado_esperado == EstadoTurno.CONFIRMADO:
                    self.assertIsNotNone(turno.confirmado_en)
                if estado_esperado == EstadoTurno.CANCELADO:
                    self.assertIsNotNone(turno.cancelado_en)
                    self.assertEqual(turno.motivo_cancelacion, "No asiste")

    def test_permite_cancelacion_false_bloquea_cancelacion(self):
        ConfiguracionNegocio.objects.create(
            negocio=self.domain.negocio,
            permite_cancelacion_online=False,
            tiempo_minimo_cancelacion_minutos=0,
        )
        turno = self._crear_turno(10)

        response = self.client.post(reverse("turnos:cancelar", kwargs={"pk": turno.pk}))
        turno.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(turno.estado, EstadoTurno.SOLICITADO)
        self.assertIsNone(turno.cancelado_en)

    def test_tiempo_minimo_cancelacion_bloquea_cancelacion_tardia(self):
        ConfiguracionNegocio.objects.create(
            negocio=self.domain.negocio,
            permite_cancelacion_online=True,
            tiempo_minimo_cancelacion_minutos=12 * 60,
        )
        inicio = timezone.now() + timedelta(hours=6)
        turno = self._crear_turno_con_inicio(inicio)

        response = self.client.post(reverse("turnos:cancelar", kwargs={"pk": turno.pk}))
        turno.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(turno.estado, EstadoTurno.SOLICITADO)
        self.assertIsNone(turno.cancelado_en)

    def test_cancelacion_permitida_funciona_si_respeta_configuracion(self):
        ConfiguracionNegocio.objects.create(
            negocio=self.domain.negocio,
            permite_cancelacion_online=True,
            tiempo_minimo_cancelacion_minutos=6 * 60,
        )
        inicio = timezone.now() + timedelta(hours=12)
        turno = self._crear_turno_con_inicio(inicio)

        response = self.client.post(
            reverse("turnos:cancelar", kwargs={"pk": turno.pk}),
            {"motivo_cancelacion": "Cambio de horario"},
        )
        turno.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(turno.estado, EstadoTurno.CANCELADO)
        self.assertIsNotNone(turno.cancelado_en)
        self.assertEqual(turno.motivo_cancelacion, "Cambio de horario")

    def _crear_turno(self, hour):
        inicio = aware_datetime_for_date(self.fecha, hour, 0)
        return Turno.objects.create(
            negocio=self.domain.negocio,
            sucursal=self.domain.sucursal,
            cliente=self.domain.cliente,
            profesional=self.domain.profesional,
            servicio=self.domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=self.domain.servicio.duracion_minutos),
        )

    def _crear_turno_con_inicio(self, inicio):
        return Turno.objects.create(
            negocio=self.domain.negocio,
            sucursal=self.domain.sucursal,
            cliente=self.domain.cliente,
            profesional=self.domain.profesional,
            servicio=self.domain.servicio,
            fecha_hora_inicio=inicio,
            fecha_hora_fin=inicio + timedelta(minutes=self.domain.servicio.duracion_minutos),
        )
