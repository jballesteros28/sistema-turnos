from django import forms

from usuarios.form_utils import limitar_querysets_por_usuario

from .models import ConfiguracionNegocio


class ConfiguracionNegocioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionNegocio
        fields = [
            "negocio",
            "permite_reserva_online",
            "permite_cancelacion_online",
            "politica_confirmacion",
            "anticipacion_minima_reserva_minutos",
            "anticipacion_maxima_reserva_dias",
            "buffer_entre_turnos_minutos",
            "buffer_default_minutos",
            "intervalo_turnos_minutos",
            "tiempo_minimo_cancelacion_minutos",
            "permite_turnos_pasados",
            "recordatorio_horas_antes",
        ]
        labels = {
            "negocio": "Negocio",
            "permite_reserva_online": "Permite reserva online",
            "permite_cancelacion_online": "Permite cancelacion",
            "politica_confirmacion": "Politica de confirmacion",
            "anticipacion_minima_reserva_minutos": "Anticipacion minima para reservar (minutos)",
            "anticipacion_maxima_reserva_dias": "Anticipacion maxima para reservar (dias)",
            "buffer_entre_turnos_minutos": "Buffer entre turnos (minutos)",
            "buffer_default_minutos": "Buffer default (minutos)",
            "intervalo_turnos_minutos": "Intervalo de turnos (minutos)",
            "tiempo_minimo_cancelacion_minutos": "Tiempo minimo para cancelar (minutos)",
            "permite_turnos_pasados": "Permite turnos pasados",
            "recordatorio_horas_antes": "Recordatorio (horas antes)",
        }
        help_texts = {
            "politica_confirmacion": "Automatica crea turnos confirmados; manual los deja solicitados.",
            "buffer_entre_turnos_minutos": "Margen minimo entre turnos activos del mismo profesional.",
            "permite_turnos_pasados": "Usar solo para carga administrativa o correcciones operativas.",
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

        if negocio:
            configuraciones = ConfiguracionNegocio.objects.filter(negocio=negocio)
            if self.instance.pk:
                configuraciones = configuraciones.exclude(pk=self.instance.pk)
            if configuraciones.exists():
                self.add_error(
                    "negocio",
                    "Este negocio ya tiene una configuracion.",
                )

        return cleaned_data
