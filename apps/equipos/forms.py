from django import forms

from apps.catalogo.models import CatalogoEquipo
from apps.instituciones.models import Institucion
from apps.servicios.models import Servicio

from .models import Equipo


class EquipoForm(forms.ModelForm):

    # ==========================================================
    # INFORMACIÓN DEL CATÁLOGO
    # Estos campos son solamente informativos.
    # No se almacenan en Equipo.
    # ==========================================================

    riesgo_catalogo = forms.CharField(
        label="Riesgo INVIMA",
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    tecnologia_catalogo = forms.CharField(
        label="Tipo de tecnología",
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    frecuencia_catalogo = forms.CharField(
        label="Frecuencia de mantenimiento",
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    calibracion_catalogo = forms.CharField(
        label="Requiere calibración",
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    mantenimiento_catalogo = forms.CharField(
        label="Requiere mantenimiento",
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "readonly": "readonly",
            }
        ),
    )

    class Meta:

        model = Equipo

        fields = [

            "institucion",
            "servicio",

            # Se mantiene para guardar la relación,
            # pero no se mostrará como selector.
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

            "catalogo": forms.HiddenInput(),

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
                    "autocomplete": "off",
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

        self.fields["registro_invima"].label = "Registro INVIMA"

        self.fields["fecha_ultimo_mantenimiento"].label = (
            "Último mantenimiento"
        )

        self.fields["fecha_proximo_mantenimiento"].label = (
            "Próximo mantenimiento"
        )

        # ======================================================
        # CARGAR INFORMACIÓN DEL CATÁLOGO EXISTENTE
        # Esto es especialmente importante al EDITAR.
        # ======================================================

        catalogo = self.instance.catalogo if self.instance.pk else None

        if catalogo:

            self.fields["riesgo_catalogo"].initial = (
                catalogo.get_riesgo_display()
            )

            self.fields["tecnologia_catalogo"].initial = (
                catalogo.get_tecnologia_display()
            )

            self.fields["frecuencia_catalogo"].initial = (
                f"Cada {catalogo.frecuencia_mantenimiento} meses"
            )

            self.fields["calibracion_catalogo"].initial = (
                "Sí"
                if catalogo.requiere_calibracion
                else "No"
            )

            self.fields["mantenimiento_catalogo"].initial = (
                "Sí"
                if catalogo.requiere_mantenimiento
                else "No"
            )