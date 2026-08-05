from django.db import models


class Institucion(models.Model):
    """
    Institución de salud.
    """

    nombre = models.CharField(
        max_length=200,
        unique=True
    )

    nit = models.CharField(
        max_length=30,
        unique=True
    )

    direccion = models.CharField(
        max_length=250,
        blank=True
    )

    ciudad = models.CharField(
        max_length=100,
        blank=True
    )

    departamento = models.CharField(
        max_length=100,
        blank=True
    )

    telefono = models.CharField(
        max_length=30,
        blank=True
    )

    correo = models.EmailField(
        blank=True
    )

    representante = models.CharField(
        max_length=150,
        blank=True
    )

    activa = models.BooleanField(
        default=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre