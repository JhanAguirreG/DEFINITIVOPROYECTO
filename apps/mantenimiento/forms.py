from django import forms

from .models import Mantenimiento, OrdenTrabajo


from django import forms

from .models import Mantenimiento
from apps.equipos.models import Equipo
from apps.hojas_vida.models import HojaVida


class MantenimientoForm(forms.ModelForm):
    """
    Formulario para registrar mantenimientos.

    Cuando se utiliza dentro de una Orden de Trabajo,
    únicamente muestra equipos pertenecientes al servicio
    de dicha orden.
    """

    class Meta:

        model = Mantenimiento

        fields = (
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
                attrs={
                    "type": "date",
                }
            ),

            "fecha_inicio": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "fecha_fin": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),

            "actividades_realizadas": forms.Textarea(
                attrs={
                    "rows": 5,
                }
            ),

            "repuestos": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),

            "observaciones": forms.Textarea(
                attrs={
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, orden_trabajo=None, **kwargs):

        super().__init__(*args, **kwargs)

        # ======================================================
        # ESTILOS
        # ======================================================

        for campo in self.fields.values():

            if isinstance(
                campo.widget,
                forms.ClearableFileInput
            ):

                campo.widget.attrs.update({
                    "class": "form-control",
                })

            elif isinstance(
                campo.widget,
                forms.CheckboxInput
            ):

                campo.widget.attrs.update({
                    "class": "form-check-input",
                })

            else:

                campo.widget.attrs.update({
                    "class": "form-control",
                })

        # ======================================================
        # EQUIPOS
        # ======================================================

        self.fields["hoja_vida"].empty_label = (
            "Seleccione un equipo"
        )

        # ======================================================
        # FILTRO POR SERVICIO DE LA ORDEN
        # ======================================================

        if orden_trabajo:

            servicio = orden_trabajo.servicio

            institucion = servicio.institucion

            self.fields["hoja_vida"].queryset = (
                HojaVida.objects
                .filter(
                    equipo__servicio=servicio,
                    equipo__institucion=institucion,
                )
                .select_related(
                    "equipo",
                    "equipo__servicio",
                    "equipo__institucion",
                )
                .order_by(
                    "equipo__nombre"
                )
            )

        # ======================================================
        # CAMPOS OPCIONALES
        # ======================================================

        self.fields["ingeniero"].required = False

        self.fields["empresa"].required = False

        self.fields["fecha_inicio"].required = False

        self.fields["fecha_fin"].required = False

        self.fields["archivo"].required = False

        self.fields["repuestos"].required = False

        self.fields["observaciones"].required = False

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