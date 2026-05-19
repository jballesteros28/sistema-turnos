from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class PoliticaConfirmacion(models.TextChoices):
    AUTOMATICA = "automatica", "Automatica"
    MANUAL = "manual", "Manual"


class ConfiguracionNegocio(models.Model):
    negocio = models.OneToOneField(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="configuracion",
    )

    permite_reserva_online = models.BooleanField(default=True)
    permite_cancelacion_online = models.BooleanField(default=True)
    politica_confirmacion = models.CharField(
        max_length=20,
        choices=PoliticaConfirmacion.choices,
        default=PoliticaConfirmacion.AUTOMATICA,
    )

    anticipacion_minima_reserva_minutos = models.PositiveIntegerField(default=60)
    anticipacion_maxima_reserva_dias = models.PositiveIntegerField(default=30)
    tiempo_minimo_cancelacion_minutos = models.PositiveIntegerField(default=120)
    buffer_default_minutos = models.PositiveSmallIntegerField(default=0)
    buffer_entre_turnos_minutos = models.PositiveIntegerField(default=0)
    intervalo_turnos_minutos = models.PositiveSmallIntegerField(default=15)
    recordatorio_horas_antes = models.PositiveSmallIntegerField(default=24)
    permite_turnos_pasados = models.BooleanField(default=False)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracion del negocio"
        verbose_name_plural = "Configuraciones de negocio"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(anticipacion_maxima_reserva_dias__gt=0),
                name="ck_conf_ant_max_dias_pos",
            ),
            models.CheckConstraint(
                condition=models.Q(intervalo_turnos_minutos__gt=0),
                name="ck_conf_intervalo_pos",
            ),
        ]

    def __str__(self):
        return f"Configuracion de {self.negocio}"

    @property
    def confirmacion_automatica(self):
        return self.politica_confirmacion == PoliticaConfirmacion.AUTOMATICA

    @property
    def permite_cancelacion(self):
        return self.permite_cancelacion_online


class ConfiguracionTurnosDefaults:
    permite_reserva_online = True
    permite_cancelacion_online = True
    politica_confirmacion = PoliticaConfirmacion.MANUAL
    anticipacion_minima_reserva_minutos = 0
    anticipacion_maxima_reserva_dias = 30
    tiempo_minimo_cancelacion_minutos = 0
    buffer_default_minutos = 0
    buffer_entre_turnos_minutos = 0
    intervalo_turnos_minutos = 15
    permite_turnos_pasados = False

    @property
    def confirmacion_automatica(self):
        return False

    @property
    def permite_cancelacion(self):
        return self.permite_cancelacion_online


def get_configuracion_turnos(negocio):
    if not negocio:
        return ConfiguracionTurnosDefaults()

    try:
        return negocio.configuracion
    except ObjectDoesNotExist:
        return ConfiguracionTurnosDefaults()
