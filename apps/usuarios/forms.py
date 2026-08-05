from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    UserChangeForm,
)

from apps.instituciones.models import Institucion
from .models import Usuario


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ingrese su usuario",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ingrese su contraseña",
            }
        ),
    )


class UsuarioCreateForm(UserCreationForm):

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control"}
        ),
    )

    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control"}
        ),
    )

    class Meta:

        model = Usuario

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "telefono",
            "rol",
            "institucion",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")

        self.fields["institucion"].queryset = Institucion.objects.filter(
            activa=True
        )


class UsuarioUpdateForm(UserChangeForm):

    password = None

    class Meta:

        model = Usuario

        fields = (
            "first_name",
            "last_name",
            "email",
            "telefono",
            "rol",
            "institucion",
            "is_active",
        )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Campos normales
        for nombre, campo in self.fields.items():

            if nombre != "is_active":
                campo.widget.attrs.setdefault(
                    "class",
                    "form-control",
                )

        # Solo instituciones activas
        self.fields["institucion"].queryset = Institucion.objects.filter(
            activa=True
        )

        # Estilo Bootstrap para el switch
        self.fields["is_active"].widget.attrs.update({
            "class": "form-check-input",
        })

        self.fields["is_active"].label = "Usuario activo"