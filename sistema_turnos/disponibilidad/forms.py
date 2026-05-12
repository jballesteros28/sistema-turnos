from django import forms

from profesional.models import EstadoProfesional
from sucursal.models import EstadoSucursal
from usuarios.form_utils import limitar_querysets_por_usuario

from .models import DiaSemana, Disponibilidad, normalizar_dias_semana


class DisponibilidadForm(forms.ModelForm):
    dias_semana = forms.TypedMultipleChoiceField(
        choices=DiaSemana.choices,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        label="Dias de atencion",
        required=True,
        error_messages={
            "required": "Selecciona al menos un dia de atencion.",
        },
    )

    class Meta:
        model = Disponibilidad
        fields = [
            "negocio",
            "sucursal",
            "profesional",
            "dias_semana",
            "hora_inicio",
            "hora_fin",
            "fecha_desde",
            "fecha_hasta",
            "activo",
        ]
        labels = {
            "negocio": "Negocio",
            "sucursal": "Sucursal",
            "profesional": "Profesional",
            "dias_semana": "Dias de atencion",
            "hora_inicio": "Hora de inicio",
            "hora_fin": "Hora de fin",
            "fecha_desde": "Fecha desde",
            "fecha_hasta": "Fecha hasta",
            "activo": "Activa",
        }
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),
            "fecha_desde": forms.DateInput(attrs={"type": "date"}),
            "fecha_hasta": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        limitar_querysets_por_usuario(self, self.user, gestion_operacion=True)

        if self.instance.pk and not self.is_bound:
            self.fields["dias_semana"].initial = self.instance.dias_semana_normalizados()

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.setdefault("class", "weekday-checkboxes")
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            else:
                field.widget.attrs.setdefault("class", "input")

    def clean_dias_semana(self):
        dias_semana = normalizar_dias_semana(self.cleaned_data["dias_semana"])
        if not dias_semana:
            raise forms.ValidationError("Selecciona al menos un dia de atencion.")
        return dias_semana

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        sucursal = cleaned_data.get("sucursal")
        profesional = cleaned_data.get("profesional")
        dias_semana = cleaned_data.get("dias_semana") or []
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")
        fecha_desde = cleaned_data.get("fecha_desde")
        fecha_hasta = cleaned_data.get("fecha_hasta")

        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            self.add_error("hora_fin", "La hora de fin debe ser posterior a la hora de inicio.")

        if fecha_desde and fecha_hasta and fecha_hasta < fecha_desde:
            self.add_error("fecha_hasta", "La fecha hasta no puede ser anterior a la fecha desde.")

        if negocio and sucursal and sucursal.negocio_id != negocio.id:
            self.add_error(
                "sucursal",
                "La sucursal seleccionada debe pertenecer al negocio seleccionado.",
            )

        if negocio and profesional and profesional.negocio_id != negocio.id:
            self.add_error(
                "profesional",
                "El profesional seleccionado debe pertenecer al negocio seleccionado.",
            )

        if sucursal and sucursal.estado != EstadoSucursal.ACTIVA:
            self.add_error("sucursal", "La sucursal debe estar activa.")

        if sucursal and not sucursal.acepta_turnos:
            self.add_error("sucursal", "La sucursal debe aceptar turnos.")

        if profesional and profesional.estado != EstadoProfesional.ACTIVO:
            self.add_error("profesional", "El profesional debe estar activo.")

        if profesional and not profesional.acepta_turnos:
            self.add_error("profesional", "El profesional debe aceptar turnos.")

        if sucursal and profesional and not profesional.sucursales.filter(pk=sucursal.pk).exists():
            self.add_error(
                "profesional",
                "El profesional debe estar asociado a la sucursal seleccionada.",
            )

        if negocio and sucursal and profesional and dias_semana and hora_inicio and hora_fin:
            disponibilidades = Disponibilidad.objects.filter(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
            )
            if self.instance.pk:
                disponibilidades = disponibilidades.exclude(pk=self.instance.pk)
            for disponibilidad in disponibilidades:
                dias_compartidos = set(dias_semana).intersection(
                    disponibilidad.dias_semana_normalizados()
                )
                horarios_solapados = (
                    hora_inicio < disponibilidad.hora_fin
                    and hora_fin > disponibilidad.hora_inicio
                )
                if dias_compartidos and horarios_solapados:
                    self.add_error(
                        "hora_inicio",
                        (
                            "Ya existe una disponibilidad con dias y horarios "
                            "superpuestos."
                        ),
                    )
                    break

        return cleaned_data

    def save(self, commit=True):
        self.instance.dias_semana = self.cleaned_data["dias_semana"]
        if self.instance.dias_semana:
            self.instance.dia_semana = self.instance.dias_semana[0]
        return super().save(commit=commit)
