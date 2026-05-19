from django import forms

from usuarios.form_utils import limitar_querysets_por_usuario

from .models import ExcepcionAgenda, TipoExcepcion


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"
    format = "%Y-%m-%dT%H:%M"


class ExcepcionAgendaForm(forms.ModelForm):
    class Meta:
        model = ExcepcionAgenda
        fields = [
            "negocio",
            "sucursal",
            "profesional",
            "tipo",
            "titulo",
            "descripcion",
            "fecha_hora_inicio",
            "fecha_hora_fin",
            "bloquea_turnos",
            "activo",
        ]
        labels = {
            "negocio": "Negocio",
            "sucursal": "Sucursal",
            "profesional": "Profesional",
            "tipo": "Tipo",
            "titulo": "Titulo",
            "descripcion": "Descripcion",
            "fecha_hora_inicio": "Inicio",
            "fecha_hora_fin": "Fin",
            "bloquea_turnos": "Bloquea turnos",
            "activo": "Activa",
        }
        help_texts = {
            "sucursal": "Dejar vacia para una excepcion de todo el negocio.",
            "profesional": "Dejar vacio si aplica a todo el negocio o a toda la sucursal.",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "fecha_hora_inicio": DateTimeLocalInput(),
            "fecha_hora_fin": DateTimeLocalInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        limitar_querysets_por_usuario(self, self.user, gestion_operacion=True)
        self.fields["fecha_hora_inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["fecha_hora_fin"].input_formats = ["%Y-%m-%dT%H:%M"]

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            else:
                field.widget.attrs.setdefault("class", "input")

    def clean_titulo(self):
        return self.cleaned_data["titulo"].strip()

    def clean_descripcion(self):
        return self.cleaned_data["descripcion"].strip()

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        sucursal = cleaned_data.get("sucursal")
        profesional = cleaned_data.get("profesional")
        tipo = cleaned_data.get("tipo")
        fecha_hora_inicio = cleaned_data.get("fecha_hora_inicio")
        fecha_hora_fin = cleaned_data.get("fecha_hora_fin")

        if fecha_hora_inicio and fecha_hora_fin and fecha_hora_inicio >= fecha_hora_fin:
            self.add_error(
                "fecha_hora_fin",
                "La fecha y hora de fin debe ser posterior al inicio.",
            )

        if tipo == TipoExcepcion.CIERRE_SUCURSAL and not sucursal:
            self.add_error(
                "sucursal",
                "Selecciona una sucursal para un cierre de sucursal.",
            )

        if tipo == TipoExcepcion.AUSENCIA_PROFESIONAL and not profesional:
            self.add_error(
                "profesional",
                "Selecciona un profesional para una ausencia profesional.",
            )

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

        if sucursal and profesional and not profesional.sucursales.filter(pk=sucursal.pk).exists():
            self.add_error(
                "profesional",
                "El profesional debe estar asociado a la sucursal seleccionada.",
            )

        if negocio and tipo and fecha_hora_inicio and fecha_hora_fin:
            excepciones = ExcepcionAgenda.objects.filter(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
                tipo=tipo,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=fecha_hora_fin,
            )
            if self.instance.pk:
                excepciones = excepciones.exclude(pk=self.instance.pk)
            if excepciones.exists():
                self.add_error(
                    "fecha_hora_inicio",
                    "Ya existe una excepcion exacta para ese alcance, tipo y horario.",
                )

        return cleaned_data
