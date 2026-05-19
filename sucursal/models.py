from django.db import models
from django.utils.text import slugify


class EstadoSucursal(models.TextChoices):
    ACTIVA = "activa", "Activa"
    INACTIVA = "inactiva", "Inactiva"
    SUSPENDIDA = "suspendida", "Suspendida"


class Sucursal(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="sucursales",
    )
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)

    estado = models.CharField(
        max_length=15,
        choices=EstadoSucursal.choices,
        default=EstadoSucursal.ACTIVA,
    )
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    motivo_cierre = models.CharField(max_length=250, blank=True)

    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=120)
    provincia_estado = models.CharField(max_length=120, blank=True)
    pais = models.CharField(max_length=120)
    codigo_postal = models.CharField(max_length=20, blank=True)
    referencia_direccion = models.CharField(max_length=250, blank=True)

    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    zona_horaria = models.CharField(max_length=100, blank=True)

    es_principal = models.BooleanField(default=False)
    acepta_turnos = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["negocio", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "slug"],
                name="uniq_sucursal_slug_negocio",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            # TODO: antes de produccion, generar slugs unicos por negocio.
            self.slug = slugify(self.nombre)
        if not self.zona_horaria and self.negocio_id:
            self.zona_horaria = self.negocio.zona_horaria
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.negocio.nombre} - {self.nombre}"
