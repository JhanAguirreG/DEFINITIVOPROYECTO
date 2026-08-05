from django.db import models


class Servicio(models.Model):
    """
    Servicios pertenecientes a una institución.
    """

    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.CASCADE,
        related_name="servicios",
        verbose_name="Institución",
    )

    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre",
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
    )

    ubicacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ubicación",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = [
            "institucion",
            "nombre",
        ]
        unique_together = (
            "institucion",
            "nombre",
        )

    def __str__(self):
        return f"{self.nombre} - {self.institucion.nombre}"