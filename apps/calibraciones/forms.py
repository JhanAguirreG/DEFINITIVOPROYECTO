from django import forms

from .models import Calibracion

class CalibracionForm(forms.ModelForm):

    class Meta:
        model = Calibracion

        fields = (
            "equipo",
            "fecha_calibracion",
            "codigo",
            "empresa",
            "certificado",
        )

        widgets = {
            "equipo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "fecha_calibracion": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "codigo": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: CAL-2026-001",
                }
            ),

            "empresa": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Empresa que realizó la calibración",
                }
            ),

            "certificado": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,application/pdf",
                }
            ),
        }

        labels = {
            "equipo": "Equipo",
            "fecha_calibracion": "Fecha de calibración",
            "codigo": "Código de calibración",
            "empresa": "Empresa que realizó la calibración",
            "certificado": "Certificado de calibración (PDF)",
        }

    def __init__(self, *args, **kwargs):
        equipo_requerido = kwargs.pop("equipo_requerido", True)

        super().__init__(*args, **kwargs)

        if not equipo_requerido:
            self.fields["equipo"].required = False

    def clean_certificado(self):
        archivo = self.cleaned_data.get("certificado")

        if archivo:
            if not archivo.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "El certificado debe estar en formato PDF."
                )

        return archivo