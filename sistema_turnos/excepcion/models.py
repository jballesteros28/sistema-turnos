from django.db import models


class TipoExcepcion(models.TextChoices):
    CIERRE_NEGOCIO = "cierre_negocio", "Cierre del negocio"
    CIERRE_SUCURSAL = "cierre_sucursal", "Cierre de sucursal"
    AUSENCIA_PROFESIONAL = "ausencia_profesional", "Ausencia profesional"
    BLOQUEO_AGENDA = "bloqueo_agenda", "Bloqueo de agenda"
    FERIADO = "feriado", "Feriado"
    OTRO = "otro", "Otro"


class ExcepcionAgenda(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="excepciones",
    )
    sucursal = models.ForeignKey(
        "sucursal.Sucursal",
        on_delete=models.CASCADE,
        related_name="excepciones",
        null=True,
        blank=True,
    )
    profesional = models.ForeignKey(
        "profesional.Profesional",
        on_delete=models.CASCADE,
        related_name="excepciones",
        null=True,
        blank=True,
    )

    tipo = models.CharField(
        max_length=30,
        choices=TipoExcepcion.choices,
        default=TipoExcepcion.BLOQUEO_AGENDA,
    )
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    bloquea_turnos = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Excepcion de agenda"
        verbose_name_plural = "Excepciones de agenda"
        ordering = ["negocio", "fecha_hora_inicio"]
        indexes = [
            models.Index(fields=["negocio", "fecha_hora_inicio", "fecha_hora_fin"]),
            models.Index(fields=["profesional", "fecha_hora_inicio"]),
            models.Index(fields=["sucursal", "fecha_hora_inicio"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_hora_fin__gt=models.F("fecha_hora_inicio")),
                name="ck_exc_fin_gt_ini",
            ),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.fecha_hora_inicio:%Y-%m-%d %H:%M})"
