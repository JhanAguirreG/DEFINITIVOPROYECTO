from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.decorators import rol_requerido

from .forms import CatalogoEquipoForm
from .models import CatalogoEquipo


# ==========================================================
# LISTADO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def lista_catalogo(request):

    catalogo = CatalogoEquipo.objects.all().order_by("nombre")

    return render(
        request,
        "catalogo/index.html",
        {
            "catalogo": catalogo,
        },
    )


# ==========================================================
# CREAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_catalogo(request):

    if request.method == "POST":

        form = CatalogoEquipoForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Equipo agregado al catálogo correctamente.",
            )

            return redirect("lista_catalogo")

    else:

        form = CatalogoEquipoForm()

    return render(
        request,
        "catalogo/form.html",
        {
            "form": form,
            "titulo": "Nuevo Equipo del Catálogo",
        },
    )


# ==========================================================
# EDITAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_catalogo(request, id):

    catalogo = get_object_or_404(
        CatalogoEquipo,
        id=id,
    )

    if request.method == "POST":

        form = CatalogoEquipoForm(
            request.POST,
            instance=catalogo,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Catálogo actualizado correctamente.",
            )

            return redirect("lista_catalogo")

    else:

        form = CatalogoEquipoForm(
            instance=catalogo,
        )

    return render(
        request,
        "catalogo/form.html",
        {
            "form": form,
            "titulo": "Editar Equipo del Catálogo",
            "editar": True,
        },
    )


# ==========================================================
# ACTIVAR / INACTIVAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def cambiar_estado_catalogo(request, id):

    catalogo = get_object_or_404(
        CatalogoEquipo,
        id=id,
    )

    catalogo.activo = not catalogo.activo

    catalogo.save()

    if catalogo.activo:

        messages.success(
            request,
            "Equipo activado correctamente.",
        )

    else:

        messages.success(
            request,
            "Equipo desactivado correctamente.",
        )

    return redirect("lista_catalogo")
