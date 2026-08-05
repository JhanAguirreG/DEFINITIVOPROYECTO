from django.db import models


class CatalogoEquipo(models.Model):
    """
    Catálogo maestro de tipos de equipos biomédicos.
    """

    class Riesgo(models.TextChoices):
        I = "I", "Clase I"
        IIA = "IIA", "Clase IIA"
        IIB = "IIB", "Clase IIB"
        III = "III", "Clase III"

    class Tecnologia(models.TextChoices):
        BIOMEDICO = "BIOMEDICO", "Equipo Biomédico"
        LABORATORIO = "LABORATORIO", "Laboratorio"
        IMAGENOLOGIA = "IMAGENOLOGIA", "Imagenología"
        INDUSTRIAL = "INDUSTRIAL", "Industrial"

    nombre = models.CharField(
        max_length=200,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True,
    )

    riesgo = models.CharField(
        max_length=5,
        choices=Riesgo.choices,
        default=Riesgo.I,
    )

    tecnologia = models.CharField(
        max_length=20,
        choices=Tecnologia.choices,
        default=Tecnologia.BIOMEDICO,
    )

    requiere_calibracion = models.BooleanField(
        default=False,
    )

    requiere_mantenimiento = models.BooleanField(
        default=True,
    )

    frecuencia_mantenimiento = models.PositiveIntegerField(
        default=6,
        help_text="Frecuencia en meses",
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Catálogo de Equipo"
        verbose_name_plural = "Catálogo de Equipos"

    def __str__(self):
        return self.nombre

        # ==========================================================
# PLANTILLAS DE INSPECCIÓN
# ==========================================================

class PlantillaInspeccion(models.Model):

    catalogo = models.OneToOneField(
        CatalogoEquipo,
        on_delete=models.CASCADE,
        related_name="plantilla",
    )

    nombre = models.CharField(
        max_length=200,
    )

    activa = models.BooleanField(
        default=True,
    )

    class Meta:

        ordering = [
            "nombre",
        ]

        verbose_name = "Plantilla de Inspección"

        verbose_name_plural = "Plantillas de Inspección"

    def __str__(self):

        return self.nombre


# ==========================================================
# ITEMS
# ==========================================================

class ItemPlantilla(models.Model):

    plantilla = models.ForeignKey(
        PlantillaInspeccion,
        on_delete=models.CASCADE,
        related_name="items",
    )

    descripcion = models.CharField(
        max_length=250,
    )

    obligatorio = models.BooleanField(
        default=True,
    )

    orden = models.PositiveIntegerField(
        default=1,
    )

    class Meta:

        ordering = [
            "orden",
        ]

        verbose_name = "Ítem"

        verbose_name_plural = "Ítems"

    def __str__(self):

        return self.descripcion