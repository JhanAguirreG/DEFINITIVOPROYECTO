from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.usuarios.decorators import rol_requerido

from .forms import MantenimientoForm
from .models import Mantenimiento

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

# ==========================================================
# LISTADO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def lista_mantenimientos(request):

    mantenimientos = (
        Mantenimiento.objects
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "hoja_vida__equipo__institucion",
            "ingeniero",
        )
        .order_by("-fecha_programada")
    )

    if request.user.es_admin or request.user.es_biomedico:

        mantenimientos = mantenimientos.filter(
            hoja_vida__equipo__institucion=request.user.institucion
        )

    hoy = timezone.now().date()

    proximos_30 = hoy + timedelta(days=30)

    context = {

        "mantenimientos": mantenimientos,

        "total_mantenimientos":
            mantenimientos.count(),

        "preventivos":
            mantenimientos.filter(
                tipo=Mantenimiento.Tipo.PREVENTIVO
            ).count(),

        "correctivos":
            mantenimientos.filter(
                tipo=Mantenimiento.Tipo.CORRECTIVO
            ).count(),

        "programados":
            mantenimientos.filter(
                estado=Mantenimiento.Estado.PROGRAMADO
            ).count(),

        "en_proceso":
            mantenimientos.filter(
                estado=Mantenimiento.Estado.EN_PROCESO
            ).count(),

        "finalizados":
            mantenimientos.filter(
                estado=Mantenimiento.Estado.FINALIZADO
            ).count(),

        "vencidos":
            mantenimientos.filter(
                estado=Mantenimiento.Estado.PROGRAMADO,
                fecha_programada__lt=hoy,
            ).count(),

        "proximos":
            mantenimientos.filter(
                estado=Mantenimiento.Estado.PROGRAMADO,
                fecha_programada__gte=hoy,
                fecha_programada__lte=proximos_30,
            ).count(),

    }

    return render(
        request,
        "mantenimiento/index.html",
        context,
    )


# ==========================================================
# CREAR
# ==========================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_mantenimiento(request):

    hoja_id = request.GET.get("hoja")

    if request.method == "POST":

        form = MantenimientoForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            mantenimiento = form.save()

            messages.success(
                request,
                "Mantenimiento registrado correctamente."
            )

            return redirect(
                "detalle_mantenimiento",
                mantenimiento.id,
            )

    else:

        initial = {}

        if hoja_id:

            initial["hoja_vida"] = hoja_id

        form = MantenimientoForm(
            initial=initial
        )

    return render(

        request,

        "mantenimiento/form.html",

        {

            "form": form,

            "titulo": "Nuevo mantenimiento",

        },

    )
# ==========================================================
# EDITAR
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_mantenimiento(request, id):

    mantenimiento = get_object_or_404(
        Mantenimiento,
        id=id,
    )

    if request.user.es_admin:

        if (
            mantenimiento.hoja_vida.equipo.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para editar este mantenimiento."
            )

            return redirect(
                "lista_mantenimientos"
            )

    if request.method == "POST":

        form = MantenimientoForm(
            request.POST,
            request.FILES,
            instance=mantenimiento,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Mantenimiento actualizado correctamente."
            )

            return redirect(
                "lista_mantenimientos"
            )

    else:

        form = MantenimientoForm(
            instance=mantenimiento,
        )

    return render(
        request,
        "mantenimiento/form.html",
        {
            "form": form,
            "titulo": "Editar mantenimiento",
            "editar": True,
        },
    )


# ==========================================================
# DETALLE
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def detalle_mantenimiento(request, id):

    mantenimiento = get_object_or_404(
        Mantenimiento.objects.select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "ingeniero",
        ),
        id=id,
    )

    if request.user.es_admin or request.user.es_biomedico:

        if (
            mantenimiento.hoja_vida.equipo.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para visualizar este mantenimiento."
            )

            return redirect(
                "lista_mantenimientos"
            )

    return render(
        request,
        "mantenimiento/detalle.html",
        {
            "mantenimiento": mantenimiento,
        },
    )