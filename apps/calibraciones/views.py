from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CalibracionForm
from .models import Calibracion
from apps.equipos.models import Equipo


@login_required
def lista_calibraciones(request):

    calibraciones = (
        Calibracion.objects
        .select_related("equipo")
        .order_by("-fecha_calibracion", "-creado")
    )

    return render(
        request,
        "calibraciones/lista.html",
        {
            "calibraciones": calibraciones,
        },
    )


@login_required
def crear_calibracion(request):

    if request.method == "POST":

        form = CalibracionForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            calibracion = form.save()

            messages.success(
                request,
                "La calibración fue registrada correctamente.",
            )

            return redirect(
                "calibraciones:lista_calibraciones"
            )

    else:

        form = CalibracionForm()

    return render(
        request,
        "calibraciones/form.html",
        {
            "form": form,
            "titulo": "Nueva calibración",
            "desde_hoja_vida": False,
        },
    )


@login_required
def crear_calibracion_equipo(request, equipo_id):

    # ---------------------------------------------------------
    # OBTENER EL EQUIPO DESDE LA URL
    # ---------------------------------------------------------

    equipo = get_object_or_404(
        Equipo,
        id=equipo_id,
    )

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    if request.method == "POST":

        form = CalibracionForm(
            request.POST,
            request.FILES,
        )

        # -----------------------------------------------------
        # EL EQUIPO VIENE DE LA URL
        # NO DEL FORMULARIO
        # -----------------------------------------------------

        form.fields["equipo"].required = False

        if form.is_valid():

            # No guardamos todavía porque vamos a asignar
            # el equipo manualmente.
            calibracion = form.save(commit=False)

            # Equipo obtenido desde /equipo/<equipo_id>/nueva/
            calibracion.equipo = equipo

            # Guardar calibración
            calibracion.save()

            messages.success(
                request,
                "La calibración fue registrada correctamente.",
            )

            # Regresar a la Hoja de Vida del equipo
            return redirect(
                "detalle_hoja_vida",
                equipo.hoja_vida.id,
            )

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    else:

        form = CalibracionForm()

        # El equipo ya está definido por la URL.
        form.fields["equipo"].required = False

    # ---------------------------------------------------------
    # MOSTRAR FORMULARIO
    # ---------------------------------------------------------

    return render(
        request,
        "calibraciones/form.html",
        {
            "form": form,
            "titulo": "Nueva calibración",
            "equipo": equipo,
            "desde_hoja_vida": True,
        },
    )


@login_required
def editar_calibracion(request, id):

    calibracion = get_object_or_404(
        Calibracion,
        id=id,
    )

    if request.method == "POST":

        form = CalibracionForm(
            request.POST,
            request.FILES,
            instance=calibracion,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "La calibración fue actualizada correctamente.",
            )

            return redirect(
                "calibraciones:lista_calibraciones"
            )

    else:

        form = CalibracionForm(
            instance=calibracion,
        )

    return render(
        request,
        "calibraciones/form.html",
        {
            "form": form,
            "titulo": "Editar calibración",
            "calibracion": calibracion,
        },
    )


@login_required
def eliminar_calibracion(request, id):

    calibracion = get_object_or_404(
        Calibracion,
        id=id,
    )

    if request.method == "POST":

        calibracion.delete()

        messages.success(
            request,
            "La calibración fue eliminada correctamente.",
        )

        return redirect(
            "calibraciones:lista_calibraciones"
        )

    return render(
        request,
        "calibraciones/confirmar_eliminacion.html",
        {
            "calibracion": calibracion,
        },
    )