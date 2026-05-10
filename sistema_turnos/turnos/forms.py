from datetime import timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from clientes.models import EstadoCliente
from configuracion_negocio.models import get_configuracion_turnos
from disponibilidad.models import Disponibilidad
from excepcion.models import ExcepcionAgenda
from profesional.models import EstadoProfesional
from servicio.models import EstadoServicio
from sucursal.models import EstadoSucursal
from usuarios.form_utils import limitar_querysets_por_usuario

from .models import EstadoTurno, Turno


ESTADOS_TURNO_ACTIVOS = [
    EstadoTurno.SOLICITADO,
    EstadoTurno.CONFIRMADO,
]


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"
    format = "%Y-%m-%dT%H:%M"


class TurnoForm(forms.ModelForm):
    class Meta:
        model = Turno
        fields = [
            "negocio",
            "sucursal",
            "cliente",
            "profesional",
            "servicio",
            "fecha_hora_inicio",
            "origen",
            "notas",
        ]
        labels = {
            "negocio": "Negocio",
            "sucursal": "Sucursal",
            "cliente": "Cliente",
            "profesional": "Profesional",
            "servicio": "Servicio",
            "fecha_hora_inicio": "Inicio",
            "origen": "Origen",
            "notas": "Notas",
        }
        help_texts = {
            "fecha_hora_inicio": "La hora de fin se calcula automaticamente segun la duracion del servicio.",
        }
        widgets = {
            "fecha_hora_inicio": DateTimeLocalInput(),
            "notas": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        self._configuracion_turnos = None
        self.fields["fecha_hora_inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        limitar_querysets_por_usuario(
            self,
            self.user,
            turnos=True,
            gestion_operacion=True,
        )

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            else:
                field.widget.attrs.setdefault("class", "input")

    def clean_notas(self):
        return self.cleaned_data["notas"].strip()

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        sucursal = cleaned_data.get("sucursal")
        cliente = cleaned_data.get("cliente")
        profesional = cleaned_data.get("profesional")
        servicio = cleaned_data.get("servicio")
        fecha_hora_inicio = cleaned_data.get("fecha_hora_inicio")
        self._configuracion_turnos = get_configuracion_turnos(negocio)

        fecha_hora_fin = None
        if fecha_hora_inicio and servicio:
            fecha_hora_fin = fecha_hora_inicio + timedelta(
                minutes=servicio.duracion_minutos
            )
            cleaned_data["fecha_hora_fin"] = fecha_hora_fin
            self.instance.fecha_hora_fin = fecha_hora_fin

        self._validar_coherencia_entidades(
            negocio=negocio,
            sucursal=sucursal,
            cliente=cliente,
            profesional=profesional,
            servicio=servicio,
        )

        if fecha_hora_inicio:
            self._validar_ventana_reserva(
                fecha_hora_inicio,
                self._configuracion_turnos,
            )

        if fecha_hora_inicio and fecha_hora_fin:
            self._validar_mismo_dia(fecha_hora_inicio, fecha_hora_fin)

        if negocio and sucursal and profesional and servicio and fecha_hora_inicio and fecha_hora_fin:
            self._validar_disponibilidad(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=fecha_hora_fin,
            )
            self._validar_excepciones(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=fecha_hora_fin,
            )
            self._validar_solapamientos(
                profesional=profesional,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=fecha_hora_fin,
                configuracion=self._configuracion_turnos,
            )

        return cleaned_data

    def save(self, commit=True):
        self.instance.fecha_hora_fin = self.cleaned_data["fecha_hora_fin"]
        if not self.instance.pk:
            configuracion = self._configuracion_turnos or get_configuracion_turnos(
                self.cleaned_data.get("negocio")
            )
            if configuracion.confirmacion_automatica:
                self.instance.estado = EstadoTurno.CONFIRMADO
                if not self.instance.confirmado_en:
                    self.instance.confirmado_en = timezone.now()
            else:
                self.instance.estado = EstadoTurno.SOLICITADO
        return super().save(commit=commit)

    def _validar_coherencia_entidades(
        self,
        *,
        negocio,
        sucursal,
        cliente,
        profesional,
        servicio,
    ):
        if negocio and sucursal and sucursal.negocio_id != negocio.id:
            self.add_error(
                "sucursal",
                "La sucursal seleccionada debe pertenecer al negocio seleccionado.",
            )

        if negocio and cliente and cliente.negocio_id != negocio.id:
            self.add_error(
                "cliente",
                "El cliente seleccionado debe pertenecer al negocio seleccionado.",
            )

        if negocio and profesional and profesional.negocio_id != negocio.id:
            self.add_error(
                "profesional",
                "El profesional seleccionado debe pertenecer al negocio seleccionado.",
            )

        if negocio and servicio and servicio.negocio_id != negocio.id:
            self.add_error(
                "servicio",
                "El servicio seleccionado debe pertenecer al negocio seleccionado.",
            )

        if sucursal and sucursal.estado != EstadoSucursal.ACTIVA:
            self.add_error("sucursal", "La sucursal debe estar activa.")

        if sucursal and not sucursal.acepta_turnos:
            self.add_error("sucursal", "La sucursal debe aceptar turnos.")

        if cliente and cliente.estado != EstadoCliente.ACTIVO:
            self.add_error("cliente", "El cliente debe estar activo.")

        if profesional and profesional.estado != EstadoProfesional.ACTIVO:
            self.add_error("profesional", "El profesional debe estar activo.")

        if profesional and not profesional.acepta_turnos:
            self.add_error("profesional", "El profesional debe aceptar turnos.")

        if servicio and servicio.estado != EstadoServicio.ACTIVO:
            self.add_error("servicio", "El servicio debe estar activo.")

        if sucursal and profesional and not profesional.sucursales.filter(pk=sucursal.pk).exists():
            self.add_error(
                "profesional",
                "El profesional debe estar asociado a la sucursal seleccionada.",
            )

        if profesional and servicio and not profesional.servicios.filter(pk=servicio.pk).exists():
            self.add_error(
                "servicio",
                "El profesional debe prestar el servicio seleccionado.",
            )

    def _validar_ventana_reserva(self, fecha_hora_inicio, configuracion):
        inicio = self._aware_datetime(fecha_hora_inicio)
        ahora = timezone.now()

        if inicio <= ahora:
            if not configuracion.permite_turnos_pasados:
                self.add_error(
                    "fecha_hora_inicio",
                    "No se pueden crear turnos en fecha u hora pasada.",
                )
            return

        anticipacion_minima = configuracion.anticipacion_minima_reserva_minutos
        if anticipacion_minima and inicio < ahora + timedelta(minutes=anticipacion_minima):
            self.add_error(
                "fecha_hora_inicio",
                (
                    "El negocio requiere una anticipacion minima de "
                    f"{anticipacion_minima} minutos para reservar."
                ),
            )

        anticipacion_maxima = configuracion.anticipacion_maxima_reserva_dias
        if anticipacion_maxima and inicio > ahora + timedelta(days=anticipacion_maxima):
            self.add_error(
                "fecha_hora_inicio",
                (
                    "No se pueden crear turnos con mas de "
                    f"{anticipacion_maxima} dias de anticipacion."
                ),
            )

    def _validar_mismo_dia(self, fecha_hora_inicio, fecha_hora_fin):
        inicio_local = self._localtime(fecha_hora_inicio)
        fin_local = self._localtime(fecha_hora_fin)
        if inicio_local.date() != fin_local.date():
            self.add_error(
                "fecha_hora_inicio",
                "El turno debe comenzar y terminar el mismo dia.",
            )

    def _validar_disponibilidad(
        self,
        *,
        negocio,
        sucursal,
        profesional,
        fecha_hora_inicio,
        fecha_hora_fin,
    ):
        inicio_local = self._localtime(fecha_hora_inicio)
        fin_local = self._localtime(fecha_hora_fin)
        fecha_turno = inicio_local.date()

        disponibilidades = Disponibilidad.objects.filter(
            negocio=negocio,
            sucursal=sucursal,
            profesional=profesional,
            dia_semana=inicio_local.weekday(),
            activo=True,
            hora_inicio__lte=inicio_local.time(),
            hora_fin__gte=fin_local.time(),
        ).filter(
            Q(fecha_desde__isnull=True) | Q(fecha_desde__lte=fecha_turno),
            Q(fecha_hasta__isnull=True) | Q(fecha_hasta__gte=fecha_turno),
        )

        if not disponibilidades.exists():
            self.add_error(
                "fecha_hora_inicio",
                "El turno debe caer dentro de una disponibilidad activa.",
            )

    def _validar_excepciones(
        self,
        *,
        negocio,
        sucursal,
        profesional,
        fecha_hora_inicio,
        fecha_hora_fin,
    ):
        excepciones = ExcepcionAgenda.objects.filter(
            negocio=negocio,
            activo=True,
            bloquea_turnos=True,
            fecha_hora_inicio__lt=fecha_hora_fin,
            fecha_hora_fin__gt=fecha_hora_inicio,
        ).filter(
            Q(sucursal__isnull=True, profesional__isnull=True)
            | Q(sucursal=sucursal, profesional__isnull=True)
            | Q(profesional=profesional)
        )

        if excepciones.exists():
            self.add_error(
                "fecha_hora_inicio",
                "El turno cae dentro de una excepcion activa de agenda.",
            )

    def _validar_solapamientos(
        self,
        *,
        profesional,
        fecha_hora_inicio,
        fecha_hora_fin,
        configuracion,
    ):
        buffer_minutos = configuracion.buffer_entre_turnos_minutos or 0
        buffer_delta = timedelta(minutes=buffer_minutos)
        turnos = Turno.objects.filter(
            profesional=profesional,
            estado__in=ESTADOS_TURNO_ACTIVOS,
            fecha_hora_inicio__lt=fecha_hora_fin + buffer_delta,
            fecha_hora_fin__gt=fecha_hora_inicio - buffer_delta,
        )
        if self.instance.pk:
            turnos = turnos.exclude(pk=self.instance.pk)

        if turnos.exists():
            if buffer_minutos:
                self.add_error(
                    "fecha_hora_inicio",
                    f"Debe respetarse un buffer de {buffer_minutos} minutos entre turnos.",
                )
                return

            self.add_error(
                "fecha_hora_inicio",
                "El turno se solapa con otro turno activo del profesional.",
            )

    def _aware_datetime(self, value):
        if timezone.is_naive(value):
            return timezone.make_aware(value)
        return value

    def _localtime(self, value):
        return timezone.localtime(self._aware_datetime(value))
