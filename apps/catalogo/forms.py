from django import forms

from .models import CatalogoEquipo


class CatalogoEquipoForm(forms.ModelForm):
    """
    Formulario del catálogo maestro de equipos.
    """

    class Meta:

        model = CatalogoEquipo

        fields = [

            "nombre",

            "descripcion",

            "riesgo",

            "tecnologia",

            "requiere_calibracion",

            "requiere_mantenimiento",

            "frecuencia_mantenimiento",

            "activo",

        ]

        widgets = {

            "descripcion": forms.Textarea(
                attrs={
                    "rows": 4,
                }
            ),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            css = "form-control"

            if isinstance(
                field.widget,
                (
                    forms.CheckboxInput,
                ),
            ):

                css = "form-check-input"

            field.widget.attrs.update(
                {
                    "class": css,
                }
            )