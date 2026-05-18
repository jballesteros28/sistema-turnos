from django import forms
from django.utils import timezone

from profesional.models import Profesional
from servicio.models import Servicio
from sucursal.models import Sucursal

from .services import (
    get_profesionales_publicos,
    get_servicios_publicos,
    get_sucursales_publicas,
)


class SeleccionTurnoForm(forms.Form):
    sucursal = forms.ModelChoiceField(
        label="Sucursal",
        queryset=Sucursal.objects.none(),
        empty_label=None,
    )
    servicio = forms.ModelChoiceField(
        label="Servicio",
        queryset=Servicio.objects.none(),
        empty_label=None,
    )
    profesional = forms.ModelChoiceField(
        label="Profesional",
        queryset=Profesional.objects.none(),
        required=False,
        empty_label="Cualquier profesional disponible",
    )
    fecha = forms.DateField(
        label="Fecha",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, negocio, *args, **kwargs):
        self.negocio = negocio
        super().__init__(*args, **kwargs)
        self.label_suffix = ""

        sucursales = get_sucursales_publicas(negocio)
        servicios = get_servicios_publicos(negocio)
        sucursal = self._get_selected_object("sucursal", sucursales)
        servicio = self._get_selected_object("servicio", servicios)

        self.fields["sucursal"].queryset = sucursales
        self.fields["servicio"].queryset = servicios
        self.fields["profesional"].queryset = get_profesionales_publicos(
            negocio,
            sucursal=sucursal,
            servicio=servicio,
        )
        self.fields["fecha"].widget.attrs.setdefault(
            "min",
            timezone.localdate().isoformat(),
        )

        if not self.is_bound:
            self.initial.setdefault("fecha", timezone.localdate().isoformat())

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "reservas-input")

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha < timezone.localdate():
            raise forms.ValidationError("Elegi una fecha actual o futura.")
        return fecha

    def _get_selected_object(self, field_name, queryset):
        value = None
        if self.is_bound:
            value = self.data.get(field_name)
        else:
            value = self.initial.get(field_name)

        if not value:
            return None

        try:
            return queryset.get(pk=value)
        except (queryset.model.DoesNotExist, TypeError, ValueError):
            return None


class DatosClienteReservaForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=120)
    apellido = forms.CharField(label="Apellido", max_length=120)
    email = forms.EmailField(label="Email", required=False)
    telefono = forms.CharField(label="Telefono", max_length=20, required=False)
    website = forms.CharField(
        label="Website",
        required=False,
        widget=forms.URLInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
            }
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "reservas-input")

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if not nombre:
            raise forms.ValidationError("Ingresa tu nombre.")
        return nombre

    def clean_apellido(self):
        apellido = self.cleaned_data["apellido"].strip()
        if not apellido:
            raise forms.ValidationError("Ingresa tu apellido.")
        return apellido

    def clean_email(self):
        return self.cleaned_data.get("email", "").strip().lower()

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono", "").strip()
        digitos = "".join(caracter for caracter in telefono if caracter.isdigit())
        if telefono and len(digitos) < 6:
            raise forms.ValidationError("Ingresa un telefono valido.")
        return telefono

    def clean_website(self):
        return self.cleaned_data.get("website", "").strip()

    def clean_observaciones(self):
        return self.cleaned_data.get("observaciones", "").strip()

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website"):
            raise forms.ValidationError(
                "No pudimos procesar la reserva. Intenta nuevamente."
            )
        if not cleaned_data.get("email") and not cleaned_data.get("telefono"):
            raise forms.ValidationError("Ingresa un email o un telefono de contacto.")
        return cleaned_data
