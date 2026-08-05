from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.decorators import rol_requerido
from .forms import ServicioForm
from .models import Servicio


# ==========================================================
# LISTADO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def lista_servicios(request):

    if request.user.es_superadmin:

        servicios = Servicio.objects.select_related(
            "institucion"
        ).order_by(
            "institucion__nombre",
            "nombre",
        )

    else:

        servicios = Servicio.objects.filter(
            institucion=request.user.institucion
        ).select_related(
            "institucion"
        ).order_by(
            "nombre",
        )

    context = {
        "servicios": servicios,
    }

    return render(
        request,
        "servicios/index.html",
        context,
    )


# ==========================================================
# CREAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_servicio(request):

    if request.method == "POST":

        form = ServicioForm(request.POST)

        if request.user.es_admin:
            form.fields["institucion"].queryset = form.fields[
                "institucion"
            ].queryset.filter(
                id=request.user.institucion.id
            )

        if form.is_valid():

            servicio = form.save(commit=False)

            if request.user.es_admin:
                servicio.institucion = request.user.institucion

            servicio.save()

            messages.success(
                request,
                "Servicio creado correctamente."
            )

            return redirect("lista_servicios")

    else:

        form = ServicioForm()

        if request.user.es_admin:

            form.fields["institucion"].queryset = form.fields[
                "institucion"
            ].queryset.filter(
                id=request.user.institucion.id
            )

    return render(
        request,
        "servicios/form.html",
        {
            "form": form,
        },
    )


# ==========================================================
# EDITAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_servicio(request, id):

    servicio = get_object_or_404(
        Servicio,
        id=id,
    )

    if (
        request.user.es_admin
        and servicio.institucion != request.user.institucion
    ):

        messages.error(
            request,
            "No tiene permisos para editar este servicio."
        )

        return redirect("lista_servicios")

    if request.method == "POST":

        form = ServicioForm(
            request.POST,
            instance=servicio,
        )

        if request.user.es_admin:

            form.fields["institucion"].queryset = form.fields[
                "institucion"
            ].queryset.filter(
                id=request.user.institucion.id
            )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Servicio actualizado correctamente."
            )

            return redirect("lista_servicios")

    else:

        form = ServicioForm(instance=servicio)

        if request.user.es_admin:

            form.fields["institucion"].queryset = form.fields[
                "institucion"
            ].queryset.filter(
                id=request.user.institucion.id
            )

    return render(
        request,
        "servicios/form.html",
        {
            "form": form,
            "editar": True,
            "servicio": servicio,
        },
    )


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def cambiar_estado_servicio(request, id):

    servicio = get_object_or_404(
        Servicio,
        id=id,
    )

    if (
        request.user.es_admin
        and servicio.institucion != request.user.institucion
    ):

        messages.error(
            request,
            "No tiene permisos."
        )

        return redirect("lista_servicios")

    servicio.activo = not servicio.activo
    servicio.save()

    messages.success(
        request,
        "Estado actualizado correctamente."
    )

    return redirect("lista_servicios")