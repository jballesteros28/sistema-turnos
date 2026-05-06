from django.db import models
from django.utils.text import slugify


class EstadoProfesional(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"
    SUSPENDIDO = "suspendido", "Suspendido"


class TipoProfesional(models.TextChoices):
    BARBERO = "barbero", "Barbero"
    ESTILISTA = "estilista", "Estilista"
    MEDICO = "medico", "Medico"
    ESTETICISTA = "esteticista", "Esteticista"
    PROFESIONAL = "profesional", "Profesional"
    OTRO = "otro", "Otro"


class Profesional(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="profesionales",
    )
    sucursales = models.ManyToManyField(
        "sucursal.Sucursal",
        blank=True,
        related_name="profesionales",
    )
    servicios = models.ManyToManyField(
        "servicio.Servicio",
        blank=True,
        related_name="profesionales",
    )

    nombre = models.CharField(max_length=120)
    apellido = models.CharField(max_length=120, blank=True)
    nombre_visible = models.CharField(max_length=160, blank=True)
    slug = models.SlugField(max_length=180, blank=True)

    tipo_profesional = models.CharField(
        max_length=30,
        choices=TipoProfesional.choices,
        default=TipoProfesional.OTRO,
    )
    especialidad = models.CharField(max_length=120, blank=True)
    matricula = models.CharField(max_length=80, blank=True)
    descripcion_profesional = models.TextField(blank=True)

    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    estado = models.CharField(
        max_length=15,
        choices=EstadoProfesional.choices,
        default=EstadoProfesional.ACTIVO,
    )
    acepta_turnos = models.BooleanField(default=True)
    duracion_buffer_minutos = models.PositiveSmallIntegerField(default=0)
    color_agenda = models.CharField(max_length=7, blank=True)
    foto = models.ImageField(upload_to="profesionales/fotos/", null=True, blank=True)
    visible_en_reserva_online = models.BooleanField(default=True)
    orden_visualizacion = models.PositiveSmallIntegerField(default=0)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profesional"
        verbose_name_plural = "Profesionales"
        ordering = ["negocio", "orden_visualizacion", "apellido", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "slug"],
                name="uniq_prof_slug_negocio",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.nombre_visible:
            self.nombre_visible = f"{self.nombre} {self.apellido}".strip()
        if not self.slug:
            self.slug = slugify(self.nombre_visible)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_visible
