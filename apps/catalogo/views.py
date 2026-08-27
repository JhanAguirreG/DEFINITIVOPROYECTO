from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.decorators import rol_requerido

from .forms import CatalogoEquipoForm
from .models import CatalogoEquipo

from apps.equipos.models import Equipo
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
# ==========================================================
# CREAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_catalogo(request):

    # ======================================================
    # EQUIPO QUE SOLICITÓ CREAR EL CATÁLOGO
    # ======================================================

    equipo_id = (
        request.POST.get("equipo_id")
        or request.GET.get("equipo_id")
    )

    equipo = None

    if equipo_id:

        equipo = get_object_or_404(
            Equipo.objects.select_related("institucion"),
            id=equipo_id,
        )

        # ==============================================
        # SEGURIDAD PARA ADMIN
        # ==============================================

        if request.user.es_admin:

            if equipo.institucion != request.user.institucion:

                messages.error(
                    request,
                    "No tiene permisos para asociar un catálogo a este equipo.",
                )

                return redirect("lista_catalogo")

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        form = CatalogoEquipoForm(request.POST)

        if form.is_valid():

            catalogo = form.save()

            # ==============================================
            # ASOCIAR AUTOMÁTICAMENTE AL EQUIPO
            # ==============================================

            if equipo:

                equipo.catalogo = catalogo
                equipo.save(
                    update_fields=["catalogo"]
                )

                messages.success(
                    request,
                    (
                        f"Catálogo '{catalogo.nombre}' creado "
                        f"y asociado correctamente al equipo "
                        f"'{equipo.nombre}'."
                    ),
                )

            else:

                messages.success(
                    request,
                    "Equipo agregado al catálogo correctamente.",
                )

            return redirect("lista_catalogo")

    # ======================================================
    # GET
    # ======================================================

    else:

        form = CatalogoEquipoForm(
            initial={
                "nombre": equipo.nombre if equipo else "",
            }
        )

    return render(
        request,
        "catalogo/form.html",
        {
            "form": form,
            "titulo": "Nuevo Equipo del Catálogo",
            "equipo": equipo,
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
