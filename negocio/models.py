from django.db import models
from django.utils.text import slugify


class TipoNegocio(models.TextChoices):
    BARBERIA = "barberia", "Barberia"
    SALON_BELLEZA = "salon_belleza", "Salon de belleza"
    CONSULTORIO = "consultorio", "Consultorio"
    CENTRO_ESTETICO = "centro_estetico", "Centro estetico"
    ESTUDIO_PROFESIONAL = "estudio_profesional", "Estudio profesional"
    OTRO = "otro", "Otro"


class EstadoNegocio(models.TextChoices):
    ACTIVO = "activo", "Activo"
    INACTIVO = "inactivo", "Inactivo"
    SUSPENDIDO = "suspendido", "Suspendido"


class Moneda(models.TextChoices):
    ARS = "ARS", "Peso argentino"
    USD = "USD", "Dolar estadounidense"
    EUR = "EUR", "Euro"


class Idioma(models.TextChoices):
    ES = "es", "Espanol"
    EN = "en", "English"
    PT = "pt", "Portugues"


class Negocio(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    tipo_negocio = models.CharField(
        max_length=30,
        choices=TipoNegocio.choices,
        default=TipoNegocio.OTRO,
    )
    descripcion = models.TextField(blank=True)

    estado = models.CharField(
        max_length=15,
        choices=EstadoNegocio.choices,
        default=EstadoNegocio.ACTIVO,
    )
    fecha_alta = models.DateTimeField(auto_now_add=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)
    motivo_baja = models.CharField(max_length=250, blank=True)

    email_principal = models.EmailField()
    telefono_principal = models.CharField(max_length=20)
    whatsapp_principal = models.CharField(max_length=20, blank=True)
    sitio_web = models.URLField(blank=True)
    instagram = models.CharField(max_length=120, blank=True)

    direccion_principal = models.CharField(max_length=200, blank=True)
    ciudad = models.CharField(max_length=120)
    provincia_estado = models.CharField(max_length=120, blank=True)
    pais = models.CharField(max_length=120)
    codigo_postal = models.CharField(max_length=20, blank=True)

    zona_horaria = models.CharField(
        max_length=100,
        default="America/Argentina/Buenos_Aires",
    )
    moneda = models.CharField(
        max_length=3,
        choices=Moneda.choices,
        default=Moneda.ARS,
    )
    idioma = models.CharField(
        max_length=2,
        choices=Idioma.choices,
        default=Idioma.ES,
    )

    nombre_visible = models.CharField(max_length=120, blank=True)
    logo = models.ImageField(upload_to="negocios/logos/", null=True, blank=True)
    color_primario = models.CharField(max_length=7, blank=True)
    color_secundario = models.CharField(max_length=7, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            # TODO: antes de produccion, generar slugs unicos de forma robusta.
            self.slug = slugify(self.nombre)
        if not self.nombre_visible:
            self.nombre_visible = self.nombre
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
