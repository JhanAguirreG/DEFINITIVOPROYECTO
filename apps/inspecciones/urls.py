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
    # CREAR
    # ======================================================

    path(
        "crear/",
        views.crear_inspeccion,
        name="crear_inspeccion",
    ),


    # ======================================================
    # DETALLE
    # ======================================================

    path(
        "<int:id>/",
        views.detalle_inspeccion,
        name="detalle_inspeccion",
    ),


    # ======================================================
    # RESULTADOS CHECKLIST
    # ======================================================

    path(
        "<int:id>/resultados/",
        views.actualizar_resultados,
        name="actualizar_resultados",
    ),


    # ======================================================
    # FINALIZAR
    # ======================================================

    path(
        "<int:id>/finalizar/",
        views.finalizar_inspeccion,
        name="finalizar_inspeccion",
    ),

]