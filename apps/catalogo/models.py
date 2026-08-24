from django.db import models


class CatalogoEquipo(models.Model):
    """
    Catálogo maestro de tipos de equipos biomédicos.

    Define las características generales del tipo de equipo,
    los requisitos de inspección, las características técnicas
    y la guía de mantenimiento preventivo.
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
        verbose_name_plural = "Catálogos de Equipos"

    def __str__(self):
        return self.nombre


# ==========================================================
# PLANTILLAS DE INSPECCIÓN
# ==========================================================

class PlantillaInspeccion(models.Model):
    """
    Define los ítems que deben verificarse durante
    una inspección periódica del tipo de equipo.
    """

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
        ordering = ["nombre"]
        verbose_name = "Plantilla de Inspección"
        verbose_name_plural = "Plantillas de Inspección"

    def __str__(self):
        return self.nombre


class ItemPlantilla(models.Model):
    """
    Ítem individual de una plantilla de inspección.
    """

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
        ordering = ["orden"]
        verbose_name = "Ítem de Inspección"
        verbose_name_plural = "Ítems de Inspección"

    def __str__(self):
        return self.descripcion


# ==========================================================
# PLANTILLA DE CARACTERÍSTICAS TÉCNICAS
# ==========================================================

class CampoTecnico(models.Model):
    """
    Define una característica técnica que debe registrarse
    para un determinado tipo de equipo.

    Ejemplo para máquina de anestesia:
        - Voltaje
        - Corriente
        - Peso
        - Frecuencia
        - Pantalla
        - Batería
        - Parámetros
    """

    class TipoDato(models.TextChoices):
        TEXTO = "TEXTO", "Texto"
        NUMERO = "NUMERO", "Número"
        DECIMAL = "DECIMAL", "Número decimal"
        FECHA = "FECHA", "Fecha"
        SI_NO = "SI_NO", "Sí / No"

    catalogo = models.ForeignKey(
        CatalogoEquipo,
        on_delete=models.CASCADE,
        related_name="campos_tecnicos",
    )

    nombre = models.CharField(
        max_length=150,
    )

    tipo_dato = models.CharField(
        max_length=20,
        choices=TipoDato.choices,
        default=TipoDato.TEXTO,
    )

    unidad = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ejemplo: V, A, kg, Hz, °C",
    )

    obligatorio = models.BooleanField(
        default=False,
    )

    orden = models.PositiveIntegerField(
        default=1,
    )

    activo = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Campo Técnico"
        verbose_name_plural = "Campos Técnicos"

        constraints = [
            models.UniqueConstraint(
                fields=["catalogo", "nombre"],
                name="unique_campo_tecnico_catalogo",
            )
        ]

    def __str__(self):
        return f"{self.catalogo.nombre} - {self.nombre}"


# ==========================================================
# GUÍA DE MANTENIMIENTO PREVENTIVO
# ==========================================================

class GuiaMantenimiento(models.Model):
    """
    Guía de mantenimiento preventivo correspondiente
    a un tipo de equipo.
    """

    catalogo = models.OneToOneField(
        CatalogoEquipo,
        on_delete=models.CASCADE,
        related_name="guia_mantenimiento",
    )

    nombre = models.CharField(
        max_length=200,
    )

    activa = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Guía de Mantenimiento"
        verbose_name_plural = "Guías de Mantenimiento"

    def __str__(self):
        return self.nombre


class ActividadMantenimiento(models.Model):
    """
    Actividad individual de la guía de mantenimiento preventivo.
    """

    guia = models.ForeignKey(
        GuiaMantenimiento,
        on_delete=models.CASCADE,
        related_name="actividades",
    )

    descripcion = models.CharField(
        max_length=300,
    )

    obligatorio = models.BooleanField(
        default=True,
    )

    orden = models.PositiveIntegerField(
        default=1,
    )

    class Meta:
        ordering = ["orden"]
        verbose_name = "Actividad de Mantenimiento"
        verbose_name_plural = "Actividades de Mantenimiento"

    def __str__(self):
        return self.descripcion