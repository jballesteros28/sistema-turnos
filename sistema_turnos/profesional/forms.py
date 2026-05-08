from django import forms
from django.utils.text import slugify

from usuarios.form_utils import limitar_querysets_por_usuario

from .models import Profesional


class ProfesionalForm(forms.ModelForm):
    class Meta:
        model = Profesional
        fields = [
            "negocio",
            "sucursales",
            "servicios",
            "nombre",
            "apellido",
            "nombre_visible",
            "tipo_profesional",
            "especialidad",
            "matricula",
            "descripcion_profesional",
            "email",
            "telefono",
            "whatsapp",
            "estado",
            "acepta_turnos",
            "duracion_buffer_minutos",
            "color_agenda",
            "visible_en_reserva_online",
            "orden_visualizacion",
        ]
        labels = {
            "negocio": "Negocio",
            "sucursales": "Sucursales",
            "servicios": "Servicios",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "nombre_visible": "Nombre visible",
            "tipo_profesional": "Tipo de profesional",
            "especialidad": "Especialidad",
            "matricula": "Matricula",
            "descripcion_profesional": "Descripcion profesional",
            "email": "Email",
            "telefono": "Telefono",
            "whatsapp": "WhatsApp",
            "estado": "Estado",
            "acepta_turnos": "Acepta turnos",
            "duracion_buffer_minutos": "Buffer entre turnos",
            "color_agenda": "Color de agenda",
            "visible_en_reserva_online": "Visible en reserva online",
            "orden_visualizacion": "Orden de visualizacion",
        }
        help_texts = {
            "sucursales": "Selecciona sucursales del mismo negocio.",
            "servicios": "Selecciona servicios del mismo negocio.",
            "color_agenda": "Formato sugerido: #0f766e.",
        }
        widgets = {
            "sucursales": forms.SelectMultiple(attrs={"size": 6}),
            "servicios": forms.SelectMultiple(attrs={"size": 6}),
            "descripcion_profesional": forms.Textarea(attrs={"rows": 4}),
            "duracion_buffer_minutos": forms.NumberInput(attrs={"min": "0"}),
            "orden_visualizacion": forms.NumberInput(attrs={"min": "0"}),
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

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_apellido(self):
        return self.cleaned_data["apellido"].strip()

    def clean_nombre_visible(self):
        return self.cleaned_data["nombre_visible"].strip()

    def clean_especialidad(self):
        return self.cleaned_data["especialidad"].strip()

    def clean_matricula(self):
        return self.cleaned_data["matricula"].strip()

    def clean_descripcion_profesional(self):
        return self.cleaned_data["descripcion_profesional"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_telefono(self):
        return self.cleaned_data["telefono"].strip()

    def clean_whatsapp(self):
        return self.cleaned_data["whatsapp"].strip()

    def clean_color_agenda(self):
        color = self.cleaned_data["color_agenda"].strip()
        if color and (not color.startswith("#") or len(color) != 7):
            raise forms.ValidationError("Usa un color hexadecimal con formato #RRGGBB.")
        return color

    def clean_duracion_buffer_minutos(self):
        buffer = self.cleaned_data["duracion_buffer_minutos"]
        if buffer < 0:
            raise forms.ValidationError("El buffer no puede ser negativo.")
        return buffer

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        sucursales = cleaned_data.get("sucursales")
        servicios = cleaned_data.get("servicios")
        nombre = cleaned_data.get("nombre", "")
        apellido = cleaned_data.get("apellido", "")
        nombre_visible = cleaned_data.get("nombre_visible") or f"{nombre} {apellido}".strip()
        slug = self.instance.slug or slugify(nombre_visible)

        if negocio and slug:
            profesionales = Profesional.objects.filter(negocio=negocio, slug=slug)
            if self.instance.pk:
                profesionales = profesionales.exclude(pk=self.instance.pk)
            if profesionales.exists():
                self.add_error(
                    "nombre_visible",
                    "Ya existe un profesional con ese nombre visible en este negocio.",
                )

        if negocio and sucursales:
            sucursales_invalidas = sucursales.exclude(negocio=negocio)
            if sucursales_invalidas.exists():
                self.add_error(
                    "sucursales",
                    "Todas las sucursales asignadas deben pertenecer al negocio seleccionado.",
                )

        if negocio and servicios:
            servicios_invalidos = servicios.exclude(negocio=negocio)
            if servicios_invalidos.exists():
                self.add_error(
                    "servicios",
                    "Todos los servicios asignados deben pertenecer al negocio seleccionado.",
                )

        return cleaned_data
