from datetime import date, timedelta
from calendar import month_name

from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count, Q

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
# DASHBOARD GENERAL
# ==========================================================
@login_required
def dashboard(request):

    # ==========================================================
    # FECHAS
    # ==========================================================

    hoy = timezone.localdate()

    año_actual = hoy.year
    mes_actual = hoy.month

    meses_es = [
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

    meses_cortos = [
        "",
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]

    mes_actual_nombre = meses_es[mes_actual]


    # ==========================================================
    # FILTRO POR INSTITUCIÓN
    # ==========================================================

    es_superadmin = getattr(
        request.user,
        "es_superadmin",
        False
    )

    es_admin = getattr(
        request.user,
        "es_admin",
        False
    )

    es_biomedico = getattr(
        request.user,
        "es_biomedico",
        False
    )


    # ==========================================================
    # QUERYSETS BASE
    # ==========================================================

    instituciones = Institucion.objects.all()

    servicios = Servicio.objects.all()

    equipos = Equipo.objects.all()

    inspecciones = Inspeccion.objects.all()

    mantenimientos = Mantenimiento.objects.all()


    # ==========================================================
    # RESTRICCIÓN PARA ADMIN Y BIOMÉDICO
    # ==========================================================

    if not es_superadmin and (es_admin or es_biomedico):

        institucion_usuario = getattr(
            request.user,
            "institucion",
            None
        )

        if institucion_usuario:

            instituciones = instituciones.filter(
                pk=institucion_usuario.pk
            )

            servicios = servicios.filter(
                institucion=institucion_usuario
            )

            equipos = equipos.filter(
                institucion=institucion_usuario
            )

            inspecciones = inspecciones.filter(
                institucion=institucion_usuario
            )

            mantenimientos = mantenimientos.filter(
                hoja_vida__equipo__institucion=institucion_usuario
            )


    # ==========================================================
    # INDICADORES GENERALES
    # ==========================================================

    total_instituciones = instituciones.count()

    total_servicios = servicios.count()

    total_equipos = equipos.count()

    total_inspecciones = inspecciones.count()


    # ==========================================================
    # INICIO Y FIN DEL MES ACTUAL
    # ==========================================================

    primer_dia_mes = date(
        año_actual,
        mes_actual,
        1
    )

    if mes_actual == 12:

        primer_dia_mes_siguiente = date(
            año_actual + 1,
            1,
            1
        )

    else:

        primer_dia_mes_siguiente = date(
            año_actual,
            mes_actual + 1,
            1
        )


    # ==========================================================
    # INSPECCIONES DEL MES
    # ==========================================================

    inspecciones_mes_qs = inspecciones.filter(
        fecha__gte=primer_dia_mes,
        fecha__lt=primer_dia_mes_siguiente,
    )

    inspecciones_mes = inspecciones_mes_qs.count()


    # ==========================================================
    # NOVEDADES
    #
    # Se considera novedad cuando un detalle:
    #
    # - está en observación
    # - está fuera de servicio
    # - tiene observaciones escritas
    # - tiene algún checklist que no cumple
    #
    # Se cuenta el detalle una sola vez.
    # ==========================================================

    filtro_novedad = (
        Q(detalles__estado=DetalleInspeccion.EstadoEquipo.OBSERVACION)
        |
        Q(detalles__estado=DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO)
        |
        ~Q(detalles__observaciones="")
        |
        Q(detalles__resultados__cumple=False)
    )
    filtro_novedad_detalle = (
        Q(estado=DetalleInspeccion.EstadoEquipo.OBSERVACION)
        |
        Q(estado=DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO)
        |
        ~Q(observaciones="")
        |
        Q(resultados__cumple=False)
    )
    filtro_novedad_inspeccion = (
        Q(detalles__estado=DetalleInspeccion.EstadoEquipo.OBSERVACION)
        |
        Q(detalles__estado=DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO)
        |
        ~Q(detalles__observaciones="")
        |
        Q(detalles__resultados__cumple=False)
    )


    # ==========================================================
    # NOVEDADES DEL MES
    # ==========================================================

    novedades_mes = (
        DetalleInspeccion.objects
        .filter(
            inspeccion__in=inspecciones_mes_qs
        )
        .filter(
            filtro_novedad_detalle
        )
        .distinct()
        .count()
    )

    # ==========================================================
    # EQUIPOS CON OBSERVACIONES
    # ==========================================================

    equipos_observacion = (
        equipos
        .filter(
            estado=Equipo.Estado.MANTENIMIENTO
        )
        .count()
    )


    # ==========================================================
    # EQUIPOS FUERA DE SERVICIO
    # ==========================================================

    equipos_fuera_servicio = (
        equipos
        .filter(
            estado=Equipo.Estado.FUERA_SERVICIO
        )
        .count()
    )


    # ==========================================================
    # CHECKLIST NO CUMPLE
    # ==========================================================

    checklist_no_cumple = (
        ResultadoItem.objects
        .filter(
            cumple=False,
            detalle__inspeccion__in=inspecciones_mes_qs,
        )
        .count()
    )


    # ==========================================================
    # MANTENIMIENTOS DEL MES
    # ==========================================================

    mantenimientos_mes = (
        mantenimientos
        .filter(
            fecha_programada__gte=primer_dia_mes,
            fecha_programada__lt=primer_dia_mes_siguiente,
        )
        .count()
    )


    # ==========================================================
    # ESTADOS DE MANTENIMIENTOS
    # ==========================================================

    mantenimientos_programados = (
        mantenimientos
        .filter(
            estado=Mantenimiento.Estado.PROGRAMADO
        )
        .count()
    )


    mantenimientos_proceso = (
        mantenimientos
        .filter(
            estado=Mantenimiento.Estado.EN_PROCESO
        )
        .count()
    )


    mantenimientos_finalizados = (
        mantenimientos
        .filter(
            estado=Mantenimiento.Estado.FINALIZADO
        )
        .count()
    )


    # ==========================================================
    # ÚLTIMOS 6 MESES
    # ==========================================================

    estadisticas_mensuales = []

    total_inspecciones_6_meses = 0

    total_novedades_6_meses = 0

    total_mantenimientos_6_meses = 0


    # Guardaremos los meses desde el más antiguo
    # hasta el actual.

    meses_calculados = []

    año = año_actual
    mes = mes_actual

    for _ in range(6):

        meses_calculados.append(
            (año, mes)
        )

        mes -= 1

        if mes == 0:

            mes = 12
            año -= 1


    meses_calculados.reverse()


    # ==========================================================
    # ESTADÍSTICAS MES POR MES
    # ==========================================================

    for año_mes, mes_numero in meses_calculados:

        inicio = date(
            año_mes,
            mes_numero,
            1
        )


        if mes_numero == 12:

            fin = date(
                año_mes + 1,
                1,
                1
            )

        else:

            fin = date(
                año_mes,
                mes_numero + 1,
                1
            )


        # ------------------------------------------------------
        # INSPECCIONES
        # ------------------------------------------------------

        inspecciones_periodo = inspecciones.filter(
            fecha__gte=inicio,
            fecha__lt=fin,
        )


        cantidad_inspecciones = (
            inspecciones_periodo.count()
        )


        # ------------------------------------------------------
        # NOVEDADES
        # ------------------------------------------------------

        cantidad_novedades = (
            DetalleInspeccion.objects
            .filter(
                inspeccion__in=inspecciones_periodo
            )
            .filter(
                filtro_novedad_detalle
            )
            .distinct()
            .count()
        )


        # ------------------------------------------------------
        # MANTENIMIENTOS
        # ------------------------------------------------------

        cantidad_mantenimientos = (
            mantenimientos
            .filter(
                fecha_programada__gte=inicio,
                fecha_programada__lt=fin,
            )
            .count()
        )


        # ------------------------------------------------------
        # ACUMULADOS
        # ------------------------------------------------------

        total_inspecciones_6_meses += (
            cantidad_inspecciones
        )

        total_novedades_6_meses += (
            cantidad_novedades
        )

        total_mantenimientos_6_meses += (
            cantidad_mantenimientos
        )


        # ------------------------------------------------------
        # OBJETO PARA EL HTML
        # ------------------------------------------------------

        estadisticas_mensuales.append(
            {
                "mes": meses_es[mes_numero],
                "mes_corto": meses_cortos[mes_numero],
                "año": año_mes,

                "inspecciones":
                    cantidad_inspecciones,

                "novedades":
                    cantidad_novedades,

                "mantenimientos":
                    cantidad_mantenimientos,
            }
        )


    # ==========================================================
    # DATOS PARA CHART.JS
    # ==========================================================

    etiquetas_grafico = [

        f"{estadistica['mes_corto']} "
        f"{estadistica['año']}"

        for estadistica
        in estadisticas_mensuales
    ]


    inspecciones_grafico = [

        estadistica["inspecciones"]

        for estadistica
        in estadisticas_mensuales
    ]


    novedades_grafico = [

        estadistica["novedades"]

        for estadistica
        in estadisticas_mensuales
    ]


    mantenimientos_grafico = [

        estadistica["mantenimientos"]

        for estadistica
        in estadisticas_mensuales
    ]


    # ==========================================================
    # ÚLTIMAS INSPECCIONES
    # ==========================================================

    ultimas_inspecciones = (
        inspecciones
        .select_related(
            "institucion",
            "servicio",
            "biomedico",
        )
        .prefetch_related(
            "detalles__equipo"
        )
        .annotate(
            novedades_total=Count(
                "detalles",
                filter=(
                    Q(
                        detalles__estado=
                        DetalleInspeccion.EstadoEquipo.OBSERVACION
                    )
                    |
                    Q(
                        detalles__estado=
                        DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO
                    )
                    |
                    ~Q(
                        detalles__observaciones=""
                    )
                    |
                    Q(
                        detalles__resultados__cumple=False
                    )
                ),
                distinct=True,
            )
        )
        .order_by(
            "-fecha",
            "-hora_inicio",
        )[:10]
    )


    # ==========================================================
    # ÚLTIMOS MANTENIMIENTOS
    # ==========================================================

    ultimos_mantenimientos = (
        mantenimientos
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "ingeniero",
        )
        .order_by(
            "-fecha_programada",
            "-id",
        )[:10]
    )


    # ==========================================================
    # EQUIPOS CON MANTENIMIENTO PENDIENTE
    # ==========================================================

    equipos_mantenimiento = (
        mantenimientos
        .filter(
            estado__in=[
                Mantenimiento.Estado.PROGRAMADO,
                Mantenimiento.Estado.EN_PROCESO,
            ]
        )
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
        )
        .order_by(
            "fecha_programada"
        )[:10]
    )


    # ==========================================================
    # CONTEXTO
    # ==========================================================

    context = {

        # ------------------------------------------------------
        # FECHA
        # ------------------------------------------------------

        "hoy":
            hoy,

        "mes_actual_nombre":
            mes_actual_nombre,

        "año_actual":
            año_actual,


        # ------------------------------------------------------
        # INDICADORES GENERALES
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
        # INDICADORES DEL MES
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
        # ESTADÍSTICAS 6 MESES
        # ------------------------------------------------------

        "estadisticas_mensuales":
            estadisticas_mensuales,

        "total_inspecciones_6_meses":
            total_inspecciones_6_meses,

        "total_novedades_6_meses":
            total_novedades_6_meses,

        "total_mantenimientos_6_meses":
            total_mantenimientos_6_meses,


        # ------------------------------------------------------
        # CHART.JS
        # ------------------------------------------------------

        "etiquetas_grafico":
            etiquetas_grafico,

        "inspecciones_grafico":
            inspecciones_grafico,

        "novedades_grafico":
            novedades_grafico,

        "mantenimientos_grafico":
            mantenimientos_grafico,


        # ------------------------------------------------------
        # ÚLTIMOS REGISTROS
        # ------------------------------------------------------

        "ultimas_inspecciones":
            ultimas_inspecciones,

        "ultimos_mantenimientos":
            ultimos_mantenimientos,

        "equipos_mantenimiento":
            equipos_mantenimiento,
    }


    # ==========================================================
    # RENDER
    # ==========================================================

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