from django import forms
from django.forms import modelformset_factory

from apps.instituciones.models import Institucion
from apps.servicios.models import Servicio

from .models import (
    Inspeccion,
    FirmaInspeccion,
    ResultadoItem,
)


# ==========================================================
# INSPECCIÓN
# ==========================================================

class InspeccionForm(forms.ModelForm):

    class Meta:

        model = Inspeccion

        fields = (
            "institucion",
            "servicio",
            "observaciones_generales",
        )

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

            "observaciones_generales": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Observaciones generales de la ronda...",
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


# ==========================================================
# FIRMA
# ==========================================================

class FirmaInspeccionForm(forms.ModelForm):

    class Meta:

        model = FirmaInspeccion

        fields = (
            "responsable_servicio",
            "firma_biomedico",
            "firma_responsable",
        )

        widgets = {

            "responsable_servicio": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "firma_biomedico": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),

            "firma_responsable": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),

        }


# ==========================================================
# RESULTADO DE ÍTEMS
# ==========================================================

class ResultadoItemForm(forms.ModelForm):

    class Meta:

        model = ResultadoItem

        fields = (
            "cumple",
            "observacion",
        )

        widgets = {

            "cumple": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "observacion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Observación (si aplica)...",
                }
            ),

        }


ResultadoItemFormSet = modelformset_factory(

    ResultadoItem,

    form=ResultadoItemForm,

    extra=0,

)