from django.db import models


class Mantenimiento(models.Model):

    class Tipo(models.TextChoices):
        PREVENTIVO = "PREVENTIVO", "Preventivo"
        CORRECTIVO = "CORRECTIVO", "Correctivo"

    class Estado(models.TextChoices):
        PROGRAMADO = "PROGRAMADO", "Programado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        FINALIZADO = "FINALIZADO", "Finalizado"

    hoja_vida = models.ForeignKey(
        "hojas_vida.HojaVida",
        on_delete=models.CASCADE,
        related_name="mantenimientos",
    )

    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADO,
    )

    fecha_programada = models.DateField()

    fecha_inicio = models.DateField(
        null=True,
        blank=True,
    )

    fecha_fin = models.DateField(
        null=True,
        blank=True,
    )

    ingeniero = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    empresa = models.CharField(
        max_length=200,
        blank=True,
    )

    descripcion = models.TextField()

    actividades_realizadas = models.TextField(
        blank=True,
    )

    repuestos = models.TextField(
        blank=True,
    )

    costo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    observaciones = models.TextField(
        blank=True,
    )

    archivo = models.FileField(
        upload_to="mantenimientos/",
        blank=True,
        null=True,
    )

    creado = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "-fecha_programada",
        ]

        verbose_name = "Mantenimiento"

        verbose_name_plural = "Mantenimientos"

    def __str__(self):

        return (
            f"{self.get_tipo_display()} - "
            f"{self.hoja_vida.equipo.nombre}"
        )