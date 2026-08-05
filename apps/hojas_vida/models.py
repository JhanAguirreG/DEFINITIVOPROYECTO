from django.db import models


class HojaVida(models.Model):
    """
    Hoja de vida técnica del equipo biomédico.
    """

    equipo = models.OneToOneField(
        "equipos.Equipo",
        on_delete=models.CASCADE,
        related_name="hoja_vida",
    )

    fecha_compra = models.DateField(
        null=True,
        blank=True,
    )

    fecha_instalacion = models.DateField(
        null=True,
        blank=True,
    )

    proveedor = models.CharField(
        max_length=200,
        blank=True,
    )

    vida_util = models.PositiveIntegerField(
        default=10,
        help_text="Vida útil en años",
    )

    garantia_hasta = models.DateField(
        null=True,
        blank=True,
    )

    costo_adquisicion = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )

    ubicacion_detallada = models.CharField(
        max_length=250,
        blank=True,
    )

    manual_operacion = models.FileField(
        upload_to="manuales/",
        null=True,
        blank=True,
    )

    manual_servicio = models.FileField(
        upload_to="manuales_servicio/",
        null=True,
        blank=True,
    )

    fotografia = models.ImageField(
        upload_to="equipos/",
        null=True,
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
    )

    creado = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Hoja de Vida"
        verbose_name_plural = "Hojas de Vida"
        ordering = [
            "equipo",
        ]

    def __str__(self):
        return str(self.equipo)