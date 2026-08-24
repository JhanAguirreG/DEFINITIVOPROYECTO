from django.contrib import admin

from .models import (
    CatalogoEquipo,
    PlantillaInspeccion,
    ItemPlantilla,
    CampoTecnico,
    GuiaMantenimiento,
    ActividadMantenimiento,
)
# ==========================================================
# INLINE - CARACTERÍSTICAS TÉCNICAS
# ==========================================================

class CampoTecnicoInline(admin.TabularInline):
    model = CampoTecnico

    extra = 1

    fields = (
        "nombre",
        "tipo_dato",
        "unidad",
        "obligatorio",
        "orden",
        "activo",
    )

    ordering = (
        "orden",
        "nombre",
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
# INLINE - ACTIVIDADES DE MANTENIMIENTO
# ==========================================================

class ActividadMantenimientoInline(admin.TabularInline):
    model = ActividadMantenimiento

    extra = 1

    fields = (
        "descripcion",
        "obligatorio",
        "orden",
    )

    ordering = (
        "orden",
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

@admin.register(CampoTecnico)
class CampoTecnicoAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "catalogo",
        "tipo_dato",
        "unidad",
        "obligatorio",
        "orden",
        "activo",
    )

    list_filter = (
        "tipo_dato",
        "obligatorio",
        "activo",
        "catalogo",
    )

    search_fields = (
        "nombre",
        "catalogo__nombre",
    )

    ordering = (
        "catalogo",
        "orden",
        "nombre",
    )

# ==========================================================
# GUÍA DE MANTENIMIENTO
# ==========================================================

@admin.register(GuiaMantenimiento)
class GuiaMantenimientoAdmin(admin.ModelAdmin):

    list_display = (
        "nombre",
        "catalogo",
        "activa",
    )

    list_filter = (
        "activa",
    )

    search_fields = (
        "nombre",
        "catalogo__nombre",
    )

    inlines = [
        ActividadMantenimientoInline,
    ]


# ==========================================================
# ACTIVIDADES DE MANTENIMIENTO
# ==========================================================

@admin.register(ActividadMantenimiento)
class ActividadMantenimientoAdmin(admin.ModelAdmin):

    list_display = (
        "descripcion",
        "guia",
        "obligatorio",
        "orden",
    )

    list_filter = (
        "obligatorio",
    )

    search_fields = (
        "descripcion",
        "guia__nombre",
    )

    ordering = (
        "guia",
        "orden",
    )