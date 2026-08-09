from django.urls import path

from . import views


app_name = "inspecciones"


urlpatterns = [

    # ======================================================
    # LISTADO
    # ======================================================

    path(
        "",
        views.lista_inspecciones,
        name="lista_inspecciones",
    ),

    # ======================================================
    # CREAR INSPECCIÓN
    # ======================================================

    path(
        "crear/",
        views.crear_inspeccion,
        name="crear_inspeccion",
    ),

    # ======================================================
    # DETALLE DE INSPECCIÓN
    # ======================================================

    path(
        "<int:id>/",
        views.detalle_inspeccion,
        name="detalle_inspeccion",
    ),

    # ======================================================
    # GENERAR PDF
    # ======================================================

    path(
        "<int:id>/pdf/",
        views.generar_pdf,
        name="generar_pdf",
    ),
]