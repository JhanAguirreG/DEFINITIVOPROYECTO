from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "rol",
        "institucion",
        "is_active",
    )

    list_filter = (
        "rol",
        "institucion",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    ordering = (
        "first_name",
        "last_name",
    )

    fieldsets = (
        (
            "Información de acceso",
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        (
            "Información personal",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "telefono",
                )
            },
        ),
        (
            "SIGHI",
            {
                "fields": (
                    "rol",
                    "institucion",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "telefono",
                    "rol",
                    "institucion",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )