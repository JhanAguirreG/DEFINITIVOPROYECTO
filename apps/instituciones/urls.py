from django.urls import path

from . import views



urlpatterns = [


    path(
        "",
        views.instituciones,
        name="lista_instituciones",
    ),



    path(
        "editar/<int:id>/",
        views.editar_institucion,
        name="editar_institucion",
    ),



    path(
        "cambiar-estado/<int:id>/",
        views.cambiar_estado_institucion,
        name="cambiar_estado_institucion",
    ),


]