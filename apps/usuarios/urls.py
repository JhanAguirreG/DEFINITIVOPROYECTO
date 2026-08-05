from django.urls import path

from . import views

urlpatterns = [

    # ==========================
    # Autenticación
    # ==========================

    path(
        "",
        views.login_view,
        name="login",
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "redireccionar/",
        views.redireccionar,
        name="redireccionar",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    # ==========================
    # Usuarios
    # ==========================

    path(
        "usuarios/",
        views.lista_usuarios,
        name="lista_usuarios",
    ),

    path(
        "usuarios/nuevo/",
        views.crear_usuario,
        name="crear_usuario",
    ),

    path(
        "usuarios/editar/<int:id>/",
        views.editar_usuario,
        name="editar_usuario",
    ),

    path(
        "usuarios/cambiar-estado/<int:id>/",
        views.cambiar_estado_usuario,
        name="cambiar_estado_usuario",
    ),

]