from django import forms

from apps.catalogo.models import CatalogoEquipo
from apps.instituciones.models import Institucion
from apps.servicios.models import Servicio

from .models import Equipo


class EquipoForm(forms.ModelForm):

    class Meta:

        model = Equipo

        fields = [

            "institucion",
            "servicio",

            "catalogo",

            "codigo",
            "inventario",

            "nombre",
            "marca",
            "modelo",
            "serie",
            "fabricante",

            "registro_invima",

            "ubicacion",

            "estado",

            "fecha_ultimo_mantenimiento",
            "fecha_proximo_mantenimiento",

            "observaciones",

            "activo",

        ]

        widgets = {

            "institucion": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "servicio": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "catalogo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "inventario": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "marca": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "modelo": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "serie": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "fabricante": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "registro_invima": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "ubicacion": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "fecha_ultimo_mantenimiento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "fecha_proximo_mantenimiento": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),

            "activo": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["institucion"].queryset = Institucion.objects.filter(
            activa=True
        )

        self.fields["servicio"].queryset = Servicio.objects.filter(
            activo=True
        )

        self.fields["catalogo"].queryset = CatalogoEquipo.objects.filter(
            activo=True
        )

        self.fields["codigo"].label = "Código interno"

        self.fields["inventario"].label = "Número de inventario"

        self.fields["catalogo"].label = "Tipo de equipo"

        self.fields["registro_invima"].label = "Registro INVIMA"

        self.fields["fecha_ultimo_mantenimiento"].label = "Último mantenimiento"

        self.fields["fecha_proximo_mantenimiento"].label = "Próximo mantenimiento"