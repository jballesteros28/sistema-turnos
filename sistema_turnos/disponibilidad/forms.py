from django import forms

from profesional.models import EstadoProfesional
from sucursal.models import EstadoSucursal
from usuarios.form_utils import limitar_querysets_por_usuario

from .models import Disponibilidad


class DisponibilidadForm(forms.ModelForm):
    class Meta:
        model = Disponibilidad
        fields = [
            "negocio",
            "sucursal",
            "profesional",
            "dia_semana",
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
            "dia_semana": "Dia de semana",
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
        limitar_querysets_por_usuario(self, self.user)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            else:
                field.widget.attrs.setdefault("class", "input")

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        sucursal = cleaned_data.get("sucursal")
        profesional = cleaned_data.get("profesional")
        dia_semana = cleaned_data.get("dia_semana")
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

        if negocio and sucursal and profesional and dia_semana is not None and hora_inicio and hora_fin:
            disponibilidades = Disponibilidad.objects.filter(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
                dia_semana=dia_semana,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
            )
            if self.instance.pk:
                disponibilidades = disponibilidades.exclude(pk=self.instance.pk)
            if disponibilidades.exists():
                self.add_error(
                    "hora_inicio",
                    "Ya existe una disponibilidad con esa misma franja.",
                )

        return cleaned_data
