from django import forms
from django.utils import timezone
from django.utils.text import slugify

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "negocio",
            "nombre",
            "apellido",
            "nombre_visible",
            "email",
            "telefono",
            "whatsapp",
            "tipo_documento",
            "numero_documento",
            "fecha_nacimiento",
            "acepta_recordatorios",
            "estado",
            "notas",
        ]
        labels = {
            "negocio": "Negocio",
            "nombre": "Nombre",
            "apellido": "Apellido",
            "nombre_visible": "Nombre visible",
            "email": "Email",
            "telefono": "Telefono",
            "whatsapp": "WhatsApp",
            "tipo_documento": "Tipo de documento",
            "numero_documento": "Numero de documento",
            "fecha_nacimiento": "Fecha de nacimiento",
            "acepta_recordatorios": "Acepta recordatorios",
            "estado": "Estado",
            "notas": "Notas",
        }
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "notas": forms.Textarea(attrs={"rows": 4}),
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

    def clean_apellido(self):
        return self.cleaned_data["apellido"].strip()

    def clean_nombre_visible(self):
        return self.cleaned_data["nombre_visible"].strip()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_telefono(self):
        return self.cleaned_data["telefono"].strip()

    def clean_whatsapp(self):
        return self.cleaned_data["whatsapp"].strip()

    def clean_numero_documento(self):
        return self.cleaned_data["numero_documento"].strip()

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data["fecha_nacimiento"]
        if fecha_nacimiento and fecha_nacimiento > timezone.localdate():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura.")
        return fecha_nacimiento

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        nombre = cleaned_data.get("nombre", "")
        apellido = cleaned_data.get("apellido", "")
        nombre_visible = cleaned_data.get("nombre_visible") or f"{nombre} {apellido}".strip()
        slug = self.instance.slug or slugify(nombre_visible)

        if negocio and slug:
            clientes = Cliente.objects.filter(negocio=negocio, slug=slug)
            if self.instance.pk:
                clientes = clientes.exclude(pk=self.instance.pk)
            if clientes.exists():
                self.add_error(
                    "nombre_visible",
                    "Ya existe un cliente con ese nombre visible en este negocio.",
                )

        return cleaned_data
