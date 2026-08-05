from django.db import models


class Equipo(models.Model):
    """
    Equipo biomédico del sistema SIGHI.
    """

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        MANTENIMIENTO = "MANTENIMIENTO", "En mantenimiento"
        FUERA_SERVICIO = "FUERA_SERVICIO", "Fuera de servicio"
        BAJA = "BAJA", "Dado de baja"

    class Riesgo(models.TextChoices):
        I = "I", "Clase I"
        IIA = "IIA", "Clase IIA"
        IIB = "IIB", "Clase IIB"
        III = "III", "Clase III"

    class Tecnologia(models.TextChoices):
        BIOMEDICO = "BIOMEDICO", "Equipo Biomédico"
        INDUSTRIAL = "INDUSTRIAL", "Industrial"
        LABORATORIO = "LABORATORIO", "Laboratorio"
        IMAGENOLOGIA = "IMAGENOLOGIA", "Imagenología"

    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.CASCADE,
        related_name="equipos",
    )

    servicio = models.ForeignKey(
        "servicios.Servicio",
        on_delete=models.CASCADE,
        related_name="equipos",
    )

    codigo = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )

    inventario = models.CharField(
        max_length=50,
        blank=True,
    )

    nombre = models.CharField(
        max_length=200,
    )

    marca = models.CharField(
        max_length=100,
        blank=True,
    )

    modelo = models.CharField(
        max_length=100,
        blank=True,
    )

    serie = models.CharField(
        max_length=100,
        blank=True,
    )

    fabricante = models.CharField(
        max_length=150,
        blank=True,
    )

    registro_invima = models.CharField(
        max_length=100,
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

    ubicacion = models.CharField(
        max_length=150,
        blank=True,
    )

    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )

    frecuencia_mantenimiento = models.PositiveIntegerField(
        default=6,
        help_text="Frecuencia en meses",
    )

    fecha_ultimo_mantenimiento = models.DateField(
        null=True,
        blank=True,
    )

    fecha_proximo_mantenimiento = models.DateField(
        null=True,
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
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
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = [
            "institucion",
            "servicio",
            "nombre",
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"