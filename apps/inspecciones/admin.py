from django.contrib import admin

from .models import (
    Inspeccion,
    DetalleInspeccion,
    FirmaInspeccion,
    ResultadoItem,
)


# ==========================================================
# INLINE RESULTADOS
# ==========================================================

class ResultadoItemInline(admin.TabularInline):

    model = ResultadoItem

    extra = 0

    autocomplete_fields = (
        "item",
    )

    fields = (
        "item",
        "cumple",
        "observacion",
    )


# ==========================================================
# INSPECCION
# ==========================================================
@admin.register(Inspeccion)
class InspeccionAdmin(admin.ModelAdmin):

    list_display = (
        "fecha",
        "institucion",
        "servicio",
        "biomedico",
        "estado",
    )

    list_filter = (
        "estado",
        "institucion",
        "servicio",
        "fecha",
    )

    search_fields = (
        "institucion__nombre",
        "servicio__nombre",
        "biomedico__first_name",
        "biomedico__last_name",
    )

    autocomplete_fields = (
        "institucion",
        "servicio",
        "biomedico",
    )

    date_hierarchy = "fecha"

    ordering = (
        "-fecha",
        "-hora_inicio",
    )

# ==========================================================
# DETALLE INSPECCION
# ==========================================================
@admin.register(DetalleInspeccion)
class DetalleInspeccionAdmin(admin.ModelAdmin):

    list_display = (
        "inspeccion",
        "equipo",
        "estado",
        "funcionamiento_correcto",
    )

    list_filter = (
        "estado",
        "equipo__institucion",
        "equipo__servicio",
    )

    search_fields = (
        "equipo__nombre",
        "equipo__codigo",
        "equipo__serie",
    )

    autocomplete_fields = (
        "inspeccion",
        "equipo",
    )

    inlines = [
        ResultadoItemInline,
    ]

# ==========================================================
# FIRMA
# ==========================================================

@admin.register(FirmaInspeccion)
class FirmaInspeccionAdmin(admin.ModelAdmin):

    list_display = (
        "inspeccion",
        "responsable_servicio",
        "fecha_firma",
    )

    search_fields = (
        "responsable_servicio",
        "inspeccion__servicio__nombre",
    )

    autocomplete_fields = (
        "inspeccion",
    )


# ==========================================================
# RESULTADOS
# ==========================================================

@admin.register(ResultadoItem)
class ResultadoItemAdmin(admin.ModelAdmin):

    list_display = (
        "detalle",
        "item",
        "cumple",
    )

    list_filter = (
        "cumple",
        "item__plantilla",
    )

    search_fields = (
        "detalle__equipo__nombre",
        "item__descripcion",
    )

    autocomplete_fields = (
        "detalle",
        "item",
    )