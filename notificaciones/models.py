from django.db import models


class TipoNotificacionEmail(models.TextChoices):
    TURNO_CREADO = "turno_creado", "Turno creado"
    TURNO_CONFIRMADO = "turno_confirmado", "Turno confirmado"
    TURNO_CANCELADO = "turno_cancelado", "Turno cancelado"
    TURNO_COMPLETADO = "turno_completado", "Turno completado"
    TURNO_AUSENTE = "turno_ausente", "Turno ausente"
    TURNO_REPROGRAMADO = "turno_reprogramado", "Turno reprogramado"


class EstadoNotificacionEmail(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    ENVIADO = "enviado", "Enviado"
    FALLIDO = "fallido", "Fallido"


class NotificacionEmail(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificaciones_email",
    )
    turno = models.ForeignKey(
        "turnos.Turno",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificaciones_email",
    )
    destinatario_email = models.EmailField()
    destinatario_nombre = models.CharField(max_length=160, blank=True)
    tipo = models.CharField(max_length=30, choices=TipoNotificacionEmail.choices)
    asunto = models.CharField(max_length=255)
    estado = models.CharField(
        max_length=20,
        choices=EstadoNotificacionEmail.choices,
        default=EstadoNotificacionEmail.PENDIENTE,
    )
    mensaje_error = models.TextField(blank=True)
    enviado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notificacion email"
        verbose_name_plural = "Notificaciones email"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["negocio", "creado_en"]),
            models.Index(fields=["turno", "creado_en"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["tipo"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} para {self.destinatario_email}"
