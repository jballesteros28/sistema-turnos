from django.db import models


class DiaSemana(models.IntegerChoices):
    LUNES = 0, "Lunes"
    MARTES = 1, "Martes"
    MIERCOLES = 2, "Miercoles"
    JUEVES = 3, "Jueves"
    VIERNES = 4, "Viernes"
    SABADO = 5, "Sabado"
    DOMINGO = 6, "Domingo"


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

    def __str__(self):
        return (
            f"{self.profesional} - {self.sucursal} - "
            f"{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"
        )
