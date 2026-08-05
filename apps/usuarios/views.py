from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.equipos.models import Equipo
from apps.inspecciones.models import Inspeccion
from apps.instituciones.models import Institucion
from apps.servicios.models import Servicio

from .decorators import rol_requerido
from .forms import LoginForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Usuario


# ==========================================================
# LOGIN
# ==========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            login(request, form.get_user())

            return redirect("dashboard")

        messages.error(
            request,
            "Usuario o contraseña incorrectos."
        )

    return render(
        request,
        "usuarios/login.html",
        {
            "form": form
        }
    )


# ==========================================================
# LOGOUT
# ==========================================================

@login_required
def logout_view(request):

    logout(request)

    return redirect("login")


# ==========================================================
# DASHBOARD
# ==========================================================

@login_required
def dashboard(request):

    context = {

        "total_instituciones": Institucion.objects.count(),
        "total_servicios": Servicio.objects.count(),
        "total_equipos": Equipo.objects.count(),
        "total_inspecciones": Inspeccion.objects.count(),

        "ultimas_inspecciones":
            Inspeccion.objects.select_related(
                "equipo",
                "biomedico",
            ).order_by("-id")[:8],

        "equipos_mantenimiento":
            Equipo.objects.filter(
                estado=Equipo.Estado.MANTENIMIENTO
            )[:8],

    }

    return render(
        request,
        "usuarios/dashboard.html",
        context,
    )


@login_required
def redireccionar(request):
    return redirect("dashboard")


# ==========================================================
# LISTA DE USUARIOS
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def lista_usuarios(request):

    if request.user.es_superadmin:

        usuarios = Usuario.objects.select_related(
            "institucion"
        ).order_by(
            "first_name",
            "last_name",
        )

    else:

        usuarios = Usuario.objects.filter(
            institucion=request.user.institucion
        ).order_by(
            "first_name",
            "last_name",
        )

    return render(
        request,
        "usuarios/usuarios.html",
        {
            "usuarios": usuarios,
        },
    )


# ==========================================================
# CREAR USUARIO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_usuario(request):

    if request.method == "POST":

        form = UsuarioCreateForm(request.POST)

        if form.is_valid():

            usuario = form.save(commit=False)

            if request.user.es_admin:

                usuario.institucion = request.user.institucion

                if usuario.rol == Usuario.Roles.SUPERADMIN:

                    usuario.rol = Usuario.Roles.ADMIN

            usuario.save()

            messages.success(
                request,
                "Usuario creado correctamente."
            )

            return redirect("lista_usuarios")

    else:
        
        form = UsuarioCreateForm()
        if request.user.es_admin:

            form.fields["institucion"].queryset = Institucion.objects.filter(
                id=request.user.institucion.id
            )

            form.fields["rol"].choices = [

                (
                    Usuario.Roles.ADMIN,
                    "Administrador",
                ),

                (
                    Usuario.Roles.BIOMEDICO,
                    "Biomédico",
                ),

            ]

    return render(
        request,
        "usuarios/crear_usuario.html",
        {
            "form": form,
            "editar": False,
        },
    )


# ==========================================================
# EDITAR USUARIO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_usuario(request, id):

    usuario = get_object_or_404(
        Usuario,
        id=id,
    )

    if request.user.es_admin:

        if usuario.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos para editar este usuario."
            )

            return redirect("lista_usuarios")

    if request.method == "POST":

        form = UsuarioUpdateForm(
            request.POST,
            instance=usuario,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Usuario actualizado correctamente."
            )

            return redirect("lista_usuarios")

    else:

        form = UsuarioUpdateForm(
            instance=usuario,
        )

    return render(
        request,
        "usuarios/crear_usuario.html",
        {
            "form": form,
            "editar": True,
            "usuario": usuario,
        },
    )


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def cambiar_estado_usuario(request, id):

    usuario = get_object_or_404(
        Usuario,
        id=id,
    )

    if request.user.es_admin:

        if usuario.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos."
            )

            return redirect("lista_usuarios")

    usuario.is_active = not usuario.is_active

    usuario.save()

    messages.success(
        request,
        "Estado del usuario actualizado."
    )

    return redirect("lista_usuarios")