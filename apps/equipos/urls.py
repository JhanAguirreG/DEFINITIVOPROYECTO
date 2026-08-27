from django.urls import path

from . import views

urlpatterns = [

    # ==========================================
    # LISTADO
    # ==========================================

    path(
        "",
        views.lista_equipos,
        name="lista_equipos",
    ),

    # ==========================================
    # CREAR
    # ==========================================

    path(
        "nuevo/",
        views.crear_equipo,
        name="crear_equipo",
    ),

    # ==========================================
    # EDITAR
    # ========================================= =

    path(
        "editar/<int:id>/",
        views.editar_equipo,
        name="editar_equipo",
    ),

    # ==========================================
    # ACTIVAR / INACTIVAR
    # ==========================================

    path(
        "cambiar-estado/<int:id>/",
        views.cambiar_estado_equipo,
        name="cambiar_estado_equipo",
    ),

    path(
        "buscar-catalogo/",
        views.buscar_catalogo,
        name="buscar_catalogo",
    ),

]