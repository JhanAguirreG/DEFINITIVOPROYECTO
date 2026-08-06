import base64
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.equipos.models import Equipo
from apps.usuarios.decorators import rol_requerido

from .forms import (
    InspeccionForm,
    ResultadoItemFormSet,
)

from .models import (
    Inspeccion,
    DetalleInspeccion,
    FirmaInspeccion,
    ResultadoItem,
)

# ==========================================================
# UTILIDADES
# ==========================================================

def guardar_firma_base64(data):

    if not data:
        return None

    if "base64," not in data:
        return None

    formato, imagen = data.split(";base64,")

    extension = formato.split("/")[-1]

    nombre = f"{uuid.uuid4()}.{extension}"

    return ContentFile(
        base64.b64decode(imagen),
        name=nombre,
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

        "inspecciones_abiertas":
            inspecciones.filter(
                estado=Inspeccion.Estado.ABIERTA
            ).count(),

        "inspecciones_finalizadas":
            inspecciones.filter(
                estado=Inspeccion.Estado.FINALIZADA
            ).count(),

        "inspecciones_hoy":
          inspecciones.filter(
                fecha=timezone.localdate()
            ).count(),

    }

    return render(
        request,
        "inspecciones/index.html",
        context,
    )

# ==========================================================
# CREAR INSPECCIÓN
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

        form = InspeccionForm(request.POST)

        if form.is_valid():

            inspeccion = form.save(commit=False)

            inspeccion.biomedico = request.user

            inspeccion.save()

            equipos = (
                Equipo.objects.filter(
                    institucion=inspeccion.institucion,
                    servicio=inspeccion.servicio,
                    activo=True,
                )
                .select_related("catalogo")
                .order_by("nombre")
            )

            detalles_creados = 0
            resultados_creados = 0

            for equipo in equipos:

                detalle = DetalleInspeccion.objects.create(
                    inspeccion=inspeccion,
                    equipo=equipo,
                )

                detalles_creados += 1

                if not equipo.catalogo:
                    continue

                try:
                    plantilla = equipo.catalogo.plantilla
                except Exception:
                    plantilla = None

                if not plantilla:
                    continue

                for item in plantilla.items.all():

                    ResultadoItem.objects.get_or_create(
                        detalle=detalle,
                        item=item,
                        defaults={
                            "cumple": True,
                            "observacion": "",
                        },
                    )

                    resultados_creados += 1

            messages.success(
                request,
                f"Inspección creada correctamente. "
                f"Equipos: {detalles_creados} | "
                f"Checklist: {resultados_creados}"
            )

            return redirect(
                "inspecciones:detalle_inspeccion",
                inspeccion.id,
            )

    else:

        form = InspeccionForm()

        if request.user.es_admin or request.user.es_biomedico:

            form.fields["institucion"].initial = request.user.institucion

            form.fields["institucion"].disabled = True

    return render(
        request,
        "inspecciones/nueva.html",
        {
            "form": form,
        },
    )

# ==========================================================
# DETALLE DE INSPECCIÓN
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
        .select_related("equipo")
        .prefetch_related(
            "resultados",
            "resultados__item",
        )
    )

    resultados = ResultadoItem.objects.filter(
        detalle__inspeccion=inspeccion
    ).select_related(
        "detalle",
        "item",
    )

    firma, _ = FirmaInspeccion.objects.get_or_create(
        inspeccion=inspeccion
    )

    if request.method == "POST":

        # ------------------------------------
        # CHECKLIST
        # ------------------------------------

        formset = ResultadoItemFormSet(
            request.POST,
            queryset=resultados,
        )

        if formset.is_valid():
            formset.save()

        # ------------------------------------
        # OBSERVACIONES POR EQUIPO
        # ------------------------------------

        for detalle in detalles:

            detalle.observaciones = request.POST.get(
                f"observaciones_{detalle.id}",
                ""
            )

            detalle.save()

        # ------------------------------------
        # OBSERVACIONES FINALES
        # ------------------------------------

        inspeccion.responsable_servicio = request.POST.get(
            "responsable_servicio",
            ""
        )

        inspeccion.observaciones_finales = request.POST.get(
            "observaciones_finales",
            ""
        )

        inspeccion.save()

        # ------------------------------------
        # FIRMAS
        # ------------------------------------

        firma.responsable_servicio = (
            inspeccion.responsable_servicio
        )

        firma_biomedico = guardar_firma_base64(
            request.POST.get(
                "firma_biomedico"
            )
        )

        if firma_biomedico:

            firma.firma_biomedico.save(
                firma_biomedico.name,
                firma_biomedico,
                save=False,
            )

        firma_responsable = guardar_firma_base64(
            request.POST.get(
                "firma_responsable"
            )
        )

        if firma_responsable:

            firma.firma_responsable.save(
                firma_responsable.name,
                firma_responsable,
                save=False,
            )

        firma.save()

        # ------------------------------------
        # GUARDAR O FINALIZAR
        # ------------------------------------

        accion = request.POST.get("accion")

        if accion == "finalizar":

            inspeccion.estado = (
                Inspeccion.Estado.FINALIZADA
            )

            inspeccion.save()

            messages.success(
                request,
                "Inspección finalizada correctamente."
            )

        else:

            messages.success(
                request,
                "Cambios guardados."
            )

        return redirect(
            "inspecciones:detalle_inspeccion",
            inspeccion.id,
        )

    formset = ResultadoItemFormSet(
        queryset=resultados
    )

    return render(
        request,
        "inspecciones/detalle.html",
        {
            "inspeccion": inspeccion,
            "detalles": detalles,
            "formset": formset,
            "firma": firma,
        },
    )

