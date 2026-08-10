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
 # ======================================================
    # ORDENES DE TRABAJO
    # ======================================================

    path(
        "ordenes/",
        views.lista_ordenes_trabajo,
        name="lista_ordenes_trabajo",
    ),

    path(
        "ordenes/crear/",
        views.crear_orden_trabajo,
        name="crear_orden_trabajo",
    ),

    path(
        "ordenes/detalle/<int:id>/",
        views.detalle_orden_trabajo,
        name="detalle_orden_trabajo",
    ),

    path(
        "ordenes/editar/<int:id>/",
        views.editar_orden_trabajo,
        name="editar_orden_trabajo",
    ),

    path(
        "ordenes/<int:id>/agregar/",
        views.agregar_mantenimiento_orden,
        name="agregar_mantenimiento_orden",
    ),

    path(
        "ordenes/<int:id>/quitar/<int:mantenimiento_id>/",
        views.quitar_mantenimiento_orden,
        name="quitar_mantenimiento_orden",
    ),

    # ======================================================
    # FIRMAR ORDEN
    # ======================================================

    path(
        "ordenes/<int:id>/firmar/",
        views.firmar_orden_trabajo,
        name="firmar_orden_trabajo",
    ),
    path(
        "ordenes/<int:id>/pdf/",
        views.pdf_orden_trabajo,
        name="pdf_orden_trabajo",
    ),
    path(
        "eliminar/<int:id>/",
        views.eliminar_mantenimiento,
        name="eliminar_mantenimiento",
    ),
    path(
        "ordenes/eliminar/<int:id>/",
        views.eliminar_orden_trabajo,
        name="eliminar_orden_trabajo",
    ),

]