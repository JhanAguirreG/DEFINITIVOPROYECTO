from django import forms

from .models import Mantenimiento, OrdenTrabajo


from django import forms

from .models import Mantenimiento
from apps.equipos.models import Equipo
from apps.hojas_vida.models import HojaVida
from apps.servicios.models import Servicio

class MantenimientoForm(forms.ModelForm):

    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.all().order_by("nombre"),
        required=False,
        empty_label="Seleccione un servicio",
        label="Servicio",
    )

    class Meta:
        model = Mantenimiento

        fields = (
            "servicio",
            "hoja_vida",
            "tipo",
            "estado",
            "fecha_programada",
            "fecha_inicio",
            "fecha_fin",
            "ingeniero",
            "empresa",
            "descripcion",
            "actividades_realizadas",
            "repuestos",
            "costo",
            "observaciones",
            "archivo",
        )

        widgets = {
            "fecha_programada": forms.DateInput(
                attrs={"type": "date"}
            ),
            "fecha_inicio": forms.DateInput(
                attrs={"type": "date"}
            ),
            "fecha_fin": forms.DateInput(
                attrs={"type": "date"}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describa el trabajo realizado..."
                }
            ),
            "actividades_realizadas": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Actividades realizadas..."
                }
            ),
            "repuestos": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Indique los repuestos utilizados..."
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Observaciones..."
                }
            ),
        }

    def __init__(self, *args, orden_trabajo=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.orden_trabajo = orden_trabajo

        # ==========================================================
        # ESTILOS
        # ==========================================================

        for nombre, campo in self.fields.items():

            if isinstance(campo.widget, forms.ClearableFileInput):

                campo.widget.attrs.update({
                    "class": "form-control"
                })

            elif isinstance(campo.widget, forms.CheckboxInput):

                campo.widget.attrs.update({
                    "class": "form-check-input"
                })

            else:

                campo.widget.attrs.update({
                    "class": "form-control"
                })

        # ==========================================================
        # QUERYSET INICIAL DE EQUIPOS
        # ==========================================================

        self.fields["hoja_vida"].queryset = (
            HojaVida.objects.none()
        )

        self.fields["hoja_vida"].empty_label = (
            "Seleccione primero un servicio"
        )

        # ==========================================================
        # SERVICIO DE UNA ORDEN DE TRABAJO
        # ==========================================================

        if orden_trabajo:

            servicio = orden_trabajo.servicio

            self.fields["servicio"].queryset = (
                Servicio.objects.filter(
                    pk=servicio.pk
                )
            )

            self.fields["servicio"].initial = servicio

            self.fields["servicio"].disabled = True
            self.fields["servicio"].required = False

            self.fields["servicio"].help_text = (
                "Servicio definido por la Orden de Trabajo."
            )

            self.fields["hoja_vida"].queryset = (
                HojaVida.objects
                .filter(
                    equipo__servicio=servicio,
                    equipo__institucion=servicio.institucion,
                )
                .select_related(
                    "equipo",
                    "equipo__servicio",
                    "equipo__institucion",
                    "equipo__catalogo",
                )
                .order_by(
                    "equipo__nombre",
                    "equipo__serie",
                )
            )

            self.fields["hoja_vida"].empty_label = (
                "Seleccione un equipo"
            )

        # ==========================================================
        # MANTENIMIENTO INDEPENDIENTE
        # ==========================================================

        else:

            servicio_id = self.data.get("servicio")

            # Si no hay POST, revisar si estamos editando
            if not servicio_id and self.instance.pk:

                servicio_id = (
                    self.instance.hoja_vida
                    .equipo
                    .servicio_id
                )

            if servicio_id:

                try:

                    servicio = Servicio.objects.get(
                        pk=servicio_id
                    )

                    self.fields["hoja_vida"].queryset = (
                        HojaVida.objects
                        .filter(
                            equipo__servicio=servicio,
                            equipo__institucion=servicio.institucion,
                        )
                        .select_related(
                            "equipo",
                            "equipo__servicio",
                            "equipo__institucion",
                            "equipo__catalogo",
                        )
                        .order_by(
                            "equipo__nombre",
                            "equipo__serie",
                        )
                    )

                    self.fields["hoja_vida"].empty_label = (
                        "Seleccione un equipo"
                    )

                except Servicio.DoesNotExist:

                    pass

        # ==========================================================
        # CAMPOS OPCIONALES
        # ==========================================================

        self.fields["ingeniero"].required = False
        self.fields["empresa"].required = False
        self.fields["fecha_inicio"].required = False
        self.fields["fecha_fin"].required = False
        self.fields["archivo"].required = False
        self.fields["repuestos"].required = False
        self.fields["observaciones"].required = False

    # ==============================================================
    # VALIDACIÓN
    # ==============================================================

    def clean(self):

        cleaned_data = super().clean()

        servicio = cleaned_data.get("servicio")
        hoja_vida = cleaned_data.get("hoja_vida")

        if not hoja_vida:
            return cleaned_data

        equipo = hoja_vida.equipo

        # ==========================================================
        # DESDE ORDEN DE TRABAJO
        # ==========================================================

        if self.orden_trabajo:

            servicio_ot = self.orden_trabajo.servicio

            if equipo.servicio_id != servicio_ot.id:

                self.add_error(
                    "hoja_vida",
                    "El equipo seleccionado no pertenece "
                    "al servicio de la Orden de Trabajo."
                )

            if equipo.institucion_id != servicio_ot.institucion_id:

                self.add_error(
                    "hoja_vida",
                    "El equipo seleccionado no pertenece "
                    "a la institución de la Orden de Trabajo."
                )

            return cleaned_data

        # ==========================================================
        # MANTENIMIENTO INDEPENDIENTE
        # ==========================================================

        if not servicio:

            self.add_error(
                "servicio",
                "Debe seleccionar un servicio."
            )

            return cleaned_data

        if equipo.servicio_id != servicio.id:

            self.add_error(
                "hoja_vida",
                "El equipo seleccionado no pertenece "
                "al servicio seleccionado."
            )

        return cleaned_data
    
class OrdenTrabajoForm(forms.ModelForm):
    """
    Formulario para crear una Orden de Trabajo general.

    Una orden puede contener varios mantenimientos/equipos.
    Las firmas se realizan una sola vez sobre la orden.
    """

    class Meta:

        model = OrdenTrabajo

        fields = (
            "numero",
            "fecha",
            "servicio",
            "ingeniero",
            "empresa",
            "descripcion",
            "responsable_nombre",
            "responsable_cargo",
            "firma_biomedico",
            "firma_responsable",
        )

        widgets = {

            "fecha": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Descripción general de los trabajos "
                        "realizados en el servicio..."
                    ),
                }
            ),

            "responsable_nombre": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Nombre del responsable del servicio"
                    ),
                }
            ),

            "responsable_cargo": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Cargo del responsable"
                    ),
                }
            ),

            "firma_biomedico": forms.HiddenInput(),

            "firma_responsable": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # --------------------------------------------------
        # CLASES BOOTSTRAP
        # --------------------------------------------------

        for nombre, campo in self.fields.items():

            if isinstance(
                campo.widget,
                forms.HiddenInput
            ):

                continue

            campo.widget.attrs.update({
                "class": "form-control",
            })

        # --------------------------------------------------
        # CAMPOS OPCIONALES
        # --------------------------------------------------

        self.fields["ingeniero"].required = False

        self.fields["empresa"].required = False

        self.fields["descripcion"].required = False

        self.fields["responsable_nombre"].required = False

        self.fields["responsable_cargo"].required = False

        self.fields["firma_biomedico"].required = False

        self.fields["firma_responsable"].required = False