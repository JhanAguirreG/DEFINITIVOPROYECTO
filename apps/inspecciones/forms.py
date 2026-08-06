from django import forms
from django.forms import modelformset_factory

from .models import (
    Inspeccion,
    FirmaInspeccion,
    ResultadoItem,
    DetalleInspeccion,
)


# ==========================================================
# CREAR INSPECCIÓN
# ==========================================================

class InspeccionForm(forms.ModelForm):

    class Meta:

        model = Inspeccion

        fields = [
            "institucion",
            "servicio",
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

        }


# ==========================================================
# DETALLE DEL EQUIPO
# ==========================================================

class DetalleInspeccionForm(forms.ModelForm):

    class Meta:

        model = DetalleInspeccion

        fields = [

            "estado",

            "observaciones",

        ]

        widgets = {

            "estado": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observaciones del equipo...",
                }
            ),

        }


# ==========================================================
# CHECKLIST
# ==========================================================

class ResultadoItemForm(forms.ModelForm):

    class Meta:

        model = ResultadoItem

        fields = [

            "cumple",

            "observacion",

        ]

        widgets = {

            "cumple": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "observacion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Observación...",
                }
            ),

        }


ResultadoItemFormSet = modelformset_factory(

    ResultadoItem,

    form=ResultadoItemForm,

    extra=0,

)


# ==========================================================
# FIRMA
# ==========================================================
class FirmaInspeccionForm(forms.ModelForm):

    class Meta:
        model = FirmaInspeccion

        fields = [

            "responsable_servicio",

            "observaciones_finales",

            "firma_biomedico",

            "firma_responsable",

        ]

        widgets = {

            "responsable_servicio": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),

            "observaciones_finales": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observaciones finales...",
                }
            ),

            # estos dos campos se ocultarán
            # porque se llenarán mediante JavaScript

            "firma_biomedico": forms.HiddenInput(),

            "firma_responsable": forms.HiddenInput(),

        }