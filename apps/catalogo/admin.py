from django.contrib import admin

from .models import CatalogoEquipo


@admin.register(CatalogoEquipo)
class CatalogoEquipoAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "tecnologia",
        "riesgo",
        "frecuencia_mantenimiento",
        "requiere_calibracion",
        "requiere_mantenimiento",
        "activo",
    )

    list_filter = (
        "tecnologia",
        "riesgo",
        "activo",
        "requiere_calibracion",
        "requiere_mantenimiento",
    )

    search_fields = (
        "nombre",
        "descripcion",
    )

    list_editable = (
        "activo",
    )

    ordering = (
        "nombre",
    )

    list_per_page = 20