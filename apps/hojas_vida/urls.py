from django.urls import path

from . import views


urlpatterns = [

    # ==================================================
    # Hojas de Vida
    # ==================================================

    path(
        "",
        views.lista_hojas_vida,
        name="lista_hojas_vida",
    ),

    path(
        "nueva/",
        views.crear_hoja_vida,
        name="crear_hoja_vida",
    ),

    path(
        "editar/<int:id>/",
        views.editar_hoja_vida,
        name="editar_hoja_vida",
    ),

    path(
        "detalle/<int:id>/",
        views.detalle_hoja_vida,
        name="detalle_hoja_vida",
    ),

]