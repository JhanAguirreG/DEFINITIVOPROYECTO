from django import forms

from .models import HojaVida


class HojaVidaForm(forms.ModelForm):
    """
    Formulario de Hoja de Vida del equipo biomédico.
    """

    class Meta:

        model = HojaVida

        fields = (

            "equipo",

            "fecha_compra",

            "fecha_instalacion",

            "proveedor",

            "vida_util",

            "garantia_hasta",

            "costo_adquisicion",

            "ubicacion_detallada",

            "manual_operacion",

            "manual_servicio",

            "fotografia",

            "observaciones",

        )

        widgets = {

            "fecha_compra": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "fecha_instalacion": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "garantia_hasta": forms.DateInput(
                attrs={
                    "type": "date",
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

                campo.widget.attrs.update(
                    {
                        "class": "form-control",
                    }
                )

            elif isinstance(campo.widget, forms.CheckboxInput):

                campo.widget.attrs.update(
                    {
                        "class": "form-check-input",
                    }
                )

            else:

                campo.widget.attrs.update(
                    {
                        "class": "form-control",
                    }
                )

        self.fields["equipo"].empty_label = "Seleccione un equipo"