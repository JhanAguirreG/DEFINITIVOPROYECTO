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

    # ==========================================================
    # FECHA ACTUAL
    # ==========================================================

    hoy = timezone.localdate()

    mes_actual = hoy.month
    año_actual = hoy.year

    meses = [
        "",
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

    mes_actual_nombre = meses[mes_actual]


    # ==========================================================
    # INDICADORES GENERALES
    # ==========================================================

    total_instituciones = Institucion.objects.count()

    total_servicios = Servicio.objects.count()

    total_equipos = Equipo.objects.count()

    total_inspecciones = Inspeccion.objects.count()


    # ==========================================================
    # INSPECCIONES DEL MES
    # ==========================================================

    inspecciones_mes = Inspeccion.objects.filter(
        fecha__year=año_actual,
        fecha__month=mes_actual,
    ).count()


    # ==========================================================
    # DETALLES DEL MES
    # ==========================================================

    detalles_mes = DetalleInspeccion.objects.filter(
        inspeccion__fecha__year=año_actual,
        inspeccion__fecha__month=mes_actual,
    )


    # ==========================================================
    # NOVEDADES DEL MES
    #
    # Una novedad puede ser:
    #
    # 1. Equipo con observaciones
    # 2. Equipo fuera de servicio
    # 3. Checklist que no cumple
    # ==========================================================

    equipos_observacion_mes = detalles_mes.filter(
        estado=DetalleInspeccion.EstadoEquipo.OBSERVACION
    ).count()


    equipos_fuera_servicio_mes = detalles_mes.filter(
        estado=DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO
    ).count()


    checklist_no_cumple_mes = ResultadoItem.objects.filter(
        detalle__inspeccion__fecha__year=año_actual,
        detalle__inspeccion__fecha__month=mes_actual,
        cumple=False,
    ).count()


    novedades_mes = (
        equipos_observacion_mes
        + equipos_fuera_servicio_mes
        + checklist_no_cumple_mes
    )


    # ==========================================================
    # ESTADO GENERAL DE NOVEDADES
    # ==========================================================

    equipos_observacion = DetalleInspeccion.objects.filter(
        estado=DetalleInspeccion.EstadoEquipo.OBSERVACION
    ).count()


    equipos_fuera_servicio = DetalleInspeccion.objects.filter(
        estado=DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO
    ).count()


    checklist_no_cumple = ResultadoItem.objects.filter(
        cumple=False
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
            "firma",
        )
        .prefetch_related(
            "detalles__equipo",
            "detalles__resultados",
        )
        .order_by(
            "-fecha",
            "-hora_inicio",
        )[:8]
    )


    # ==========================================================
    # AGREGAR NÚMERO DE NOVEDADES A CADA INSPECCIÓN
    # ==========================================================

    for inspeccion in ultimas_inspecciones:

        novedades = 0

        for detalle in inspeccion.detalles.all():

            if detalle.estado in [
                DetalleInspeccion.EstadoEquipo.OBSERVACION,
                DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO,
            ]:
                novedades += 1

            novedades += detalle.resultados.filter(
                cumple=False
            ).count()

        inspeccion.novedades_total = novedades


    # ==========================================================
    # MANTENIMIENTOS DEL MES
    # ==========================================================

    mantenimientos_mes = Mantenimiento.objects.filter(
        fecha_programada__year=año_actual,
        fecha_programada__month=mes_actual,
    ).count()


    # ==========================================================
    # ESTADO DE MANTENIMIENTOS
    # ==========================================================

    mantenimientos_programados = Mantenimiento.objects.filter(
        estado=Mantenimiento.Estado.PROGRAMADO
    ).count()


    mantenimientos_proceso = Mantenimiento.objects.filter(
        estado=Mantenimiento.Estado.EN_PROCESO
    ).count()


    mantenimientos_finalizados = Mantenimiento.objects.filter(
        estado=Mantenimiento.Estado.FINALIZADO
    ).count()


    # ==========================================================
    # ÚLTIMOS MANTENIMIENTOS
    # ==========================================================

    ultimos_mantenimientos = (
        Mantenimiento.objects
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "ingeniero",
        )
        .order_by(
            "-fecha_programada"
        )[:8]
    )


    # ==========================================================
    # EQUIPOS CON MANTENIMIENTO PENDIENTE
    # ==========================================================

    equipos_mantenimiento = (
        Mantenimiento.objects
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
        )
        .filter(
            estado__in=[
                Mantenimiento.Estado.PROGRAMADO,
                Mantenimiento.Estado.EN_PROCESO,
            ]
        )
        .order_by(
            "fecha_programada"
        )[:8]
    )


    # ==========================================================
    # ESTADÍSTICAS DE LOS ÚLTIMOS 6 MESES
    # ==========================================================

    estadisticas_mensuales = []


    for i in range(5, -1, -1):

        # Calcular mes anterior
        mes = mes_actual - i
        año = año_actual

        while mes <= 0:

            mes += 12
            año -= 1


        # ------------------------------------------------------
        # INSPECCIONES
        # ------------------------------------------------------

        inspecciones = Inspeccion.objects.filter(
            fecha__year=año,
            fecha__month=mes,
        ).count()


        # ------------------------------------------------------
        # DETALLES DE INSPECCIÓN
        # ------------------------------------------------------

        detalles = DetalleInspeccion.objects.filter(
            inspeccion__fecha__year=año,
            inspeccion__fecha__month=mes,
        )


        observaciones = detalles.filter(
            estado=DetalleInspeccion.EstadoEquipo.OBSERVACION
        ).count()


        fuera_servicio = detalles.filter(
            estado=DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO
        ).count()


        # ------------------------------------------------------
        # CHECKLIST
        # ------------------------------------------------------

        checklist = ResultadoItem.objects.filter(
            detalle__inspeccion__fecha__year=año,
            detalle__inspeccion__fecha__month=mes,
            cumple=False,
        ).count()


        novedades = (
            observaciones
            + fuera_servicio
            + checklist
        )


        # ------------------------------------------------------
        # MANTENIMIENTOS
        # ------------------------------------------------------

        mantenimientos = Mantenimiento.objects.filter(
            fecha_programada__year=año,
            fecha_programada__month=mes,
        ).count()


        estadisticas_mensuales.append({

            "mes": meses[mes],

            "año": año,

            "inspecciones": inspecciones,

            "novedades": novedades,

            "mantenimientos": mantenimientos,

        })


    # ==========================================================
    # MÁXIMOS PARA LAS BARRAS DEL DASHBOARD
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

        # ------------------------------------------------------
        # GENERALES
        # ------------------------------------------------------

        "total_instituciones":
            total_instituciones,

        "total_servicios":
            total_servicios,

        "total_equipos":
            total_equipos,

        "total_inspecciones":
            total_inspecciones,


        # ------------------------------------------------------
        # FECHA
        # ------------------------------------------------------

        "mes_actual_nombre":
            mes_actual_nombre,

        "año_actual":
            año_actual,


        # ------------------------------------------------------
        # MES
        # ------------------------------------------------------

        "inspecciones_mes":
            inspecciones_mes,

        "novedades_mes":
            novedades_mes,

        "mantenimientos_mes":
            mantenimientos_mes,


        # ------------------------------------------------------
        # NOVEDADES
        # ------------------------------------------------------

        "equipos_observacion":
            equipos_observacion,

        "equipos_fuera_servicio":
            equipos_fuera_servicio,

        "checklist_no_cumple":
            checklist_no_cumple,


        # ------------------------------------------------------
        # MANTENIMIENTOS
        # ------------------------------------------------------

        "mantenimientos_programados":
            mantenimientos_programados,

        "mantenimientos_proceso":
            mantenimientos_proceso,

        "mantenimientos_finalizados":
            mantenimientos_finalizados,


        # ------------------------------------------------------
        # INSPECCIONES
        # ------------------------------------------------------

        "ultimas_inspecciones":
            ultimas_inspecciones,


        # ------------------------------------------------------
        # MANTENIMIENTOS
        # ------------------------------------------------------

        "ultimos_mantenimientos":
            ultimos_mantenimientos,

        "equipos_mantenimiento":
            equipos_mantenimiento,


        # ------------------------------------------------------
        # ESTADÍSTICAS
        # ------------------------------------------------------

        "estadisticas_mensuales":
            estadisticas_mensuales,

        "max_inspecciones":
            max_inspecciones,

        "max_novedades":
            max_novedades,

        "max_mantenimientos":
            max_mantenimientos,

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