from django.contrib import admin

from .models import (
    CatalogoEquipo,
    PlantillaInspeccion,
    ItemPlantilla,
)


# ==========================================================
# INLINE ITEMS
# ==========================================================

class ItemPlantillaInline(admin.TabularInline):

    model = ItemPlantilla

    extra = 1

    ordering = (
        "orden",
    )

    fields = (
        "orden",
        "descripcion",
        "obligatorio",
    )


# ==========================================================
# CATALOGO
# ==========================================================

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

    list_per_page = 25


# ==========================================================
# PLANTILLAS
# ==========================================================

@admin.register(PlantillaInspeccion)
class PlantillaInspeccionAdmin(admin.ModelAdmin):

    list_display = (
        "catalogo",
        "nombre",
        "activa",
        "cantidad_items",
    )

    list_filter = (
        "activa",
        "catalogo__tecnologia",
        "catalogo__riesgo",
    )

    search_fields = (
        "nombre",
        "catalogo__nombre",
    )

    autocomplete_fields = (
        "catalogo",
    )

    inlines = [
        ItemPlantillaInline,
    ]

    ordering = (
        "catalogo__nombre",
    )

    def cantidad_items(self, obj):
        return obj.items.count()

    cantidad_items.short_description = "Ítems"


# ==========================================================
# ITEMS
# ==========================================================

@admin.register(ItemPlantilla)
class ItemPlantillaAdmin(admin.ModelAdmin):

    list_display = (
        "descripcion",
        "plantilla",
        "orden",
        "obligatorio",
    )

    list_filter = (
        "plantilla",
        "obligatorio",
    )

    search_fields = (
        "descripcion",
        "plantilla__nombre",
        "plantilla__catalogo__nombre",
    )

    autocomplete_fields = (
        "plantilla",
    )

    ordering = (
        "plantilla",
        "orden",
    )