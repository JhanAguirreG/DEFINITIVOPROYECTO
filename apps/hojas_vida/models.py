from django.db import models


class HojaVida(models.Model):
    """
    Hoja de vida técnica y documental de un equipo biomédico.

    Cada equipo tiene una única hoja de vida.
    """

    class FormaAdquisicion(models.TextChoices):
        COMPRA = "COMPRA", "Compra"
        DONACION = "DONACION", "Donación"
        COMODATO = "COMODATO", "Comodato"
        ARRIENDO = "ARRIENDO", "Arriendo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        OTRO = "OTRO", "Otro"

    class PeriodicidadMantenimiento(models.TextChoices):
        TRIMESTRAL = "TRIMESTRAL", "Trimestral"
        CUATRIMESTRAL = "CUATRIMESTRAL", "Cuatrimestral"
        SEMESTRAL = "SEMESTRAL", "Semestral"
        ANUAL = "ANUAL", "Anual"
        NO_APLICA = "NO_APLICA", "No aplica"

    class PeriodicidadCalibracion(models.TextChoices):
        BIMENSUAL = "BIMENSUAL", "Bimensual"
        CUATRIMESTRAL = "CUATRIMESTRAL", "Cuatrimestral"
        SEMESTRAL = "SEMESTRAL", "Semestral"
        ANUAL = "ANUAL", "Anual"
        NO_APLICA = "NO_APLICA", "No aplica"

    class RiesgoElectrico(models.TextChoices):
        NO_APLICA = "NO_APLICA", "No aplica"
        CLASE_I = "CLASE_I", "Clase I"
        CLASE_II = "CLASE_II", "Clase II"
        CLASE_III = "CLASE_III", "Clase III"

    equipo = models.OneToOneField(
        "equipos.Equipo",
        on_delete=models.CASCADE,
        related_name="hoja_vida",
    )

    # ==========================================================
    # DATOS DE ADQUISICIÓN
    # ==========================================================

    forma_adquisicion = models.CharField(
        max_length=30,
        choices=FormaAdquisicion.choices,
        blank=True,
    )

    numero_factura = models.CharField(
        max_length=100,
        blank=True,
    )

    fecha_compra = models.DateField(
        null=True,
        blank=True,
    )

    fecha_instalacion = models.DateField(
        null=True,
        blank=True,
    )

    fecha_fabricacion = models.CharField(
        max_length=50,
        blank=True,
    )

    garantia_hasta = models.DateField(
        null=True,
        blank=True,
    )

    garantia_anios = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    costo_adquisicion = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )

    vida_util = models.PositiveIntegerField(
        default=10,
        help_text="Vida útil en años",
    )

    # ==========================================================
    # INFORMACIÓN REGULATORIA
    # ==========================================================

    registro_importacion = models.CharField(
        max_length=150,
        blank=True,
    )

    # ==========================================================
    # PROVEEDOR
    # ==========================================================

    proveedor = models.CharField(
        max_length=200,
        blank=True,
    )

    proveedor_telefono = models.CharField(
        max_length=50,
        blank=True,
    )

    proveedor_ciudad_pais = models.CharField(
        max_length=150,
        blank=True,
    )

    # ==========================================================
    # FABRICANTE
    # ==========================================================

    fabricante_telefono = models.CharField(
        max_length=50,
        blank=True,
    )

    fabricante_ciudad_pais = models.CharField(
        max_length=150,
        blank=True,
    )

    # ==========================================================
    # CLASIFICACIÓN
    # ==========================================================

    riesgo_electrico = models.CharField(
        max_length=20,
        choices=RiesgoElectrico.choices,
        default=RiesgoElectrico.NO_APLICA,
    )

    # ==========================================================
    # ALIMENTACIÓN
    # ==========================================================

    alimentacion_electricidad = models.BooleanField(
        default=False,
    )

    alimentacion_emergencia = models.BooleanField(
        default=False,
    )

    alimentacion_vapor = models.BooleanField(
        default=False,
    )

    alimentacion_vacio = models.BooleanField(
        default=False,
    )

    alimentacion_regulada = models.BooleanField(
        default=False,
    )

    alimentacion_baterias = models.BooleanField(
        default=False,
    )

    alimentacion_oxigeno = models.BooleanField(
        default=False,
    )

    alimentacion_agua = models.BooleanField(
        default=False,
    )

    alimentacion_estandar = models.BooleanField(
        default=False,
    )

    alimentacion_servicio = models.BooleanField(
        default=False,
    )

    alimentacion_aire = models.BooleanField(
        default=False,
    )

    tecnologia_predominante = models.CharField(
        max_length=100,
        blank=True,
    )

    # ==========================================================
    # MANTENIMIENTO Y CALIBRACIÓN
    # ==========================================================

    periodicidad_mantenimiento = models.CharField(
        max_length=30,
        choices=PeriodicidadMantenimiento.choices,
        blank=True,
    )

    periodicidad_calibracion = models.CharField(
        max_length=30,
        choices=PeriodicidadCalibracion.choices,
        blank=True,
    )

    # ==========================================================
    # UBICACIÓN Y DOCUMENTACIÓN GENERAL
    # ==========================================================

    ubicacion_detallada = models.CharField(
        max_length=250,
        blank=True,
    )

    fotografia = models.ImageField(
        upload_to="equipos/",
        null=True,
        blank=True,
    )

    # ==========================================================
    # RECOMENDACIONES DEL FABRICANTE
    # ==========================================================

    recomendaciones_fabricante = models.TextField(
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
    )

    # ==========================================================
    # CONTROL DEL REGISTRO
    # ==========================================================

    creado = models.DateTimeField(
        auto_now_add=True,
    )

    actualizado = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Hoja de Vida"
        verbose_name_plural = "Hojas de Vida"
        ordering = ["equipo"]

    def __str__(self):
        return str(self.equipo)


# ==========================================================
# VALORES DE CARACTERÍSTICAS TÉCNICAS
# ==========================================================

class ValorCampoTecnico(models.Model):
    """
    Guarda el valor de una característica técnica para
    una hoja de vida específica.

    El nombre del campo viene del catálogo y el valor
    pertenece al equipo concreto.
    """

    hoja_vida = models.ForeignKey(
        HojaVida,
        on_delete=models.CASCADE,
        related_name="valores_tecnicos",
    )

    campo = models.ForeignKey(
        "catalogo.CampoTecnico",
        on_delete=models.PROTECT,
        related_name="valores",
    )

    valor = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "campo__orden",
            "campo__nombre",
        ]

        verbose_name = "Valor de Característica Técnica"
        verbose_name_plural = "Valores de Características Técnicas"

        constraints = [
            models.UniqueConstraint(
                fields=["hoja_vida", "campo"],
                name="unique_valor_campo_hoja_vida",
            )
        ]

    def __str__(self):
        return f"{self.campo.nombre}: {self.valor}"


# ==========================================================
# ACCESORIOS / COMPONENTES
# ==========================================================

class AccesorioHojaVida(models.Model):
    """
    Accesorio o componente asociado a una hoja de vida.
    """

    hoja_vida = models.ForeignKey(
        HojaVida,
        on_delete=models.CASCADE,
        related_name="accesorios",
    )

    cantidad = models.PositiveIntegerField(
        default=1,
    )

    nombre = models.CharField(
        max_length=200,
    )

    observaciones = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "nombre",
        ]

        verbose_name = "Accesorio de Hoja de Vida"
        verbose_name_plural = "Accesorios de Hoja de Vida"

    def __str__(self):
        return f"{self.cantidad} - {self.nombre}"


# ==========================================================
# DOCUMENTACIÓN DE LA HOJA DE VIDA
# ==========================================================

class DocumentacionHojaVida(models.Model):
    """
    Documentación técnica asociada al equipo.
    """

    class Tipo(models.TextChoices):
        MANUAL_SERVICIO = "MANUAL_SERVICIO", "Manual de servicios"
        MANUAL_OPERACION = "MANUAL_OPERACION", "Manual de operación"
        PLANOS = "PLANOS", "Planos"
        DIAGRAMA_PARTES = "DIAGRAMA_PARTES", "Diagrama de partes"
        OTROS = "OTROS", "Otros"

    hoja_vida = models.ForeignKey(
        HojaVida,
        on_delete=models.CASCADE,
        related_name="documentos",
    )

    tipo = models.CharField(
        max_length=30,
        choices=Tipo.choices,
    )

    nombre = models.CharField(
        max_length=200,
        blank=True,
    )

    archivo = models.FileField(
        upload_to="hojas_vida/documentos/",
    )

    observaciones = models.TextField(
        blank=True,
    )

    fecha_carga = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "tipo",
            "nombre",
        ]

        verbose_name = "Documento de Hoja de Vida"
        verbose_name_plural = "Documentos de Hojas de Vida"

    def __str__(self):
        if self.nombre:
            return self.nombre

        return self.get_tipo_display()