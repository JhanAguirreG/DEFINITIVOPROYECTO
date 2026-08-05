from django.contrib import admin

from .models import Equipo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):

    list_display = (
        "codigo",
        "nombre",
        "marca",
        "modelo",
        "servicio",
        "institucion",
        "estado",
        "activo",
    )

    list_filter = (
        "servicio",
        "estado",
        "activo",
    )

    search_fields = (
        "codigo",
        "serie",
        "nombre",
        "marca",
        "modelo",
    )

    ordering = (
        "servicio",
        "nombre",
    )

    list_per_page = 25