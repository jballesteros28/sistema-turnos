from django.db import models
from django.utils.text import slugify


class EstadoCliente(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"
    BLOQUEADO = "bloqueado", "Bloqueado"


class TipoDocumento(models.TextChoices):
    DNI = "dni", "DNI"
    PASAPORTE = "pasaporte", "Pasaporte"
    CUIT = "cuit", "CUIT"
    OTRO = "otro", "Otro"


class Cliente(models.Model):
    negocio = models.ForeignKey(
        "negocio.Negocio",
        on_delete=models.CASCADE,
        related_name="clientes",
    )
    nombre = models.CharField(max_length=120)
    apellido = models.CharField(max_length=120, blank=True)
    nombre_visible = models.CharField(max_length=160, blank=True)
    slug = models.SlugField(max_length=180, blank=True)

    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)

    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        blank=True,
    )
    numero_documento = models.CharField(max_length=40, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True)

    estado = models.CharField(
        max_length=15,
        choices=EstadoCliente.choices,
        default=EstadoCliente.ACTIVO,
    )
    acepta_recordatorios = models.BooleanField(default=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["negocio", "apellido", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "slug"],
                name="uniq_cliente_slug_negocio",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.nombre_visible:
            self.nombre_visible = f"{self.nombre} {self.apellido}".strip()
        if not self.slug:
            # TODO: antes de produccion, generar slugs unicos por negocio.
            self.slug = slugify(self.nombre_visible)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_visible
