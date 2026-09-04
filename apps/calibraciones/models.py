from django.db import models
from django.core.validators import FileExtensionValidator


class Calibracion(models.Model):
    """
    Registro de calibración de un equipo biomédico.

    Cada registro corresponde a un certificado de calibración
    realizado por una empresa externa.
    """

    equipo = models.ForeignKey(
        "equipos.Equipo",
        on_delete=models.CASCADE,
        related_name="calibraciones",
        verbose_name="Equipo",
    )

    fecha_calibracion = models.DateField(
        verbose_name="Fecha de calibración"
    )

    codigo = models.CharField(
        max_length=100,
        verbose_name="Código de calibración"
    )

    empresa = models.CharField(
        max_length=200,
        verbose_name="Empresa que realizó la calibración"
    )

    certificado = models.FileField(
        upload_to="calibraciones/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ],
        verbose_name="Certificado de calibración",
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Calibración"
        verbose_name_plural = "Calibraciones"
        ordering = ["-fecha_calibracion", "-creado"]

    def __str__(self):
        return f"{self.equipo} - {self.codigo}"