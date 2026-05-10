from django import forms
from django.utils.text import slugify

from usuarios.form_utils import limitar_querysets_por_usuario

from .models import Servicio


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = [
            "negocio",
            "nombre",
            "descripcion",
            "categoria",
            "duracion_minutos",
            "precio",
            "estado",
            "visible_en_reserva_online",
            "orden_visualizacion",
        ]
        labels = {
            "negocio": "Negocio",
            "nombre": "Nombre",
            "descripcion": "Descripcion",
            "categoria": "Categoria",
            "duracion_minutos": "Duracion en minutos",
            "precio": "Precio",
            "estado": "Estado",
            "visible_en_reserva_online": "Visible en reserva online",
            "orden_visualizacion": "Orden de visualizacion",
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "duracion_minutos": forms.NumberInput(attrs={"min": "1"}),
            "orden_visualizacion": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        limitar_querysets_por_usuario(self, self.user, gestion_negocio=True)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox-input")
            else:
                field.widget.attrs.setdefault("class", "input")

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_descripcion(self):
        return self.cleaned_data["descripcion"].strip()

    def clean_categoria(self):
        return self.cleaned_data["categoria"].strip()

    def clean_duracion_minutos(self):
        duracion = self.cleaned_data["duracion_minutos"]
        if duracion <= 0:
            raise forms.ValidationError("La duracion debe ser mayor a cero.")
        return duracion

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio

    def clean(self):
        cleaned_data = super().clean()
        negocio = cleaned_data.get("negocio")
        nombre = cleaned_data.get("nombre", "")
        slug = self.instance.slug or slugify(nombre)

        if negocio and slug:
            servicios = Servicio.objects.filter(negocio=negocio, slug=slug)
            if self.instance.pk:
                servicios = servicios.exclude(pk=self.instance.pk)
            if servicios.exists():
                self.add_error(
                    "nombre",
                    "Ya existe un servicio con ese nombre en este negocio.",
                )

        return cleaned_data
