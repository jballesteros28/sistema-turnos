from django.db import models


class EstadoTurno(models.TextChoices):
    SOLICITADO = "solicitado", "Solicitado"
    CONFIRMADO = "confirmado", "Confirmado"
    CANCELADO = "cancelado", "Cancelado"
    COMPLETADO = "completado", "Completado"
    AUSENTE = "ausente", "Ausente"


class OrigenTurno(models.TextChoices):
    ADMIN = "admin", "Admin"
    ONLINE = "online", "Online"
    TELEFONO = "telefono", "Telefono"
    WHATSAPP = "whatsapp", "WhatsApp"


class Turno(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="turnos",
    )
    sucursal = models.ForeignKey(
        "sucursal.Sucursal",
        on_delete=models.PROTECT,
        related_name="turnos",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="turnos",
    )
    profesional = models.ForeignKey(
        "profesional.Profesional",
        on_delete=models.PROTECT,
        related_name="turnos",
    )
    servicio = models.ForeignKey(
        "servicio.Servicio",
        on_delete=models.PROTECT,
        related_name="turnos",
    )

    fecha_hora_inicio = models.DateTimeField()
    fecha_hora_fin = models.DateTimeField()
    estado = models.CharField(
        max_length=20,
        choices=EstadoTurno.choices,
        default=EstadoTurno.SOLICITADO,
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenTurno.choices,
        default=OrigenTurno.ADMIN,
    )

    notas = models.TextField(blank=True)
    motivo_cancelacion = models.CharField(max_length=250, blank=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    cancelado_en = models.DateTimeField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ["-fecha_hora_inicio"]
        indexes = [
            models.Index(fields=["negocio", "fecha_hora_inicio"]),
            models.Index(fields=["sucursal", "fecha_hora_inicio"]),
            models.Index(fields=["profesional", "fecha_hora_inicio"]),
            models.Index(fields=["cliente", "fecha_hora_inicio"]),
            models.Index(fields=["estado"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_hora_fin__gt=models.F("fecha_hora_inicio")),
                name="ck_turno_fin_gt_ini",
            ),
            models.UniqueConstraint(
                fields=["profesional", "fecha_hora_inicio"],
                condition=~models.Q(estado=EstadoTurno.CANCELADO),
                name="uniq_turno_prof_inicio_act",
            ),
        ]

    @property
    def duracion_minutos(self):
        if not self.fecha_hora_inicio or not self.fecha_hora_fin:
            return None
        segundos = (self.fecha_hora_fin - self.fecha_hora_inicio).total_seconds()
        return int(segundos // 60)

    def __str__(self):
        return (
            f"{self.fecha_hora_inicio:%Y-%m-%d %H:%M} - "
            f"{self.cliente} con {self.profesional}"
        )
