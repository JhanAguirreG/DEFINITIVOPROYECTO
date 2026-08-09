from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.equipos.models import Equipo
from apps.inspecciones.models import (
    Inspeccion,
    DetalleInspeccion,
    ResultadoItem,
)
from apps.instituciones.models import Institucion
from apps.servicios.models import Servicio
from apps.mantenimiento.models import Mantenimiento

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

    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import date

    hoy = timezone.localdate()

    # ==========================================================
    # INDICADORES GENERALES
    # ==========================================================

    total_instituciones = Institucion.objects.count()
    total_servicios = Servicio.objects.count()
    total_equipos = Equipo.objects.count()
    total_inspecciones = Inspeccion.objects.count()

    # ==========================================================
    # MES ACTUAL
    # ==========================================================

    inspecciones_mes = Inspeccion.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month,
    ).count()

    mantenimientos_mes = Mantenimiento.objects.filter(
        fecha_programada__year=hoy.year,
        fecha_programada__month=hoy.month,
    ).count()

    # ==========================================================
    # NOVEDADES
    # ==========================================================

    equipos_observacion = Inspeccion.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month,
        detalles__estado=DetalleInspeccion.EstadoEquipo.OBSERVACION,
    ).distinct().count()

    equipos_fuera_servicio = Equipo.objects.filter(
        estado=Equipo.Estado.FUERA_SERVICIO,
    ).count()

    checklist_no_cumple = ResultadoItem.objects.filter(
        cumple=False,
        detalle__inspeccion__fecha__year=hoy.year,
        detalle__inspeccion__fecha__month=hoy.month,
    ).count()

    novedades_mes = (
        equipos_observacion
        + checklist_no_cumple
    )

    # ==========================================================
    # ESTADO DE MANTENIMIENTOS
    # ==========================================================

    mantenimientos_programados = Mantenimiento.objects.filter(
        estado=Mantenimiento.Estado.PROGRAMADO,
    ).count()

    mantenimientos_proceso = Mantenimiento.objects.filter(
        estado=Mantenimiento.Estado.EN_PROCESO,
    ).count()

    mantenimientos_finalizados = Mantenimiento.objects.filter(
        estado=Mantenimiento.Estado.FINALIZADO,
    ).count()

    # ==========================================================
    # ÚLTIMAS INSPECCIONES
    # ==========================================================

    ultimas_inspecciones = (
        Inspeccion.objects
        .select_related(
            "institucion",
            "servicio",
            "biomedico",
        )
        .prefetch_related(
            "detalles__equipo",
            "detalles__resultados",
        )
        .order_by("-fecha", "-hora_inicio")[:8]
    )

    # Agregar total de novedades a cada inspección
    for inspeccion in ultimas_inspecciones:

        novedades_estado = inspeccion.detalles.filter(
            estado__in=[
                DetalleInspeccion.EstadoEquipo.OBSERVACION,
                DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO,
            ]
        ).count()

        novedades_checklist = ResultadoItem.objects.filter(
            detalle__inspeccion=inspeccion,
            cumple=False,
        ).count()

        inspeccion.novedades_total = (
            novedades_estado
            + novedades_checklist
        )

    # ==========================================================
    # ÚLTIMOS MANTENIMIENTOS
    # ==========================================================

    ultimos_mantenimientos = (
        Mantenimiento.objects
        .select_related(
            "hoja_vida__equipo",
            "ingeniero",
        )
        .order_by("-fecha_programada")[:8]
    )

    # ==========================================================
    # EQUIPOS EN MANTENIMIENTO
    # ==========================================================

    equipos_mantenimiento = (
        Mantenimiento.objects
        .filter(
            estado__in=[
                Mantenimiento.Estado.PROGRAMADO,
                Mantenimiento.Estado.EN_PROCESO,
            ]
        )
        .select_related(
            "hoja_vida__equipo",
        )
        .order_by("fecha_programada")[:8]
    )

    # ==========================================================
    # ESTADÍSTICAS ÚLTIMOS 6 MESES
    # ==========================================================

    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]

    estadisticas_mensuales = []

    for i in range(5, -1, -1):

        año = hoy.year
        mes = hoy.month - i

        if mes <= 0:
            mes += 12
            año -= 1

        inspecciones = Inspeccion.objects.filter(
            fecha__year=año,
            fecha__month=mes,
        ).count()

        novedades_estado = DetalleInspeccion.objects.filter(
            inspeccion__fecha__year=año,
            inspeccion__fecha__month=mes,
            estado__in=[
                DetalleInspeccion.EstadoEquipo.OBSERVACION,
                DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO,
            ],
        ).count()

        novedades_checklist = ResultadoItem.objects.filter(
            detalle__inspeccion__fecha__year=año,
            detalle__inspeccion__fecha__month=mes,
            cumple=False,
        ).count()

        novedades = (
            novedades_estado
            + novedades_checklist
        )

        mantenimientos = Mantenimiento.objects.filter(
            fecha_programada__year=año,
            fecha_programada__month=mes,
        ).count()

        estadisticas_mensuales.append({

            "mes": meses[mes - 1],

            "mes_numero": mes,

            "año": año,

            "inspecciones": inspecciones,

            "novedades": novedades,

            "mantenimientos": mantenimientos,

        })

    # ==========================================================
    # MÁXIMOS PARA LAS BARRAS
    # ==========================================================

    max_inspecciones = max(
        [x["inspecciones"] for x in estadisticas_mensuales],
        default=0,
    )

    max_novedades = max(
        [x["novedades"] for x in estadisticas_mensuales],
        default=0,
    )

    max_mantenimientos = max(
        [x["mantenimientos"] for x in estadisticas_mensuales],
        default=0,
    )

    # ==========================================================
    # CONTEXTO
    # ==========================================================

    context = {

        "total_instituciones": total_instituciones,

        "total_servicios": total_servicios,

        "total_equipos": total_equipos,

        "total_inspecciones": total_inspecciones,

        "inspecciones_mes": inspecciones_mes,

        "novedades_mes": novedades_mes,

        "mantenimientos_mes": mantenimientos_mes,

        "equipos_observacion": equipos_observacion,

        "equipos_fuera_servicio": equipos_fuera_servicio,

        "checklist_no_cumple": checklist_no_cumple,

        "mantenimientos_programados":
            mantenimientos_programados,

        "mantenimientos_proceso":
            mantenimientos_proceso,

        "mantenimientos_finalizados":
            mantenimientos_finalizados,

        "estadisticas_mensuales":
            estadisticas_mensuales,

        "max_inspecciones":
            max_inspecciones,

        "max_novedades":
            max_novedades,

        "max_mantenimientos":
            max_mantenimientos,

        "ultimas_inspecciones":
            ultimas_inspecciones,

        "ultimos_mantenimientos":
            ultimos_mantenimientos,

        "equipos_mantenimiento":
            equipos_mantenimiento,

        "mes_actual_nombre":
            meses[hoy.month - 1],

        "año_actual":
            hoy.year,
            
        "hoy": hoy,

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