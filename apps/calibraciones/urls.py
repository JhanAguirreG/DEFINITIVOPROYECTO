from django.urls import path

from . import views


app_name = "calibraciones"


urlpatterns = [
    path(
        "",
        views.lista_calibraciones,
        name="lista_calibraciones",
    ),

    path(
        "nueva/",
        views.crear_calibracion,
        name="crear_calibracion",
    ),

    path(
        "<int:id>/editar/",
        views.editar_calibracion,
        name="editar_calibracion",
    ),

    path(
        "<int:id>/eliminar/",
        views.eliminar_calibracion,
        name="eliminar_calibracion",
    ),
    path(
        "equipo/<int:equipo_id>/nueva/",
        views.crear_calibracion_equipo,
        name="crear_calibracion_equipo",
    ),
]