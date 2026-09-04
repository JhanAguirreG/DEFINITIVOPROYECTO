from django.db import models


class OrdenTrabajo(models.Model):
    """
    Orden general de trabajo.

    Una orden puede contener varios mantenimientos/equipos.
    La firma del responsable se realiza una sola vez
    y queda asociada a toda la orden.
    """

    numero = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Número de orden",
    )

    fecha = models.DateField(
        verbose_name="Fecha",
    )

    servicio = models.ForeignKey(
        "servicios.Servicio",
        on_delete=models.CASCADE,
        related_name="ordenes_trabajo",
        verbose_name="Servicio",
    )

    ingeniero = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordenes_trabajo",
        verbose_name="Ingeniero / Biomédico",
    )

    empresa = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Empresa",
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción general",
    )

    responsable_nombre = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre del responsable",
    )

    responsable_cargo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Cargo del responsable",
    )

    firma_biomedico = models.TextField(
        blank=True,
        verbose_name="Firma del biomédico",
    )

    firma_responsable = models.TextField(
        blank=True,
        verbose_name="Firma del responsable",
    )

    creado = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Orden de Trabajo"
        verbose_name_plural = "Órdenes de Trabajo"
        ordering = [
            "-fecha",
            "-id",
        ]

    def __str__(self):
        return self.numero


class Mantenimiento(models.Model):

    class Tipo(models.TextChoices):
        PREVENTIVO = "PREVENTIVO", "Preventivo"
        CORRECTIVO = "CORRECTIVO", "Correctivo"

    class Estado(models.TextChoices):
        PROGRAMADO = "PROGRAMADO", "Programado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        FINALIZADO = "FINALIZADO", "Finalizado"

    # ==========================================================
    # ORDEN DE TRABAJO
    # ==========================================================

    orden_trabajo = models.ForeignKey(
        "mantenimiento.OrdenTrabajo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mantenimientos",
        verbose_name="Orden de Trabajo",
    )

    # ==========================================================
    # EQUIPO
    # ==========================================================

    hoja_vida = models.ForeignKey(
        "hojas_vida.HojaVida",
        on_delete=models.CASCADE,
        related_name="mantenimientos",
        verbose_name="Hoja de vida",
    )

    # ==========================================================
    # INFORMACIÓN DEL MANTENIMIENTO
    # ==========================================================

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
        related_name="mantenimientos",
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
    firma_biomedico = models.TextField(
        blank=True,
        verbose_name="Firma del biomédico",
    )   

    firma_responsable = models.TextField(
        blank=True,
        verbose_name="Firma del responsable",
    )

    mantenimiento_anterior = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mantenimiento_siguiente",
        verbose_name="Mantenimiento anterior",
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

class MantenimientoActividad(models.Model):
    mantenimiento = models.ForeignKey(
        "mantenimiento.Mantenimiento",
        on_delete=models.CASCADE,
        related_name="actividades",
        verbose_name="Mantenimiento",
    )

    actividad = models.ForeignKey(
        "catalogo.ActividadMantenimiento",
        on_delete=models.PROTECT,
        related_name="ejecuciones",
        verbose_name="Actividad",
    )

    realizada = models.BooleanField(
        default=False,
        verbose_name="Realizada",
    )

    observacion = models.TextField(
        blank=True,
        verbose_name="Observación",
    )

    class Meta:
        verbose_name = "Actividad de Mantenimiento"
        verbose_name_plural = "Actividades de Mantenimiento"
        ordering = ["actividad__orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["mantenimiento", "actividad"],
                name="unique_mantenimiento_actividad",
            )
        ]

    def __str__(self):
        return f"{self.mantenimiento} - {self.actividad}"