from django.contrib import admin

from .models import Servicio


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "institucion",
        "ubicacion",
        "activo",
        "fecha_creacion",
    )

    list_filter = (
        "institucion",
        "activo",
    )

    search_fields = (
        "nombre",
        "institucion__nombre",
        "ubicacion",
    )

    ordering = (
        "institucion__nombre",
        "nombre",
    )

    list_per_page = 20