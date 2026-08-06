from django.conf import settings
from django.db import models


# ==========================================================
# INSPECCION
# ==========================================================

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
    )


    servicio = models.ForeignKey(
        "servicios.Servicio",
        on_delete=models.CASCADE,
        related_name="inspecciones",
    )


    biomedico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspecciones_realizadas",
    )


    fecha = models.DateField(
        auto_now_add=True,
    )


    hora_inicio = models.DateTimeField(
        auto_now_add=True,
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
    )


    actualizado = models.DateTimeField(
        auto_now=True,
    )


    class Meta:

        ordering = [
            "-fecha",
            "-hora_inicio",
        ]

        verbose_name = "Inspección"

        verbose_name_plural = "Inspecciones"


    def __str__(self):

        return (
            f"{self.institucion} - "
            f"{self.servicio} - "
            f"{self.fecha}"
        )



# ==========================================================
# DETALLE INSPECCION
# ==========================================================

class DetalleInspeccion(models.Model):
    """
    Evaluación individual de cada equipo durante la ronda.
    """


    class EstadoEquipo(models.TextChoices):

        OPERATIVO = (
            "OPERATIVO",
            "Operativo"
        )

        OBSERVACION = (
            "OBSERVACION",
            "Con observaciones"
        )

        FUERA_SERVICIO = (
            "FUERA_SERVICIO",
            "Fuera de servicio"
        )


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


    limpio = models.BooleanField(
        default=True,
    )


    energiza = models.BooleanField(
        default=True,
    )


    accesorios_completos = models.BooleanField(
        default=True,
    )


    alarmas_funcionan = models.BooleanField(
        default=True,
    )


    funcionamiento_correcto = models.BooleanField(
        default=True,
    )


    observaciones = models.TextField(
        blank=True,
    )


    class Meta:

        ordering = [
            "equipo__nombre",
        ]

        verbose_name = "Detalle de inspección"

        verbose_name_plural = "Detalles de inspección"



    def __str__(self):

        return (
            f"{self.equipo.nombre}"
        )



# ==========================================================
# FIRMA
# ==========================================================

class FirmaInspeccion(models.Model):

    inspeccion = models.OneToOneField(
        Inspeccion,
        on_delete=models.CASCADE,
        related_name="firma",
    )

    responsable_servicio = models.CharField(
        max_length=150,
    )

    # NUEVO CAMPO
    observaciones_finales = models.TextField(
        blank=True,
    )

    firma_biomedico = models.ImageField(
        upload_to="firmas/biomedicos/",
        blank=True,
        null=True,
    )

    firma_responsable = models.ImageField(
        upload_to="firmas/responsables/",
        blank=True,
        null=True,
    )

    fecha_firma = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Firma de inspección"
        verbose_name_plural = "Firmas de inspección"

    def __str__(self):
        return f"Firma - Inspección {self.inspeccion.id}"


# ==========================================================
# RESULTADO ITEMS CHECKLIST
# ==========================================================

class ResultadoItem(models.Model):
    """
    Resultado de cada punto del checklist
    asociado a un equipo.
    """


    detalle = models.ForeignKey(

        DetalleInspeccion,

        on_delete=models.CASCADE,

        related_name="resultados",

    )


    item = models.ForeignKey(

        "catalogo.ItemPlantilla",

        on_delete=models.CASCADE,

        related_name="resultados",

    )


    cumple = models.BooleanField(

        default=True,

    )


    observacion = models.TextField(

        blank=True,

    )


    class Meta:

        ordering = [
            "item__orden",
        ]


        verbose_name = "Resultado de ítem"


        verbose_name_plural = "Resultados de ítems"


        unique_together = (

            "detalle",

            "item",

        )


    def __str__(self):

        return (

            f"{self.detalle.equipo.nombre} - "
            f"{self.item}"

        )