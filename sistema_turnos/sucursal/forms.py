from django import forms
from django.utils.text import slugify

from .models import Sucursal


class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = [
            "negocio",
            "nombre",
            "estado",
            "direccion",
            "ciudad",
            "provincia_estado",
            "pais",
            "codigo_postal",
            "referencia_direccion",
            "email",
            "telefono",
            "whatsapp",
            "zona_horaria",
            "es_principal",
            "acepta_turnos",
        ]
        labels = {
            "negocio": "Negocio",
            "nombre": "Nombre",
            "estado": "Estado",
            "direccion": "Direccion",
            "ciudad": "Ciudad",
            "provincia_estado": "Provincia o estado",
            "pais": "Pais",
            "codigo_postal": "Codigo postal",
            "referencia_direccion": "Referencia de direccion",
            "email": "Email",
            "telefono": "Telefono",
            "whatsapp": "WhatsApp",
            "zona_horaria": "Zona horaria",
            "es_principal": "Es principal",
            "acepta_turnos": "Acepta turnos",
        }
        help_texts = {
            "zona_horaria": "Si queda vacia, se usara la zona horaria del negocio.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            else:
                field.widget.attrs.setdefault("class", "input")

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_direccion(self):
        return self.cleaned_data["direccion"].strip()

    def clean_ciudad(self):
        return self.cleaned_data["ciudad"].strip()

    def clean_provincia_estado(self):
        return self.cleaned_data["provincia_estado"].strip()

    def clean_pais(self):
        return self.cleaned_data["pais"].strip()

    def clean_codigo_postal(self):
        return self.cleaned_data["codigo_postal"].strip()

    def clean_referencia_direccion(self):
        return self.cleaned_data["referencia_direccion"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_telefono(self):
        return self.cleaned_data["telefono"].strip()

    def clean_whatsapp(self):
        return self.cleaned_data["whatsapp"].strip()

    def clean_zona_horaria(self):
        return self.cleaned_data["zona_horaria"].strip()

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        nombre = cleaned_data.get("nombre", "")
        slug = self.instance.slug or slugify(nombre)

        if negocio and slug:
            sucursales = Sucursal.objects.filter(negocio=negocio, slug=slug)
            if self.instance.pk:
                sucursales = sucursales.exclude(pk=self.instance.pk)
            if sucursales.exists():
                self.add_error(
                    "nombre",
                    "Ya existe una sucursal con ese nombre en este negocio.",
                )

        return cleaned_data
