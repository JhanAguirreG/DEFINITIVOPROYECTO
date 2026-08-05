from django.contrib import admin

from .models import HojaVida


@admin.register(HojaVida)
class HojaVidaAdmin(admin.ModelAdmin):

    list_display = (
        "equipo",
        "proveedor",
        "fecha_compra",
        "garantia_hasta",
        "vida_util",
    )

    search_fields = (
        "equipo__codigo",
        "equipo__nombre",
        "equipo__serie",
        "proveedor",
    )

    list_filter = (
        "fecha_compra",
        "garantia_hasta",
    )

    autocomplete_fields = (
        "equipo",
    )

    readonly_fields = (
        "creado",
        "actualizado",
    )

    fieldsets = (

        (
            "Equipo",
            {
                "fields": (
                    "equipo",
                )
            },
        ),

        (
            "Información General",
            {
                "fields": (
                    "fecha_compra",
                    "fecha_instalacion",
                    "proveedor",
                    "vida_util",
                    "garantia_hasta",
                    "costo_adquisicion",
                    "ubicacion_detallada",
                )
            },
        ),

        (
            "Documentación",
            {
                "fields": (
                    "manual_operacion",
                    "manual_servicio",
                    "fotografia",
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

        (
            "Control",
            {
                "fields": (
                    "creado",
                    "actualizado",
                )
            },
        ),

    )