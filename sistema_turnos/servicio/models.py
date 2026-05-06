from django.db import models
from django.utils.text import slugify


class EstadoServicio(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"


class Servicio(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="servicios",
    )
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=120, blank=True)

    estado = models.CharField(
        max_length=15,
        choices=EstadoServicio.choices,
        default=EstadoServicio.ACTIVO,
    )
    duracion_minutos = models.PositiveSmallIntegerField(default=30)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    visible_en_reserva_online = models.BooleanField(default=True)
    orden_visualizacion = models.PositiveSmallIntegerField(default=0)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["negocio", "orden_visualizacion", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "slug"],
                name="uniq_servicio_slug_negocio",
            ),
            models.CheckConstraint(
                condition=models.Q(duracion_minutos__gt=0),
                name="ck_servicio_duracion_pos",
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gte=0),
                name="ck_servicio_precio_no_neg",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
