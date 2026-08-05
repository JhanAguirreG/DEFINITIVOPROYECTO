from django import forms

from .models import (
    Inspeccion,
    DetalleInspeccion,
    FirmaInspeccion,
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


# ==========================================================
# DETALLE DE INSPECCIÓN
# ==========================================================

class DetalleInspeccionForm(forms.ModelForm):

    class Meta:

        model = DetalleInspeccion

        exclude = (

            "inspeccion",

            "equipo",

        )

        widgets = {

            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Observaciones del equipo...",
                }
            ),

        }


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

        }