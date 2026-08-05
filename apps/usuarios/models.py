from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado del sistema SIGHI.
    """

    class Roles(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Administrador"
        ADMIN = "ADMIN", "Administrador"
        BIOMEDICO = "BIOMEDICO", "Biomédico"

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.BIOMEDICO,
    )

    institucion = models.ForeignKey(
        "instituciones.Institucion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        nombre = self.get_full_name()
        return nombre if nombre else self.username

    @property
    def es_superadmin(self):
        return self.rol == self.Roles.SUPERADMIN

    @property
    def es_admin(self):
        return self.rol == self.Roles.ADMIN

    @property
    def es_biomedico(self):
        return self.rol == self.Roles.BIOMEDICO