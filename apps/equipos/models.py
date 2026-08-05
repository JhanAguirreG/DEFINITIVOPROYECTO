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

    catalogo = models.ForeignKey(
        "catalogo.CatalogoEquipo",
        on_delete=models.PROTECT,
        related_name="equipos",
        null=True,
        blank=True,
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

    ubicacion = models.CharField(
        max_length=150,
        blank=True,
    )

    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.ACTIVO,
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
    @property
    def riesgo_catalogo(self):
        return self.catalogo.riesgo if self.catalogo else None


    @property
    def tecnologia_catalogo(self):
        return self.catalogo.tecnologia if self.catalogo else None

    @property
    def frecuencia_catalogo(self):
        return (
            self.catalogo.frecuencia_mantenimiento
            if self.catalogo
            else None
        )

    @property
    def requiere_calibracion(self):
        if self.catalogo:
            return self.catalogo.requiere_calibracion
        return False


    @property
    def requiere_mantenimiento(self):
        if self.catalogo:
            return self.catalogo.requiere_mantenimiento
        return True

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"