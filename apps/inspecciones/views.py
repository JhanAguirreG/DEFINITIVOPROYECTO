from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.equipos.models import Equipo
from apps.usuarios.decorators import rol_requerido

from .forms import (
    InspeccionForm,
    FirmaInspeccionForm,
    ResultadoItemFormSet,
)

from .models import (
    Inspeccion,
    DetalleInspeccion,
    FirmaInspeccion,
    ResultadoItem,
)


# ==========================================================
# LISTADO
# ==========================================================

@login_required
@rol_requerido(
    [
        "SUPERADMIN",
        "ADMIN",
        "BIOMEDICO",
    ]
)
def lista_inspecciones(request):

    inspecciones = (
        Inspeccion.objects
        .select_related(
            "institucion",
            "servicio",
            "biomedico",
        )
        .order_by(
            "-fecha",
            "-hora_inicio",
        )
    )


    if request.user.es_admin or request.user.es_biomedico:

        inspecciones = inspecciones.filter(
            institucion=request.user.institucion
        )


    context = {

        "inspecciones": inspecciones,

        "total_inspecciones": inspecciones.count(),

        "inspecciones_abiertas":
            inspecciones.filter(
                estado=Inspeccion.Estado.ABIERTA
            ).count(),

        "inspecciones_finalizadas":
            inspecciones.filter(
                estado=Inspeccion.Estado.FINALIZADA
            ).count(),

    }


    return render(
        request,
        "inspecciones/index.html",
        context,
    )



# ==========================================================
# CREAR INSPECCION
# ==========================================================

@login_required
@rol_requerido(
    [
        "SUPERADMIN",
        "ADMIN",
        "BIOMEDICO",
    ]
)
@transaction.atomic
def crear_inspeccion(request):


    if request.method == "POST":

        form = InspeccionForm(
            request.POST
        )


        if form.is_valid():

            inspeccion = form.save(
                commit=False
            )


            inspeccion.biomedico = request.user

            inspeccion.save()



            equipos = (
                Equipo.objects
                .filter(
                    institucion=inspeccion.institucion,
                    servicio=inspeccion.servicio,
                    activo=True,
                )
                .select_related(
                    "catalogo",
                )
                .order_by(
                    "nombre"
                )
            )



            for equipo in equipos:


                detalle = DetalleInspeccion.objects.create(

                    inspeccion=inspeccion,

                    equipo=equipo,

                )


                # Crear checklist desde catálogo

                if hasattr(
                    equipo,
                    "catalogo"
                ) and equipo.catalogo:


                    plantilla = getattr(
                        equipo.catalogo,
                        "plantilla",
                        None
                    )


                    if plantilla:


                        for item in plantilla.items.all():


                            ResultadoItem.objects.create(

                                detalle=detalle,

                                item=item,

                            )



            messages.success(
                request,
                "Inspección creada correctamente."
            )


            return redirect("inspecciones:detalle_inspeccion", inspeccion.id)


    else:


        form = InspeccionForm()


        if request.user.es_admin or request.user.es_biomedico:

            form.fields[
                "institucion"
            ].initial = request.user.institucion



    return render(

        request,

        "inspecciones/nueva.html",

        {
            "form": form,
        },

    )



# ==========================================================
# DETALLE
# ==========================================================

@login_required
@rol_requerido(
    [
        "SUPERADMIN",
        "ADMIN",
        "BIOMEDICO",
    ]
)
def detalle_inspeccion(request, id):


    inspeccion = get_object_or_404(

        Inspeccion.objects.select_related(

            "institucion",

            "servicio",

            "biomedico",

        ),

        id=id,

    )



    detalles = (

        inspeccion.detalles

        .select_related(
            "equipo",
        )

        .prefetch_related(
            "resultados__item",
        )

    )



    return render(

        request,

        "inspecciones/detalle.html",

        {

            "inspeccion": inspeccion,

            "detalles": detalles,

        },

    )



# ==========================================================
# ACTUALIZAR RESULTADOS
# ==========================================================

@login_required
@rol_requerido(
    [
        "SUPERADMIN",
        "ADMIN",
        "BIOMEDICO",
    ]
)
@transaction.atomic
def actualizar_resultados(request, id):


    inspeccion = get_object_or_404(

        Inspeccion,

        id=id,

    )


    resultados = ResultadoItem.objects.filter(

        detalle__inspeccion=inspeccion

    )



    formset = ResultadoItemFormSet(

        request.POST or None,

        queryset=resultados,

    )


    if request.method == "POST":


        if formset.is_valid():

            formset.save()


            messages.success(

                request,

                "Resultados actualizados."

            )


            return redirect("inspecciones:detalle_inspeccion", inspeccion.id)



    return render(

        request,

        "inspecciones/resultados.html",

        {

            "inspeccion": inspeccion,

            "formset": formset,

        },

    )



# ==========================================================
# FINALIZAR
# ==========================================================

@login_required
@rol_requerido(
    [
        "SUPERADMIN",
        "ADMIN",
        "BIOMEDICO",
    ]
)
def finalizar_inspeccion(request, id):


    inspeccion = get_object_or_404(

        Inspeccion,

        id=id,

    )


    if request.method == "POST":


        form = FirmaInspeccionForm(

            request.POST,

            request.FILES,

        )


        if form.is_valid():


            firma = form.save(

                commit=False

            )


            firma.inspeccion = inspeccion

            firma.save()



            inspeccion.estado = (

                Inspeccion.Estado.FINALIZADA

            )

            inspeccion.save()



            messages.success(

                request,

                "Inspección finalizada."

            )



            return redirect("inspecciones:detalle_inspeccion", inspeccion.id)


    else:


        form = FirmaInspeccionForm()



    return render(

        request,

        "inspecciones/finalizar.html",

        {

            "inspeccion": inspeccion,

            "form": form,

        },

    )