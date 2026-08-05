from django import forms

from .models import Mantenimiento


class MantenimientoForm(forms.ModelForm):
    """
    Formulario de órdenes de trabajo de mantenimiento.
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

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for campo in self.fields.values():

            if isinstance(campo.widget, forms.ClearableFileInput):

                campo.widget.attrs.update({

                    "class": "form-control",

                })

            elif isinstance(campo.widget, forms.CheckboxInput):

                campo.widget.attrs.update({

                    "class": "form-check-input",

                })

            else:

                campo.widget.attrs.update({

                    "class": "form-control",

                })

        self.fields["hoja_vida"].empty_label = (
            "Seleccione un equipo"
        )

        self.fields["ingeniero"].required = False

        self.fields["empresa"].required = False

        self.fields["fecha_inicio"].required = False

        self.fields["fecha_fin"].required = False

        self.fields["archivo"].required = False

        self.fields["repuestos"].required = False

        self.fields["observaciones"].required = False