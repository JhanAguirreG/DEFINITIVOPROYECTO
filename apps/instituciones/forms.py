from django import forms

from .models import Institucion



class InstitucionForm(forms.ModelForm):
    """
    Formulario para creación y edición de instituciones.
    """

    class Meta:

        model = Institucion


        fields = [
            "nombre",
            "nit",
            "direccion",
            "ciudad",
            "departamento",
            "telefono",
            "correo",
            "representante",
            "activa",
        ]



        widgets = {


            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre de la institución",
                }
            ),



            "nit": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Número de NIT",
                }
            ),



            "direccion": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dirección",
                }
            ),



            "ciudad": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ciudad",
                }
            ),



            "departamento": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Departamento",
                }
            ),



            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Teléfono",
                }
            ),



            "correo": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Correo electrónico",
                }
            ),



            "representante": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Representante legal",
                }
            ),



            "activa": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

        }



    def clean_nit(self):

        nit = self.cleaned_data.get("nit")


        if Institucion.objects.filter(
            nit=nit
        ).exclude(
            id=self.instance.id
        ).exists():

            raise forms.ValidationError(
                "Ya existe una institución registrada con este NIT."
            )


        return nit



    def clean_nombre(self):

        nombre = self.cleaned_data.get("nombre")


        if Institucion.objects.filter(
            nombre__iexact=nombre
        ).exclude(
            id=self.instance.id
        ).exists():

            raise forms.ValidationError(
                "Ya existe una institución con este nombre."
            )


        return nombre