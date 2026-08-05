from django.urls import path

from . import views


urlpatterns = [

    # ==========================================================
    # MANTENIMIENTOS
    # ==========================================================

    path(
        "",
        views.lista_mantenimientos,
        name="lista_mantenimientos",
    ),

    path(
        "nuevo/",
        views.crear_mantenimiento,
        name="crear_mantenimiento",
    ),

    path(
        "editar/<int:id>/",
        views.editar_mantenimiento,
        name="editar_mantenimiento",
    ),

    path(
        "detalle/<int:id>/",
        views.detalle_mantenimiento,
        name="detalle_mantenimiento",
    ),

]