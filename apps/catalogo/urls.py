from django.urls import path

from . import views


urlpatterns = [

    # ==========================
    # Catálogo Maestro
    # ==========================

    path(
        "",
        views.lista_catalogo,
        name="lista_catalogo",
    ),

    path(
        "nuevo/",
        views.crear_catalogo,
        name="crear_catalogo",
    ),

    path(
        "editar/<int:id>/",
        views.editar_catalogo,
        name="editar_catalogo",
    ),

    path(
        "estado/<int:id>/",
        views.cambiar_estado_catalogo,
        name="cambiar_estado_catalogo",
    ),

]