from django import forms
from django.utils.text import slugify

from .models import Negocio


class NegocioForm(forms.ModelForm):
    class Meta:
        model = Negocio
        fields = [
            "nombre",
            "nombre_visible",
            "tipo_negocio",
            "descripcion",
            "estado",
            "email_principal",
            "telefono_principal",
            "whatsapp_principal",
            "sitio_web",
            "instagram",
            "direccion_principal",
            "ciudad",
            "provincia_estado",
            "pais",
            "codigo_postal",
            "zona_horaria",
            "moneda",
            "idioma",
            "color_primario",
            "color_secundario",
        ]
        labels = {
            "nombre": "Nombre",
            "nombre_visible": "Nombre visible",
            "tipo_negocio": "Tipo de negocio",
            "descripcion": "Descripcion",
            "estado": "Estado",
            "email_principal": "Email principal",
            "telefono_principal": "Telefono principal",
            "whatsapp_principal": "WhatsApp principal",
            "sitio_web": "Sitio web",
            "instagram": "Instagram",
            "direccion_principal": "Direccion principal",
            "ciudad": "Ciudad",
            "provincia_estado": "Provincia o estado",
            "pais": "Pais",
            "codigo_postal": "Codigo postal",
            "zona_horaria": "Zona horaria",
            "moneda": "Moneda",
            "idioma": "Idioma",
            "color_primario": "Color primario",
            "color_secundario": "Color secundario",
        }
        help_texts = {
            "color_primario": "Formato sugerido: #0f766e.",
            "color_secundario": "Formato sugerido: #2563eb.",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
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

    def clean_nombre_visible(self):
        return self.cleaned_data["nombre_visible"].strip()

    def clean_descripcion(self):
        return self.cleaned_data["descripcion"].strip()

    def clean_email_principal(self):
        return self.cleaned_data["email_principal"].strip().lower()

    def clean_telefono_principal(self):
        return self.cleaned_data["telefono_principal"].strip()

    def clean_whatsapp_principal(self):
        return self.cleaned_data["whatsapp_principal"].strip()

    def clean_instagram(self):
        return self.cleaned_data["instagram"].strip()

    def clean_direccion_principal(self):
        return self.cleaned_data["direccion_principal"].strip()

    def clean_ciudad(self):
        return self.cleaned_data["ciudad"].strip()

    def clean_provincia_estado(self):
        return self.cleaned_data["provincia_estado"].strip()

    def clean_pais(self):
        return self.cleaned_data["pais"].strip()

    def clean_codigo_postal(self):
        return self.cleaned_data["codigo_postal"].strip()

    def clean_zona_horaria(self):
        return self.cleaned_data["zona_horaria"].strip()

    def clean_color_primario(self):
        return self._clean_color("color_primario")

    def clean_color_secundario(self):
        return self._clean_color("color_secundario")

    def _clean_color(self, field_name):
        color = self.cleaned_data[field_name].strip()
        if color and (not color.startswith("#") or len(color) != 7):
            raise forms.ValidationError("Usa un color hexadecimal con formato #RRGGBB.")
        return color

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get("nombre", "")
        slug = self.instance.slug or slugify(nombre)

        if nombre:
            negocios = Negocio.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                negocios = negocios.exclude(pk=self.instance.pk)
            if negocios.exists():
                self.add_error("nombre", "Ya existe un negocio con ese nombre.")

        if slug:
            negocios = Negocio.objects.filter(slug=slug)
            if self.instance.pk:
                negocios = negocios.exclude(pk=self.instance.pk)
            if negocios.exists():
                self.add_error("nombre", "Ya existe un negocio con un slug equivalente.")

        return cleaned_data
