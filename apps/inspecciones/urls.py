from django.urls import path

from . import views

app_name = "inspecciones"

urlpatterns = [

    path(
        "",
        views.lista_inspecciones,
        name="lista_inspecciones",
    ),

    path(
        "crear/",
        views.crear_inspeccion,
        name="crear_inspeccion",
    ),

    path(
        "<int:id>/",
        views.detalle_inspeccion,
        name="detalle_inspeccion",
    ),

]