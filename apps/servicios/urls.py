from django.urls import path

from . import views


urlpatterns = [

    # =====================================
    # LISTADO
    # =====================================

    path(
        "",
        views.lista_servicios,
        name="lista_servicios",
    ),

    # =====================================
    # CREAR
    # =====================================

    path(
        "nuevo/",
        views.crear_servicio,
        name="crear_servicio",
    ),

    # =====================================
    # EDITAR
    # =====================================

    path(
        "editar/<int:id>/",
        views.editar_servicio,
        name="editar_servicio",
    ),

    # =====================================
    # ACTIVAR / INACTIVAR
    # =====================================

    path(
        "cambiar-estado/<int:id>/",
        views.cambiar_estado_servicio,
        name="cambiar_estado_servicio",
    ),

]