from django.contrib import admin

from .models import Mantenimiento


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):

    list_display = (
        "hoja_vida",
        "tipo",
        "estado",
        "fecha_programada",
        "fecha_inicio",
        "fecha_fin",
        "ingeniero",
    )

    search_fields = (
        "hoja_vida__equipo__codigo",
        "hoja_vida__equipo__nombre",
        "hoja_vida__equipo__serie",
        "empresa",
    )

    list_filter = (
        "tipo",
        "estado",
        "fecha_programada",
        "ingeniero",
    )

    autocomplete_fields = (
        "hoja_vida",
        "ingeniero",
    )

    readonly_fields = (
        "creado",
        "actualizado",
    )

    fieldsets = (

        (
            "Información General",
            {
                "fields": (
                    "hoja_vida",
                    "tipo",
                    "estado",
                    "ingeniero",
                    "empresa",
                )
            },
        ),

        (
            "Fechas",
            {
                "fields": (
                    "fecha_programada",
                    "fecha_inicio",
                    "fecha_fin",
                )
            },
        ),

        (
            "Trabajo realizado",
            {
                "fields": (
                    "descripcion",
                    "actividades_realizadas",
                    "repuestos",
                    "costo",
                    "observaciones",
                )
            },
        ),

        (
            "Documentos",
            {
                "fields": (
                    "archivo",
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