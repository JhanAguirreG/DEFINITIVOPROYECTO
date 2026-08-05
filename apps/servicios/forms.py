from django import forms

from apps.instituciones.models import Institucion
from .models import Servicio


class ServicioForm(forms.ModelForm):
    """
    Formulario para crear y editar servicios.
    """

    class Meta:

        model = Servicio

        fields = (
            "institucion",
            "nombre",
            "descripcion",
            "ubicacion",
            "activo",
        )

        widgets = {

            "descripcion": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for nombre, campo in self.fields.items():

            if nombre != "activo":

                campo.widget.attrs.update({
                    "class": "form-control",
                })

        self.fields["activo"].widget.attrs.update({
            "class": "form-check-input",
        })

        self.fields["activo"].label = "Servicio activo"

        self.fields["institucion"].queryset = Institucion.objects.filter(
            activa=True
        )

    def clean_nombre(self):

        nombre = self.cleaned_data["nombre"]

        return nombre.strip().upper()