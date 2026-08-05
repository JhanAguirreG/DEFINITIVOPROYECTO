from django.conf import settings
from django.db import models


class Inspeccion(models.Model):
    """
    Cabecera de una inspección diaria realizada a un servicio.
    """

    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        FINALIZADA = "FINALIZADA", "Finalizada"

    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.CASCADE,
        related_name="inspecciones",
        null=True,
        blank=True,
    )

    servicio = models.ForeignKey(
        "servicios.Servicio",
        on_delete=models.CASCADE,
        related_name="inspecciones",
        null=True,
        blank=True,
    )

    biomedico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspecciones_realizadas",
        null=True,
        blank=True,
    )

    fecha = models.DateField(
        auto_now_add=True,
    )

    hora_inicio = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )

    hora_fin = models.DateTimeField(
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTA,
    )

    observaciones_generales = models.TextField(
        blank=True,
    )

    creado = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    actualizado = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )
    class Meta:
        ordering = ["-fecha", "-hora_inicio"]
        verbose_name = "Inspección"
        verbose_name_plural = "Inspecciones"

    def __str__(self):
        return (
            f"{self.institucion} - "
            f"{self.servicio} - "
            f"{self.fecha}"
        )


class DetalleInspeccion(models.Model):
    """
    Resultado de la inspección para un equipo específico.
    """

    class EstadoEquipo(models.TextChoices):
        OPERATIVO = "OPERATIVO", "Operativo"
        OBSERVACION = "OBSERVACION", "Con observaciones"
        FUERA_SERVICIO = "FUERA_SERVICIO", "Fuera de servicio"

    inspeccion = models.ForeignKey(
        Inspeccion,
        on_delete=models.CASCADE,
        related_name="detalles",
    )

    equipo = models.ForeignKey(
        "equipos.Equipo",
        on_delete=models.CASCADE,
        related_name="inspecciones",
    )

    estado = models.CharField(
        max_length=30,
        choices=EstadoEquipo.choices,
        default=EstadoEquipo.OPERATIVO,
    )

    limpio = models.BooleanField(default=True)
    energiza = models.BooleanField(default=True)
    accesorios_completos = models.BooleanField(default=True)
    alarmas_funcionan = models.BooleanField(default=True)
    funcionamiento_correcto = models.BooleanField(default=True)

    observaciones = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["equipo__nombre"]
        verbose_name = "Detalle de inspección"
        verbose_name_plural = "Detalles de inspección"

    def __str__(self):
        return (
            f"{self.inspeccion} - "
            f"{self.equipo.nombre}"
        )


class FirmaInspeccion(models.Model):
    """
    Firmas digitales de la inspección.
    """

    inspeccion = models.OneToOneField(
        Inspeccion,
        on_delete=models.CASCADE,
        related_name="firma",
    )

    responsable_servicio = models.CharField(
        max_length=150,
    )

    firma_biomedico = models.ImageField(
        upload_to="firmas/biomedicos/",
        null=True,
        blank=True,
    )

    firma_responsable = models.ImageField(
        upload_to="firmas/responsables/",
        null=True,
        blank=True,
    )

    fecha_firma = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Firma de inspección"
        verbose_name_plural = "Firmas de inspección"

    def __str__(self):
        return f"Firmas - {self.inspeccion}"