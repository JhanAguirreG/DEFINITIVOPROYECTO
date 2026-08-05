from django.contrib import admin

from .models import Equipo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "nombre",
        "catalogo",
        "marca",
        "modelo",
        "servicio",
        "institucion",
        "estado",
        "activo",
    )

    list_filter = (
        "catalogo",
        "institucion",
        "servicio",
        "estado",
        "activo",
    )

    search_fields = (
        "codigo",
        "inventario",
        "serie",
        "nombre",
        "marca",
        "modelo",
        "catalogo__nombre",
    )

    autocomplete_fields = (
        "institucion",
        "servicio",
        "catalogo",
    )

    ordering = (
        "institucion",
        "servicio",
        "nombre",
    )

    list_per_page = 25

    fieldsets = (

        (
            "Información General",
            {
                "fields": (
                    "institucion",
                    "servicio",
                    "catalogo",
                    "codigo",
                    "inventario",
                    "nombre",
                )
            },
        ),

        (
            "Información Técnica",
            {
                "fields": (
                    "marca",
                    "modelo",
                    "serie",
                    "fabricante",
                    "registro_invima",
                )
            },
        ),

        (
            "Ubicación y Estado",
            {
                "fields": (
                    "ubicacion",
                    "estado",
                    "activo",
                )
            },
        ),

        (
            "Mantenimiento",
            {
                "fields": (
                    "fecha_ultimo_mantenimiento",
                    "fecha_proximo_mantenimiento",
                )
            },
        ),

        (
            "Observaciones",
            {
                "fields": (
                    "observaciones",
                )
            },
        ),

    )