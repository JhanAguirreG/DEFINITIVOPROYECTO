from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalogo.models import CatalogoEquipo
from apps.usuarios.decorators import rol_requerido

from .forms import EquipoForm
from .models import Equipo

# ======================================================
# LISTADO
# ======================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def lista_equipos(request):

    # ==========================================================
    # FILTRO POR ESTADO
    # ==========================================================

    estado = request.GET.get("estado")

    # ==========================================================
    # EQUIPOS SEGÚN INSTITUCIÓN
    # ==========================================================

    if request.user.es_superadmin:

        equipos = Equipo.objects.select_related(
            "institucion",
            "servicio",
        )

    else:

        equipos = Equipo.objects.filter(
            institucion=request.user.institucion
        ).select_related(
            "institucion",
            "servicio",
        )

    # ==========================================================
    # APLICAR FILTRO
    # ==========================================================

    if estado:

        estados_validos = [
            Equipo.Estado.ACTIVO,
            Equipo.Estado.MANTENIMIENTO,
            Equipo.Estado.FUERA_SERVICIO,
            Equipo.Estado.BAJA,
        ]

        if estado in estados_validos:

            equipos = equipos.filter(
                estado=estado
            )

    # ==========================================================
    # ORDEN
    # ==========================================================

    if request.user.es_superadmin:

        equipos = equipos.order_by(
            "institucion__nombre",
            "servicio__nombre",
            "nombre",
        )

    else:

        equipos = equipos.order_by(
            "servicio__nombre",
            "nombre",
        )

    # ==========================================================
    # CONTEXTO
    # ==========================================================

    return render(
        request,
        "equipos/index.html",
        {
            "equipos": equipos,
            "estado_filtro": estado,
        },
    )

# ======================================================
# BUSCAR CATÁLOGO AUTOMÁTICAMENTE
# ======================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def buscar_catalogo(request):

    nombre = request.GET.get("nombre", "").strip()

    if not nombre:

        return JsonResponse({
            "encontrado": False,
        })

    catalogos = CatalogoEquipo.objects.filter(
        activo=True
    )

    catalogo = None

    # --------------------------------------------------
    # Búsqueda ignorando mayúsculas/minúsculas
    # --------------------------------------------------

    for item in catalogos:

        if item.nombre.strip().casefold() == nombre.casefold():

            catalogo = item
            break

    if not catalogo:

        return JsonResponse({
            "encontrado": False,
            "nombre": nombre,
        })

    return JsonResponse({

        "encontrado": True,

        "id": catalogo.id,

        "nombre": catalogo.nombre,

        "riesgo": catalogo.get_riesgo_display(),

        "tecnologia": catalogo.get_tecnologia_display(),

        "frecuencia": (
            f"Cada {catalogo.frecuencia_mantenimiento} meses"
        ),

        "requiere_calibracion": (
            "Sí"
            if catalogo.requiere_calibracion
            else "No"
        ),

        "requiere_mantenimiento": (
            "Sí"
            if catalogo.requiere_mantenimiento
            else "No"
        ),

        "descripcion": catalogo.descripcion,
    })
# ======================================================
# CREAR
# ======================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_equipo(request):

    if request.method == "POST":

        form = EquipoForm(request.POST)

        if request.user.es_admin:

            form.fields["institucion"].queryset = (
                form.fields["institucion"].queryset.filter(
                    id=request.user.institucion.id
                )
            )

        if form.is_valid():

            equipo = form.save(commit=False)

            # --------------------------------------------------
            # INSTITUCIÓN
            # --------------------------------------------------

            if request.user.es_admin:

                equipo.institucion = request.user.institucion

            # --------------------------------------------------
            # CATÁLOGO AUTOMÁTICO
            # --------------------------------------------------

            nombre_equipo = form.cleaned_data.get(
                "nombre"
            ).strip()

            catalogo = None

            for item in CatalogoEquipo.objects.filter(
                activo=True
            ):

                if item.nombre.strip().casefold() == (
                    nombre_equipo.casefold()
                ):

                    catalogo = item
                    break

            equipo.catalogo = catalogo

            # --------------------------------------------------
            # GUARDAR
            # --------------------------------------------------

            equipo.save()

            if catalogo:

                messages.success(
                    request,
                    (
                        f"Equipo creado correctamente. "
                        f"Se vinculó automáticamente al catálogo "
                        f"'{catalogo.nombre}'."
                    ),
                )

            else:

                messages.warning(
                    request,
                    (
                        "Equipo creado correctamente, "
                        "pero no tiene un catálogo asociado. "
                        "Se recomienda crear un catálogo para este "
                        "tipo de equipo."
                    ),
                )

            return redirect("lista_equipos")

    else:

        form = EquipoForm()

        if request.user.es_admin:

            form.fields["institucion"].queryset = (
                form.fields["institucion"].queryset.filter(
                    id=request.user.institucion.id
                )
            )

    return render(
        request,
        "equipos/form.html",
        {
            "form": form,
            "titulo": "Nuevo Equipo",
        },
    )

# ======================================================
# EDITAR
# ======================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_equipo(request, id):

    equipo = get_object_or_404(
        Equipo,
        id=id,
    )

    if request.user.es_admin:

        if equipo.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos para editar este equipo."
            )

            return redirect("lista_equipos")

    catalogo_anterior = equipo.catalogo

    if request.method == "POST":

        form = EquipoForm(
            request.POST,
            instance=equipo,
        )

        if request.user.es_admin:

            form.fields["institucion"].queryset = (
                form.fields["institucion"].queryset.filter(
                    id=request.user.institucion.id
                )
            )

        if form.is_valid():

            equipo = form.save(commit=False)

            if request.user.es_admin:

                equipo.institucion = request.user.institucion

            # --------------------------------------------------
            # BUSCAR NUEVAMENTE EL CATÁLOGO
            # --------------------------------------------------

            nombre_equipo = form.cleaned_data.get(
                "nombre"
            ).strip()

            catalogo = None

            for item in CatalogoEquipo.objects.filter(
                activo=True
            ):

                if item.nombre.strip().casefold() == (
                    nombre_equipo.casefold()
                ):

                    catalogo = item
                    break

            # --------------------------------------------------
            # Si existe un catálogo nuevo, usarlo.
            # Si no existe, conservar el anterior.
            # --------------------------------------------------

            if catalogo:

                equipo.catalogo = catalogo

            else:

                equipo.catalogo = catalogo_anterior

            equipo.save()

            messages.success(
                request,
                "Equipo actualizado correctamente."
            )

            return redirect("lista_equipos")

    else:

        form = EquipoForm(
            instance=equipo,
        )

        if request.user.es_admin:

            form.fields["institucion"].queryset = (
                form.fields["institucion"].queryset.filter(
                    id=request.user.institucion.id
                )
            )

    return render(
        request,
        "equipos/form.html",
        {
            "form": form,
            "titulo": "Editar Equipo",
            "equipo": equipo,
        },
    )

# ======================================================
# ACTIVAR / INACTIVAR
# ======================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def cambiar_estado_equipo(request, id):

    equipo = get_object_or_404(
        Equipo,
        id=id,
    )

    if request.user.es_admin:

        if equipo.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos."
            )

            return redirect("lista_equipos")

    equipo.activo = not equipo.activo

    equipo.save()

    messages.success(
        request,
        "Estado actualizado correctamente."
    )

    return redirect("lista_equipos")