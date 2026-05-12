from django.db import models


class DiaSemana(models.IntegerChoices):
    LUNES = 0, "Lunes"
    MARTES = 1, "Martes"
    MIERCOLES = 2, "Miercoles"
    JUEVES = 3, "Jueves"
    VIERNES = 4, "Viernes"
    SABADO = 5, "Sabado"
    DOMINGO = 6, "Domingo"


DIAS_SEMANA_LABELS = dict(DiaSemana.choices)
DIAS_LUNES_A_VIERNES = [0, 1, 2, 3, 4]
DIAS_LUNES_A_SABADO = [0, 1, 2, 3, 4, 5]
DIAS_TODOS = [0, 1, 2, 3, 4, 5, 6]


def normalizar_dias_semana(dias_semana, dia_semana=None):
    dias = []

    for dia in dias_semana or []:
        try:
            dia_normalizado = int(dia)
        except (TypeError, ValueError):
            continue

        if dia_normalizado in DIAS_SEMANA_LABELS and dia_normalizado not in dias:
            dias.append(dia_normalizado)

    if not dias and dia_semana is not None:
        try:
            dia_legacy = int(dia_semana)
        except (TypeError, ValueError):
            dia_legacy = None

        if dia_legacy in DIAS_SEMANA_LABELS:
            dias.append(dia_legacy)

    return sorted(dias)


class Disponibilidad(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="disponibilidades",
    )
    sucursal = models.ForeignKey(
        "sucursal.Sucursal",
        on_delete=models.CASCADE,
        related_name="disponibilidades",
    )
    profesional = models.ForeignKey(
        "profesional.Profesional",
        on_delete=models.CASCADE,
        related_name="disponibilidades",
    )

    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices)
    dias_semana = models.JSONField(default=list)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    fecha_desde = models.DateField(null=True, blank=True)
    fecha_hasta = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Disponibilidad"
        verbose_name_plural = "Disponibilidades"
        ordering = ["negocio", "sucursal", "profesional", "dia_semana", "hora_inicio"]
        indexes = [
            models.Index(fields=["negocio", "dia_semana", "activo"]),
            models.Index(fields=["profesional", "dia_semana", "activo"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hora_fin__gt=models.F("hora_inicio")),
                name="ck_disp_hora_fin_gt_ini",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(fecha_hasta__isnull=True)
                    | models.Q(fecha_desde__isnull=True)
                    | models.Q(fecha_hasta__gte=models.F("fecha_desde"))
                ),
                name="ck_disp_fecha_fin_gte_ini",
            ),
        ]

    def dias_semana_normalizados(self):
        return normalizar_dias_semana(self.dias_semana, self.dia_semana)

    def incluye_dia(self, dia_semana):
        try:
            dia = int(dia_semana)
        except (TypeError, ValueError):
            return False
        return dia in self.dias_semana_normalizados()

    def dias_semana_display(self):
        dias = self.dias_semana_normalizados()
        if dias == DIAS_LUNES_A_VIERNES:
            return "Lunes a viernes"
        if dias == DIAS_LUNES_A_SABADO:
            return "Lunes a sabado"
        if dias == DIAS_TODOS:
            return "Todos los dias"
        if not dias:
            return "Sin dias"
        return ", ".join(DIAS_SEMANA_LABELS[dia] for dia in dias)

    def save(self, *args, **kwargs):
        self.dias_semana = self.dias_semana_normalizados()
        if self.dias_semana:
            self.dia_semana = self.dias_semana[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.profesional} - {self.sucursal} - "
            f"{self.dias_semana_display()} {self.hora_inicio}-{self.hora_fin}"
        )
