from django.contrib import admin

from .models import Institucion



@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):


    list_display = (

        "nombre",

        "nit",

        "ciudad",

        "telefono",

        "activa",

        "fecha_creacion",

    )


    list_filter = (

        "activa",

        "departamento",

        "ciudad",

    )


    search_fields = (

        "nombre",

        "nit",

        "ciudad",

    )


    ordering = (

        "nombre",

    )


    readonly_fields = (

        "fecha_creacion",

        "fecha_actualizacion",

    )