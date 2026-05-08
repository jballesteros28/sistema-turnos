from django.conf import settings
from django.db import models


class RolMiembroNegocio(models.TextChoices):
    SUPERADMIN = "superadmin", "Superadmin"
    ADMIN_NEGOCIO = "admin_negocio", "Admin negocio"
    RECEPCIONISTA = "recepcionista", "Recepcionista"
    PROFESIONAL = "profesional", "Profesional"


class MiembroNegocio(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membresias_negocio",
    )
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="miembros",
    )
    rol = models.CharField(
        max_length=20,
        choices=RolMiembroNegocio.choices,
        default=RolMiembroNegocio.RECEPCIONISTA,
    )
    profesional = models.ForeignKey(
        "profesional.Profesional",
        on_delete=models.SET_NULL,
        related_name="membresias_usuario",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Miembro de negocio"
        verbose_name_plural = "Miembros de negocio"
        ordering = ["negocio", "user__username"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "negocio"],
                name="uniq_miembro_user_negocio",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.negocio} ({self.get_rol_display()})"
