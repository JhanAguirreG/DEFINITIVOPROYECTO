from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.decorators import rol_requerido

from .forms import InstitucionForm
from .models import Institucion



@login_required
@rol_requerido(["SUPERADMIN"])
def instituciones(request):

    instituciones = Institucion.objects.all()


    if request.method == "POST":

        form = InstitucionForm(request.POST)


        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Institución creada correctamente."
            )

            return redirect(
                "lista_instituciones"
            )

        else:

            messages.error(
                request,
                "Revise los datos ingresados."
            )


    else:

        form = InstitucionForm()



    context = {
        "instituciones": instituciones,
        "form": form,
    }


    return render(
        request,
        "instituciones/index.html",
        context
    )


@login_required
@rol_requerido(["SUPERADMIN"])
def editar_institucion(request, id):
    """
    Editar institución.
    """


    institucion = get_object_or_404(
        Institucion,
        id=id
    )


    if request.method == "POST":


        form = InstitucionForm(
            request.POST,
            instance=institucion
        )


        if form.is_valid():


            form.save()


            messages.success(
                request,
                "Institución actualizada correctamente."
            )


            return redirect(
                "lista_instituciones"
            )



    else:


        form = InstitucionForm(
            instance=institucion
        )



    return render(
        request,
        "instituciones/editar.html",
        {
            "form": form,
            "institucion": institucion,
        }
    )





@login_required
@rol_requerido(["SUPERADMIN"])
def cambiar_estado_institucion(request, id):
    """
    Activa o desactiva una institución.
    """


    institucion = get_object_or_404(
        Institucion,
        id=id
    )


    institucion.activa = not institucion.activa


    institucion.save()



    messages.success(
        request,
        "Estado de institución actualizado."
    )



    return redirect(
        "lista_instituciones"
    )