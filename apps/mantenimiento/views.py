from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from apps import mantenimiento
from apps.usuarios.decorators import rol_requerido

from .forms import MantenimientoForm, OrdenTrabajoForm
from .models import Mantenimiento, OrdenTrabajo, MantenimientoActividad

from datetime import timedelta

from django.db.models import Count
from django.utils import json, timezone
from io import BytesIO
from apps.servicios.models import Servicio
from apps.hojas_vida.models import HojaVida
from apps.catalogo.models import GuiaMantenimiento
from django.http import HttpResponse, JsonResponse, request
from apps.catalogo.models import GuiaMantenimiento, ActividadMantenimiento
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from apps.hojas_vida.models import HojaVida

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from xml.sax.saxutils import escape
import calendar
from datetime import date
def sumar_meses(fecha, meses):
    """
    Suma una cantidad de meses a una fecha,
    conservando el día cuando sea posible.

    Ejemplo:
    31/01/2026 + 1 mes = 28/02/2026
    """

    mes = fecha.month - 1 + meses

    anio = fecha.year + mes // 12

    mes = mes % 12 + 1

    dia = min(
        fecha.day,
        calendar.monthrange(anio, mes)[1]
    )

    return date(
        anio,
        mes,
        dia
    )

def programar_siguiente_mantenimiento(mantenimiento):
    """
    Programa automáticamente el siguiente mantenimiento
    cuando el mantenimiento actual queda FINALIZADO.

    La frecuencia se obtiene del catálogo asociado al equipo.
    """

    # ---------------------------------------------------------
    # SOLO SE PROGRAMA SI ESTÁ FINALIZADO
    # ---------------------------------------------------------

    if mantenimiento.estado != Mantenimiento.Estado.FINALIZADO:
        return None

    with transaction.atomic():

        # -----------------------------------------------------
        # BLOQUEAR ÚNICAMENTE EL REGISTRO DE MANTENIMIENTO
        # -----------------------------------------------------

        mantenimiento = (
            Mantenimiento.objects
            .select_for_update()
            .get(pk=mantenimiento.pk)
        )

        # -----------------------------------------------------
        # VERIFICAR SI YA EXISTE EL SIGUIENTE
        # -----------------------------------------------------

        siguiente_existente = (
            Mantenimiento.objects
            .filter(
                mantenimiento_anterior=mantenimiento
            )
            .order_by("-id")
            .first()
        )

        if siguiente_existente:
            return siguiente_existente

        # -----------------------------------------------------
        # OBTENER EQUIPO Y CATÁLOGO
        # -----------------------------------------------------

        equipo = mantenimiento.hoja_vida.equipo

        catalogo = equipo.catalogo

        if not catalogo:
            return None

        # -----------------------------------------------------
        # VERIFICAR SI REQUIERE MANTENIMIENTO
        # -----------------------------------------------------

        if not catalogo.requiere_mantenimiento:
            return None

        frecuencia = catalogo.frecuencia_mantenimiento

        if not frecuencia or frecuencia <= 0:
            return None

        # -----------------------------------------------------
        # FECHA BASE
        # -----------------------------------------------------

        fecha_base = (
            mantenimiento.fecha_fin
            or mantenimiento.fecha_programada
        )

        # -----------------------------------------------------
        # CALCULAR FECHA DEL PRÓXIMO MANTENIMIENTO
        # -----------------------------------------------------

        fecha_siguiente = sumar_meses(
            fecha_base,
            frecuencia
        )

        # -----------------------------------------------------
        # CREAR SIGUIENTE MANTENIMIENTO
        # -----------------------------------------------------

        siguiente = Mantenimiento.objects.create(

            hoja_vida=mantenimiento.hoja_vida,

            tipo=Mantenimiento.Tipo.PREVENTIVO,

            estado=Mantenimiento.Estado.PROGRAMADO,

            fecha_programada=fecha_siguiente,

            descripcion=(
                "Mantenimiento preventivo programado "
                "automáticamente después del mantenimiento "
                f"#{mantenimiento.id}."
            ),

            mantenimiento_anterior=mantenimiento,
        )

        # -----------------------------------------------------
        # CARGAR ACTIVIDADES DE LA GUÍA
        # -----------------------------------------------------

        guia = GuiaMantenimiento.objects.filter(
            catalogo=catalogo,
            activa=True,
        ).first()

        if guia:

            actividades = list(
                guia.actividades.order_by(
                    "orden",
                    "id"
                )
            )

            MantenimientoActividad.objects.bulk_create(
                [
                    MantenimientoActividad(
                        mantenimiento=siguiente,
                        actividad=actividad,
                        realizada=False,
                        observacion="",
                    )
                    for actividad in actividades
                ]
            )

        return siguiente

def guardar_actividades_mantenimiento(mantenimiento, request):
    """
    Guarda las actividades ejecutadas de un mantenimiento.

    También valida que todas las actividades obligatorias
    de la guía hayan sido realizadas.

    Retorna:
        (True, None) si todo está correcto.
        (False, mensaje_error) si existe algún problema.
    """

    hoja_vida = mantenimiento.hoja_vida
    equipo = hoja_vida.equipo
    catalogo = equipo.catalogo

    # ---------------------------------------------------------
    # Si el equipo no tiene catálogo, no hay actividades
    # que validar.
    # ---------------------------------------------------------

    if not catalogo:
        MantenimientoActividad.objects.filter(
            mantenimiento=mantenimiento
        ).delete()

        return True, None


    # ---------------------------------------------------------
    # Buscar guía activa
    # ---------------------------------------------------------

    guia = GuiaMantenimiento.objects.filter(
        catalogo=catalogo,
        activa=True,
    ).first()


    # ---------------------------------------------------------
    # Si no existe guía, simplemente no hay actividades
    # ---------------------------------------------------------

    if not guia:
        MantenimientoActividad.objects.filter(
            mantenimiento=mantenimiento
        ).delete()

        return True, None


    # ---------------------------------------------------------
    # Actividades válidas de esta guía
    # ---------------------------------------------------------

    actividades_guia = list(
        guia.actividades.order_by("orden", "id")
    )

    actividades_ids_validos = {
        actividad.id
        for actividad in actividades_guia
    }


    # ---------------------------------------------------------
    # Actividades marcadas por el usuario
    #
    # El JavaScript envía:
    #
    # actividad = 1
    # actividad = 4
    # actividad = 7
    # ---------------------------------------------------------

    actividades_seleccionadas = request.POST.getlist(
        "actividad"
    )


    try:
        actividades_seleccionadas = {
            int(pk)
            for pk in actividades_seleccionadas
        }

    except (TypeError, ValueError):

        return False, (
            "Se encontraron actividades inválidas "
            "en el formulario."
        )


    # ---------------------------------------------------------
    # Seguridad:
    # evitar que alguien envíe manualmente una actividad
    # perteneciente a otra guía.
    # ---------------------------------------------------------

    actividades_fuera_de_guia = (
        actividades_seleccionadas -
        actividades_ids_validos
    )

    if actividades_fuera_de_guia:

        return False, (
            "Una o más actividades seleccionadas "
            "no pertenecen a la guía de mantenimiento "
            "del equipo."
        )


    # ---------------------------------------------------------
    # VALIDAR ACTIVIDADES OBLIGATORIAS
    # ---------------------------------------------------------

    actividades_obligatorias = {
        actividad.id
        for actividad in actividades_guia
        if actividad.obligatorio
    }


    faltantes = (
        actividades_obligatorias -
        actividades_seleccionadas
    )


    if faltantes:

        actividades_faltantes = [
            actividad.descripcion
            for actividad in actividades_guia
            if actividad.id in faltantes
        ]

        mensaje = (
            "Debe completar todas las actividades obligatorias: "
            + ", ".join(actividades_faltantes)
        )

        return False, mensaje


    # ---------------------------------------------------------
    # GUARDAR ACTIVIDADES
    #
    # Primero eliminamos las anteriores y reconstruimos
    # el estado actual del mantenimiento.
    # ---------------------------------------------------------

    MantenimientoActividad.objects.filter(
        mantenimiento=mantenimiento
    ).delete()


    registros = []

    for actividad in actividades_guia:

        realizada = (
            actividad.id in actividades_seleccionadas
        )

        observacion = request.POST.get(
            f"observacion_actividad_{actividad.id}",
            ""
        ).strip()


        registros.append(
            MantenimientoActividad(
                mantenimiento=mantenimiento,
                actividad=actividad,
                realizada=realizada,
                observacion=observacion,
            )
        )


    if registros:
        MantenimientoActividad.objects.bulk_create(
            registros
        )


    # ---------------------------------------------------------
    # MANTENER COMPATIBILIDAD CON EL CAMPO ANTIGUO
    #
    # Esto permite que el PDF de las Órdenes de Trabajo
    # continúe mostrando las actividades realizadas.
    # ---------------------------------------------------------

    actividades_realizadas_texto = []

    for actividad in actividades_guia:

        if actividad.id in actividades_seleccionadas:

            observacion = request.POST.get(
                f"observacion_actividad_{actividad.id}",
                ""
            ).strip()

            texto = f"✓ {actividad.descripcion}"

            if observacion:
                texto += f" — {observacion}"

            actividades_realizadas_texto.append(
                texto
            )


    mantenimiento.actividades_realizadas = "\n".join(
        actividades_realizadas_texto
    )

    mantenimiento.save(
        update_fields=[
            "actividades_realizadas",
            "actualizado",
        ]
    )


    return True, None


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

    # ==========================================================
    # FILTRO POR INSTITUCIÓN
    # ==========================================================

    if request.user.es_admin or request.user.es_biomedico:

        mantenimientos = mantenimientos.filter(
            hoja_vida__equipo__institucion=request.user.institucion
        )

    # ==========================================================
    # FILTRO POR MES Y AÑO
    # ==========================================================

    mes = request.GET.get("mes")
    anio = request.GET.get("anio")

    if mes and anio:

        try:

            mes = int(mes)
            anio = int(anio)

            if 1 <= mes <= 12:

                mantenimientos = mantenimientos.filter(
                    fecha_programada__year=anio,
                    fecha_programada__month=mes,
                )

        except (ValueError, TypeError):

            pass

    # ==========================================================
    # FILTRO POR ESTADO
    # ==========================================================

    estado = request.GET.get("estado")

    estados_validos = [
        Mantenimiento.Estado.PROGRAMADO,
        Mantenimiento.Estado.EN_PROCESO,
        Mantenimiento.Estado.FINALIZADO,
    ]

    if estado in estados_validos:

        mantenimientos = mantenimientos.filter(
            estado=estado
        )

    # ==========================================================
    # FECHAS
    # ==========================================================

    hoy = timezone.localdate()

    proximos_30 = hoy + timedelta(days=30)

    # ==========================================================
    # CONTEXTO
    # ==========================================================

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

        # Filtros activos
        "mes_filtro": mes,
        "anio_filtro": anio,
        "estado_filtro": estado,

    }

    return render(
        request,
        "mantenimiento/index.html",
        context,
    )
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def equipos_por_servicio(request):

    servicio_id = request.GET.get("servicio")

    if not servicio_id:
        return JsonResponse(
            {
                "equipos": []
            }
        )

    servicio = get_object_or_404(
        Servicio.objects.select_related("institucion"),
        id=servicio_id,
    )

    # ==========================================================
    # SEGURIDAD POR INSTITUCIÓN
    # ==========================================================

    if request.user.es_admin:

        if servicio.institucion != request.user.institucion:

            return JsonResponse(
                {
                    "error": "No tiene permisos para consultar este servicio."
                },
                status=403,
            )

    hojas_vida = (
        HojaVida.objects
        .filter(
            equipo__servicio=servicio,
            equipo__institucion=servicio.institucion,
        )
        .select_related(
            "equipo",
            "equipo__catalogo",
        )
        .order_by(
            "equipo__nombre",
            "equipo__serie",
        )
    )

    equipos = []

    for hoja in hojas_vida:

        equipo = hoja.equipo

        equipos.append(
            {
                "id": hoja.id,
                "nombre": equipo.nombre,
                "serie": equipo.serie or "Sin serial",
                "codigo": equipo.codigo or "Sin código",
                "marca": equipo.marca or "",
                "modelo": equipo.modelo or "",
                "catalogo_id": (
                    equipo.catalogo_id
                    if equipo.catalogo
                    else None
                ),
            }
        )

    return JsonResponse(
        {
            "equipos": equipos
        }
    )
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def guia_por_equipo(request):

    hoja_id = request.GET.get("hoja")

    if not hoja_id:
        return JsonResponse({
            "guia": None,
            "actividades": [],
        })

    hoja_vida = get_object_or_404(
        HojaVida.objects.select_related(
            "equipo",
            "equipo__catalogo",
            "equipo__servicio",
            "equipo__institucion",
        ),
        id=hoja_id,
    )

    equipo = hoja_vida.equipo

    if request.user.es_admin:

        if equipo.institucion != request.user.institucion:

            return JsonResponse(
                {
                    "error": (
                        "No tiene permisos para consultar "
                        "este equipo."
                    )
                },
                status=403,
            )

    catalogo = equipo.catalogo

    if not catalogo:

        return JsonResponse({
            "guia": None,
            "actividades": [],
            "mensaje": (
                "El equipo no tiene un catálogo asociado."
            ),
        })

    guia = GuiaMantenimiento.objects.filter(
        catalogo=catalogo,
        activa=True,
    ).first()

    if not guia:

        return JsonResponse({
            "guia": None,
            "actividades": [],
            "mensaje": (
                "Este catálogo no tiene una guía de "
                "mantenimiento activa."
            ),
            "frecuencia": catalogo.frecuencia_mantenimiento,
        })

    actividades = (
        guia.actividades
        .order_by("orden", "id")
    )

    datos_actividades = []

    for actividad in actividades:

        datos_actividades.append({
            "id": actividad.id,
            "descripcion": actividad.descripcion,
            "obligatorio": actividad.obligatorio,
            "orden": actividad.orden,
        })

    return JsonResponse({
        "guia": {
            "id": guia.id,
            "nombre": guia.nombre,
            "activa": guia.activa,
        },
        "actividades": datos_actividades,
        "frecuencia": catalogo.frecuencia_mantenimiento,
    })
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
            request.FILES
        )

        if form.is_valid():

            try:

                with transaction.atomic():

                    mantenimiento = form.save()

                    # -----------------------------------------
                    # GUARDAR Y VALIDAR ACTIVIDADES
                    # -----------------------------------------

                    actividades_ok, error = (
                        guardar_actividades_mantenimiento(
                            mantenimiento,
                            request
                        )
                    )


                    if not actividades_ok:

                        raise ValueError(error)
                    
                    siguiente = None

                    programar_siguiente = (
                        request.POST.get("programar_siguiente") == "si"
                    )

                    if (
                        programar_siguiente
                        and mantenimiento.tipo == Mantenimiento.Tipo.PREVENTIVO
                        and mantenimiento.estado == Mantenimiento.Estado.FINALIZADO
                    ):

                        siguiente = programar_siguiente_mantenimiento(
                            mantenimiento
                        )

                    if siguiente:

                        messages.success(
                            request,
                            (
                                "Mantenimiento registrado correctamente. "
                                f"El próximo mantenimiento quedó programado "
                                f"para el {siguiente.fecha_programada.strftime('%d/%m/%Y')}."
                            )
                        )

                    else:

                        messages.success(
                            request,
                            "Mantenimiento registrado correctamente."
                        )


            except ValueError as error:

                form.add_error(
                    None,
                    str(error)
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
            "actividades_guardadas": [],
        },
    )

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_mantenimiento(request, id):

    mantenimiento = get_object_or_404(
        Mantenimiento.objects.select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "hoja_vida__equipo__institucion",
            "hoja_vida__equipo__servicio",
            "hoja_vida__equipo__catalogo",
        ),
        id=id,
    )
    actividades_guardadas = list(
        mantenimiento.actividades.values_list(
            "actividad_id",
            flat=True
        )
    )


    # ---------------------------------------------------------
    # SEGURIDAD POR INSTITUCIÓN
    # ---------------------------------------------------------

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


    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    if request.method == "POST":

        form = MantenimientoForm(
            request.POST,
            request.FILES,
            instance=mantenimiento
        )


        if form.is_valid():

            try:

                with transaction.atomic():

                    mantenimiento = form.save()


                    # -----------------------------------------
                    # GUARDAR ACTIVIDADES
                    # -----------------------------------------

                    actividades_ok, error = (
                        guardar_actividades_mantenimiento(
                            mantenimiento,
                            request
                        )
                    )


                    if not actividades_ok:

                        raise ValueError(error)
                    # -----------------------------------------
                    # PROGRAMAR SIGUIENTE SOLO SI EL USUARIO
                    # LO SOLICITÓ
                    # -----------------------------------------

                    siguiente = None

                    programar_siguiente = (
                        request.POST.get("programar_siguiente") == "si"
                    )

                    if (
                        programar_siguiente
                        and mantenimiento.tipo == Mantenimiento.Tipo.PREVENTIVO
                        and mantenimiento.estado == Mantenimiento.Estado.FINALIZADO
                    ):
                        
                        siguiente = programar_siguiente_mantenimiento(
                            mantenimiento
                        )

                if siguiente:

                    messages.success(
                        request,
                        (
                            "Mantenimiento actualizado correctamente. "
                            f"El próximo mantenimiento quedó programado "
                            f"para el {siguiente.fecha_programada.strftime('%d/%m/%Y')}."
                        )
                    )

                else:

                    messages.success(
                        request,
                        "Mantenimiento actualizado correctamente."
                    )

                return redirect(
                    "detalle_mantenimiento",
                    mantenimiento.id
                )


            except ValueError as error:

                form.add_error(
                    None,
                    str(error)
                )


    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    else:

        form = MantenimientoForm(
            instance=mantenimiento
        )

    actividades_guardadas = list(
        mantenimiento.actividades.values_list(
            "actividad_id",
            flat=True
        )
    )
    return render(
        request,
        "mantenimiento/form.html",
        {
            "form": form,
            "titulo": "Editar mantenimiento",
            "editar": True,
            "mantenimiento": mantenimiento,
            "actividades_guardadas": actividades_guardadas,
        },
    )

# ==========================================================
# DETALLE
# ==========================================================
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
            "hoja_vida__equipo__institucion",
            "hoja_vida__equipo__servicio",
            "hoja_vida__equipo__catalogo",
            "ingeniero",
            "orden_trabajo",
        ),
        id=id,
    )

    # ---------------------------------------------------------
    # SEGURIDAD POR INSTITUCIÓN
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # MANTENIMIENTO ANTERIOR
    # ---------------------------------------------------------

    mantenimiento_anterior = (
        mantenimiento.mantenimiento_anterior
    )

    # ---------------------------------------------------------
    # PRÓXIMO MANTENIMIENTO
    # ---------------------------------------------------------

    proximo_mantenimiento = (
        mantenimiento.mantenimiento_siguiente
        .order_by("-id")
        .first()
    )

    # ---------------------------------------------------------
    # ACTIVIDADES
    # ---------------------------------------------------------

    actividades = (
        mantenimiento.actividades
        .select_related("actividad")
        .order_by(
            "actividad__orden",
            "actividad__id"
        )
    )

    # ---------------------------------------------------------
    # DETERMINAR DE DÓNDE VIENE
    # ---------------------------------------------------------

    volver_a_ordenes = (
        mantenimiento.orden_trabajo is not None
        and request.GET.get("origen") == "orden"
    )

    return render(
        request,
        "mantenimiento/detalle.html",
        {
            "mantenimiento": mantenimiento,
            "mantenimiento_anterior": mantenimiento_anterior,
            "proximo_mantenimiento": proximo_mantenimiento,
            "actividades": actividades,
            "volver_a_ordenes": volver_a_ordenes,
        },
    )
# ==========================================================
# ORDENES DE TRABAJO
# ==========================================================


@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def lista_ordenes_trabajo(request):
    """
    Lista las órdenes de trabajo.
    """

    ordenes = (
        OrdenTrabajo.objects
        .select_related(
            "servicio",
            "servicio__institucion",
            "ingeniero",
        )
        .prefetch_related(
            "mantenimientos",
            "mantenimientos__hoja_vida",
            "mantenimientos__hoja_vida__equipo",
        )
        .order_by(
            "-fecha",
            "-id",
        )
    )

    # ======================================================
    # FILTRO POR INSTITUCIÓN
    # ======================================================

    if request.user.es_admin or request.user.es_biomedico:

        ordenes = ordenes.filter(
            servicio__institucion=request.user.institucion
        )

    return render(
        request,
        "mantenimiento/ordenes.html",
        {
            "ordenes": ordenes,
        },
    )


# ==========================================================
# CREAR ORDEN DE TRABAJO
# ==========================================================


@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_orden_trabajo(request):
    """
    Crea una Orden de Trabajo general.

    La orden inicialmente se crea sin equipos.
    Posteriormente se podrán agregar varios mantenimientos.
    """

    if request.method == "POST":

        form = OrdenTrabajoForm(
            request.POST
        )

        if form.is_valid():

            orden = form.save()

            messages.success(
                request,
                "Orden de Trabajo creada correctamente."
            )

            return redirect(
                "detalle_orden_trabajo",
                orden.id,
            )

    else:

        form = OrdenTrabajoForm(
            initial={
                "fecha": timezone.localdate(),
            }
        )

    return render(
        request,
        "mantenimiento/orden_form.html",
        {
            "form": form,
            "titulo": "Nueva Orden de Trabajo",
        },
    )


# ==========================================================
# DETALLE ORDEN DE TRABAJO
# ==========================================================


@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def detalle_orden_trabajo(request, id):
    """
    Muestra una Orden de Trabajo y todos los equipos
    incluidos en ella.
    """

    orden = get_object_or_404(
        OrdenTrabajo.objects
        .select_related(
            "servicio",
            "servicio__institucion",
            "ingeniero",
        )
        .prefetch_related(
            "mantenimientos",
            "mantenimientos__hoja_vida",
            "mantenimientos__hoja_vida__equipo",
            "mantenimientos__hoja_vida__equipo__institucion",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD POR INSTITUCIÓN
    # ======================================================

    if request.user.es_admin or request.user.es_biomedico:

        if orden.servicio.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos para visualizar esta "
                "Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )

    mantenimientos = (
        orden.mantenimientos
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "ingeniero",
        )
        .order_by(
            "id"
        )
    )

    return render(
        request,
        "mantenimiento/orden_detalle.html",
        {
            "orden": orden,
            "mantenimientos": mantenimientos,
        },
    )


# ==========================================================
# EDITAR ORDEN DE TRABAJO
# ==========================================================


@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_orden_trabajo(request, id):
    """
    Edita la información general de una Orden de Trabajo.
    """

    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related(
            "servicio",
            "servicio__institucion",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD
    # ======================================================

    if request.user.es_admin:

        if (
            orden.servicio.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para editar esta "
                "Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )

    # ======================================================
    # FORMULARIO
    # ======================================================

    if request.method == "POST":

        form = OrdenTrabajoForm(
            request.POST,
            instance=orden,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Orden de Trabajo actualizada correctamente."
            )

            return redirect(
                "detalle_orden_trabajo",
                orden.id,
            )

    else:

        form = OrdenTrabajoForm(
            instance=orden,
        )

    return render(
        request,
        "mantenimiento/orden_form.html",
        {
            "form": form,
            "titulo": "Editar Orden de Trabajo",
            "orden": orden,
            "editar": True,
        },
    )


# ==========================================================
# AGREGAR MANTENIMIENTO A UNA ORDEN
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def agregar_mantenimiento_orden(request, id):

    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related(
            "servicio",
            "servicio__institucion"
        ),
        id=id,
    )


    if request.user.es_admin:

        if (
            orden.servicio.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para modificar esta Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )


    if request.method == "POST":

        form = MantenimientoForm(
            request.POST,
            request.FILES,
            orden_trabajo=orden
        )


        if form.is_valid():

            try:

                with transaction.atomic():

                    mantenimiento = form.save(
                        commit=False
                    )

                    mantenimiento.orden_trabajo = orden

                    mantenimiento.save()


                    actividades_ok, error = (
                        guardar_actividades_mantenimiento(
                            mantenimiento,
                            request
                        )
                    )


                    if not actividades_ok:

                        raise ValueError(error)
                    
                    siguiente = programar_siguiente_mantenimiento(
                        mantenimiento
                    )

                if siguiente:

                    messages.success(
                        request,
                        (
                            "Equipo agregado correctamente a la Orden de Trabajo. "
                            f"El próximo mantenimiento quedó programado "
                            f"para el {siguiente.fecha_programada.strftime('%d/%m/%Y')}."
                        )
                    )

                else:

                    messages.success(
                        request,
                        "Equipo agregado correctamente a la Orden de Trabajo."
                    )

                return redirect(
                    "detalle_orden_trabajo",
                    orden.id
                )


            except ValueError as error:

                form.add_error(
                    None,
                    str(error)
                )


    else:

        form = MantenimientoForm(
            initial={
                "fecha_programada": orden.fecha,
                "ingeniero": orden.ingeniero,
                "empresa": orden.empresa,
            },
            orden_trabajo=orden,
        )


    return render(
        request,
        "mantenimiento/form.html",
        {
            "form": form,
            "titulo": f"Agregar equipo a la OT {orden.numero}",
            "orden": orden,
            "actividades_guardadas": [],
        },
    )

# ==========================================================
# QUITAR MANTENIMIENTO DE UNA ORDEN
# ==========================================================


@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def quitar_mantenimiento_orden(request, id, mantenimiento_id):
    """
    Retira un mantenimiento de una Orden de Trabajo.

    NO elimina el mantenimiento.
    Simplemente lo deja nuevamente independiente.
    """

    orden = get_object_or_404(
        OrdenTrabajo,
        id=id,
    )

    mantenimiento = get_object_or_404(
        Mantenimiento,
        id=mantenimiento_id,
        orden_trabajo=orden,
    )

    # ======================================================
    # SEGURIDAD
    # ======================================================

    if request.user.es_admin:

        if (
            orden.servicio.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para modificar esta "
                "Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )

    # ======================================================
    # DESVINCULAR
    # ======================================================

    mantenimiento.orden_trabajo = None
    mantenimiento.save(
        update_fields=[
            "orden_trabajo",
            "actualizado",
        ]
    )

    messages.success(
        request,
        "El equipo fue retirado de la Orden de Trabajo."
    )

    return redirect(
        "detalle_orden_trabajo",
        orden.id,
    )
# ==========================================================
# FIRMAR ORDEN DE TRABAJO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def firmar_orden_trabajo(request, id):
    """
    Permite registrar las firmas de una Orden de Trabajo.

    La firma se realiza una sola vez por cada responsable
    y queda almacenada en la Orden de Trabajo.

    Las firmas también se copian automáticamente a todos
    los mantenimientos/equipos pertenecientes a la orden.
    """

    orden = get_object_or_404(
        OrdenTrabajo.objects
        .select_related(
            "servicio",
            "servicio__institucion",
            "ingeniero",
        )
        .prefetch_related(
            "mantenimientos",
            "mantenimientos__hoja_vida",
            "mantenimientos__hoja_vida__equipo",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD POR INSTITUCIÓN
    # ======================================================

    if request.user.es_admin or request.user.es_biomedico:

        if orden.servicio.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos para firmar esta "
                "Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )

    # ======================================================
    # PROCESAR FIRMAS
    # ======================================================

    if request.method == "POST":

        firma_biomedico = request.POST.get(
            "firma_biomedico",
            ""
        ).strip()

        firma_responsable = request.POST.get(
            "firma_responsable",
            ""
        ).strip()

        responsable_nombre = request.POST.get(
            "responsable_nombre",
            ""
        ).strip()

        responsable_cargo = request.POST.get(
            "responsable_cargo",
            ""
        ).strip()

        # ==============================================
        # VALIDAR FIRMA BIOMÉDICO
        # ==============================================

        if not firma_biomedico:

            messages.error(
                request,
                "Debe registrar la firma del biomédico."
            )

            return redirect(
                "firmar_orden_trabajo",
                orden.id,
            )

        # ==============================================
        # VALIDAR FIRMA RESPONSABLE
        # ==============================================

        if not firma_responsable:

            messages.error(
                request,
                "Debe registrar la firma del responsable "
                "del servicio."
            )

            return redirect(
                "firmar_orden_trabajo",
                orden.id,
            )

        # ==============================================
        # VALIDAR NOMBRE RESPONSABLE
        # ==============================================

        if not responsable_nombre:

            messages.error(
                request,
                "Debe ingresar el nombre del responsable."
            )

            return redirect(
                "firmar_orden_trabajo",
                orden.id,
            )

        # ==============================================
        # GUARDAR ORDEN Y FIRMAS EN LOS MANTENIMIENTOS
        # ==============================================

        from django.db import transaction

        with transaction.atomic():

            # ------------------------------------------
            # GUARDAR FIRMAS EN LA ORDEN
            # ------------------------------------------

            orden.firma_biomedico = firma_biomedico

            orden.firma_responsable = firma_responsable

            orden.responsable_nombre = responsable_nombre

            orden.responsable_cargo = responsable_cargo

            orden.save(
                update_fields=[
                    "firma_biomedico",
                    "firma_responsable",
                    "responsable_nombre",
                    "responsable_cargo",
                    "actualizado",
                ]
            )

            # ------------------------------------------
            # COPIAR FIRMAS A CADA MANTENIMIENTO
            # ------------------------------------------

            mantenimientos = orden.mantenimientos.all()

            for mantenimiento in mantenimientos:

                mantenimiento.firma_biomedico = (
                    firma_biomedico
                )

                mantenimiento.firma_responsable = (
                    firma_responsable
                )

                mantenimiento.save(
                    update_fields=[
                        "firma_biomedico",
                        "firma_responsable",
                        "actualizado",
                    ]
                )

        messages.success(
            request,
            "Firmas registradas correctamente. "
            "Las firmas fueron aplicadas a todos los "
            "equipos de la Orden de Trabajo."
        )

        # ==============================================
        # REGRESAR A LA ORDEN
        # ==============================================

        return redirect(
            "detalle_orden_trabajo",
            orden.id,
        )

    # ======================================================
    # MOSTRAR FORMULARIO
    # ======================================================

    return render(
        request,
        "mantenimiento/orden_firmar.html",
        {
            "orden": orden,
        },
    )
# ==========================================================
# PDF ORDEN DE TRABAJO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def pdf_orden_trabajo(request, id):
    """
    Genera el PDF completo de una Orden de Trabajo.

    La OT puede contener varios equipos/mantenimientos.
    Las firmas aparecen una sola vez al final.
    """

    orden = get_object_or_404(
        OrdenTrabajo.objects
        .select_related(
            "servicio",
            "servicio__institucion",
            "ingeniero",
        )
        .prefetch_related(
            "mantenimientos",
            "mantenimientos__hoja_vida",
            "mantenimientos__hoja_vida__equipo",
            "mantenimientos__hoja_vida__equipo__institucion",
            "mantenimientos__hoja_vida__equipo__servicio",
            "mantenimientos__ingeniero",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD POR INSTITUCIÓN
    # ======================================================

    if request.user.es_admin or request.user.es_biomedico:

        if orden.servicio.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos para generar el PDF "
                "de esta Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )

    # ======================================================
    # MANTENIMIENTOS
    # ======================================================

    mantenimientos = (
        orden.mantenimientos
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "hoja_vida__equipo__institucion",
            "hoja_vida__equipo__servicio",
            "ingeniero",
        )
        .order_by("id")
    )

    # ======================================================
    # CREAR PDF EN MEMORIA
    # ======================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Orden de Trabajo {orden.numero}",
        author="SIGHI",
    )

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloOT",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    subtitulo = ParagraphStyle(
        "SubtituloOT",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=15,
    )

    encabezado = ParagraphStyle(
        "Encabezado",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.white,
    )

    normal = ParagraphStyle(
        "NormalOT",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    pequeno = ParagraphStyle(
        "PequenoOT",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    firma = ParagraphStyle(
        "FirmaOT",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
    )

    elementos = []

    # ======================================================
    # ENCABEZADO
    # ======================================================

    institucion = orden.servicio.institucion

    elementos.append(
        Paragraph(
            "ORDEN DE TRABAJO",
            titulo,
        )
    )

    elementos.append(
        Paragraph(
            "SIGHI - Sistema de Gestión Hospitalaria",
            subtitulo,
        )
    )

    # ======================================================
    # INFORMACIÓN GENERAL
    # ======================================================

    datos_generales = [
        [
            Paragraph("<b>Número de OT</b>", normal),
            Paragraph(str(orden.numero), normal),
            Paragraph("<b>Fecha</b>", normal),
            Paragraph(
                orden.fecha.strftime("%d/%m/%Y"),
                normal,
            ),
        ],
        [
            Paragraph("<b>Institución</b>", normal),
            Paragraph(
                str(institucion),
                normal,
            ),
            Paragraph("<b>Servicio</b>", normal),
            Paragraph(
                str(orden.servicio),
                normal,
            ),
        ],
        [
            Paragraph("<b>Ingeniero / Biomédico</b>", normal),
            Paragraph(
                str(orden.ingeniero)
                if orden.ingeniero
                else "No asignado",
                normal,
            ),
            Paragraph("<b>Empresa</b>", normal),
            Paragraph(
                orden.empresa or "No registra",
                normal,
            ),
        ],
    ]

    tabla_general = Table(
        datos_generales,
        colWidths=[
            3.3 * cm,
            6.2 * cm,
            3.3 * cm,
            5.0 * cm,
        ],
    )

    tabla_general.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E9ECEF"),
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    colors.HexColor("#E9ECEF"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    elementos.append(tabla_general)
    elementos.append(Spacer(1, 0.4 * cm))

    # ======================================================
    # DESCRIPCIÓN GENERAL
    # ======================================================

    elementos.append(
        Table(
            [
                [
                    Paragraph(
                        "DESCRIPCIÓN GENERAL",
                        encabezado,
                    )
                ]
            ],
            colWidths=[17.8 * cm],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#198754"),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            ),
        )
    )

    elementos.append(
        Spacer(1, 0.15 * cm)
    )

    elementos.append(
        Paragraph(
            orden.descripcion or "No registra.",
            normal,
        )
    )

    elementos.append(
        Spacer(1, 0.5 * cm)
    )

    # ======================================================
    # EQUIPOS / MANTENIMIENTOS
    # ======================================================

    elementos.append(
        Table(
            [
                [
                    Paragraph(
                        "EQUIPOS Y MANTENIMIENTOS",
                        encabezado,
                    )
                ]
            ],
            colWidths=[17.8 * cm],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#0D6EFD"),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            ),
        )
    )

    elementos.append(
        Spacer(1, 0.2 * cm)
    )

    # ======================================================
    # CADA EQUIPO
    # ======================================================

    for numero, mantenimiento in enumerate(
        mantenimientos,
        start=1,
    ):

        equipo = mantenimiento.hoja_vida.equipo

        datos_equipo = [
            [
                Paragraph(
                    f"<b>EQUIPO {numero}</b>",
                    normal,
                ),
                "",
            ],
            [
                Paragraph("<b>Equipo</b>", normal),
                Paragraph(
                    str(equipo.nombre),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Código</b>", normal),
                Paragraph(
                    str(equipo.codigo or "No registra"),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Marca</b>", normal),
                Paragraph(
                    str(equipo.marca or "No registra"),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Modelo</b>", normal),
                Paragraph(
                    str(equipo.modelo or "No registra"),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Tipo</b>", normal),
                Paragraph(
                    mantenimiento.get_tipo_display(),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Estado</b>", normal),
                Paragraph(
                    mantenimiento.get_estado_display(),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Fecha programada</b>", normal),
                Paragraph(
                    mantenimiento.fecha_programada.strftime(
                        "%d/%m/%Y"
                    ),
                    normal,
                ),
            ],
            [
                Paragraph("<b>Descripción</b>", normal),
                Paragraph(
                    mantenimiento.descripcion
                    or "No registra.",
                    normal,
                ),
            ],
            [
                Paragraph("<b>Actividades realizadas</b>", normal),
                Paragraph(
                    mantenimiento.actividades_realizadas
                    or "No registra.",
                    normal,
                ),
            ],
            [
                Paragraph("<b>Repuestos</b>", normal),
                Paragraph(
                    mantenimiento.repuestos
                    or "No registra.",
                    normal,
                ),
            ],
            [
                Paragraph("<b>Costo</b>", normal),
                Paragraph(
                    f"$ {mantenimiento.costo:,.2f}",
                    normal,
                ),
            ],
            [
                Paragraph("<b>Observaciones</b>", normal),
                Paragraph(
                    mantenimiento.observaciones
                    or "Sin observaciones.",
                    normal,
                ),
            ],
        ]

        tabla_equipo = Table(
            datos_equipo,
            colWidths=[
                5.0 * cm,
                12.8 * cm,
            ],
        )

        tabla_equipo.setStyle(
            TableStyle(
                [
                    (
                        "SPAN",
                        (0, 0),
                        (1, 0),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (1, 0),
                        colors.HexColor("#E9ECEF"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (0, -1),
                        colors.HexColor("#F8F9FA"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        elementos.append(tabla_equipo)

        elementos.append(
            Spacer(1, 0.35 * cm)
        )

    # ======================================================
    # FIRMAS
    # ======================================================

    elementos.append(
        Spacer(1, 0.5 * cm)
    )

    elementos.append(
        Table(
            [
                [
                    Paragraph(
                        "FIRMAS",
                        encabezado,
                    )
                ]
            ],
            colWidths=[17.8 * cm],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor("#212529"),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            ),
        )
    )

    elementos.append(
        Spacer(1, 0.4 * cm)
    )

    # ======================================================
    # IMÁGENES DE LAS FIRMAS
    # ======================================================

    import base64

    def firma_a_imagen(firma_data):
        """
        Convierte una firma base64 en una imagen
        compatible con ReportLab.
        """

        if not firma_data:
            return None

        try:

            if "," in firma_data:
                firma_data = firma_data.split(
                    ",",
                    1
                )[1]

            datos = base64.b64decode(
                firma_data
            )

            return Image(
                BytesIO(datos),
                width=5.5 * cm,
                height=2.2 * cm,
            )

        except Exception:
            return None

    firma_bio = firma_a_imagen(
        orden.firma_biomedico
    )

    firma_resp = firma_a_imagen(
        orden.firma_responsable
    )

    firma_bio_elemento = (
        firma_bio
        if firma_bio
        else Paragraph(
            "<br/><br/><br/>",
            firma,
        )
    )

    firma_resp_elemento = (
        firma_resp
        if firma_resp
        else Paragraph(
            "<br/><br/><br/>",
            firma,
        )
    )

    firmas = Table(
        [
            [
                firma_bio_elemento,
                firma_resp_elemento,
            ],
        ],
        colWidths=[
            8.9 * cm,
            8.9 * cm,
        ],
    )

    firmas.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "BOTTOM",
                ),
            ]
        )
    )

    elementos.append(firmas)

    # ======================================================
    # LÍNEAS DE FIRMA
    # ======================================================

    lineas = Table(
        [
            [
                Paragraph(
                    "______________________________",
                    firma,
                ),
                Paragraph(
                    "______________________________",
                    firma,
                ),
            ],
            [
                Paragraph(
                    "<b>Biomédico / Ingeniero</b>",
                    firma,
                ),
                Paragraph(
                    "<b>Responsable del Servicio</b>",
                    firma,
                ),
            ],
            [
                Paragraph(
                    str(orden.ingeniero)
                    if orden.ingeniero
                    else "",
                    firma,
                ),
                Paragraph(
                    orden.responsable_nombre
                    or "",
                    firma,
                ),
            ],
            [
                Paragraph(
                    "",
                    firma,
                ),
                Paragraph(
                    orden.responsable_cargo
                    or "",
                    firma,
                ),
            ],
        ],
        colWidths=[
            8.9 * cm,
            8.9 * cm,
        ],
    )

    lineas.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    elementos.append(lineas)

    # ======================================================
    # GENERAR
    # ======================================================

    doc.build(elementos)

    pdf = buffer.getvalue()

    buffer.close()

    response = HttpResponse(
        pdf,
        content_type="application/pdf",
    )

    response[
        "Content-Disposition"
    ] = (
        f'inline; filename="OT-{orden.numero}.pdf"'
    )

    return response

# ==========================================================
# ELIMINAR MANTENIMIENTO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def eliminar_mantenimiento(request, id):

    mantenimiento = get_object_or_404(
        Mantenimiento.objects.select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "hoja_vida__equipo__institucion",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD POR INSTITUCIÓN
    # ======================================================

    if request.user.es_admin:

        if (
            mantenimiento.hoja_vida.equipo.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para eliminar este mantenimiento."
            )

            return redirect(
                "lista_mantenimientos"
            )

    # ======================================================
    # SOLO PERMITIR ELIMINAR POR POST
    # ======================================================

    if request.method != "POST":

        messages.error(
            request,
            "La eliminación debe realizarse mediante el formulario."
        )

        return redirect(
            "detalle_mantenimiento",
            mantenimiento.id,
        )

    # ======================================================
    # GUARDAR INFORMACIÓN PARA EL MENSAJE
    # ======================================================

    equipo = mantenimiento.hoja_vida.equipo.nombre

    # ======================================================
    # ELIMINAR
    # ======================================================

    mantenimiento.delete()

    messages.success(
        request,
        f"El mantenimiento del equipo {equipo} "
        "fue eliminado correctamente."
    )

    return redirect(
        "lista_mantenimientos"
    )

# ==========================================================
# ELIMINAR ORDEN DE TRABAJO Y SUS MANTENIMIENTOS
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def eliminar_orden_trabajo(request, id):

    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related(
            "servicio",
            "servicio__institucion",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD POR INSTITUCIÓN
    # ======================================================

    if request.user.es_admin:

        if (
            orden.servicio.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para eliminar esta "
                "Orden de Trabajo."
            )

            return redirect(
                "lista_ordenes_trabajo"
            )

    # ======================================================
    # SOLO POST
    # ======================================================

    if request.method != "POST":

        messages.error(
            request,
            "La eliminación debe realizarse mediante "
            "el formulario."
        )

        return redirect(
            "detalle_orden_trabajo",
            orden.id,
        )

    # ======================================================
    # ELIMINAR OT + MANTENIMIENTOS ASOCIADOS
    # ======================================================

    with transaction.atomic():

        mantenimientos = orden.mantenimientos.all()

        cantidad = mantenimientos.count()

        # Primero eliminamos los mantenimientos
        mantenimientos.delete()

        # Luego eliminamos la Orden de Trabajo
        orden.delete()

    messages.success(
        request,
        f"La Orden de Trabajo fue eliminada correctamente "
        f"junto con {cantidad} mantenimiento(s) asociado(s)."
    )

    return redirect(
        "lista_ordenes_trabajo"
    )
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def calendario_mantenimientos(request):
    """
    Calendario mensual de mantenimientos.

    Permite visualizar los mantenimientos programados
    por fecha y filtrarlos por servicio, estado, tipo
    y únicamente vencidos.
    """

    hoy = timezone.localdate()

    # ==========================================================
    # MES Y AÑO SELECCIONADOS
    # ==========================================================

    try:
        year = int(
            request.GET.get(
                "year",
                hoy.year,
            )
        )

        month = int(
            request.GET.get(
                "month",
                hoy.month,
            )
        )

    except (TypeError, ValueError):

        year = hoy.year
        month = hoy.month

    if month < 1 or month > 12:
        year = hoy.year
        month = hoy.month

    # ==========================================================
    # SERVICIOS DISPONIBLES
    # ==========================================================

    servicios = (
        Servicio.objects
        .all()
        .order_by("nombre")
    )

    if request.user.es_admin or request.user.es_biomedico:

        servicios = servicios.filter(
            institucion=request.user.institucion
        )

    # ==========================================================
    # MANTENIMIENTOS DEL MES
    # ==========================================================

    mantenimientos = (
        Mantenimiento.objects
        .select_related(
            "hoja_vida",
            "hoja_vida__equipo",
            "hoja_vida__equipo__servicio",
            "hoja_vida__equipo__institucion",
            "hoja_vida__equipo__catalogo",
            "ingeniero",
        )
        .filter(
            fecha_programada__year=year,
            fecha_programada__month=month,
        )
    )

    # ==========================================================
    # RESTRICCIÓN POR INSTITUCIÓN
    # ==========================================================

    if request.user.es_admin or request.user.es_biomedico:

        mantenimientos = mantenimientos.filter(
            hoja_vida__equipo__institucion=request.user.institucion
        )

    # ==========================================================
    # FILTROS
    # ==========================================================

    servicio_id = request.GET.get(
        "servicio",
        "",
    ).strip()

    estado = request.GET.get(
        "estado",
        "",
    ).strip()

    tipo = request.GET.get(
        "tipo",
        "",
    ).strip()

    solo_vencidos = request.GET.get(
        "vencidos",
        "",
    ).strip() == "1"

    # ==========================================================
    # FILTRO POR SERVICIO
    # ==========================================================

    if servicio_id:

        mantenimientos = mantenimientos.filter(
            hoja_vida__equipo__servicio_id=servicio_id
        )

    # ==========================================================
    # FILTRO POR ESTADO
    # ==========================================================

    if estado:

        mantenimientos = mantenimientos.filter(
            estado=estado
        )

    # ==========================================================
    # FILTRO POR TIPO
    # ==========================================================

    if tipo:

        mantenimientos = mantenimientos.filter(
            tipo=tipo
        )

    # ==========================================================
    # FILTRO SOLO VENCIDOS
    # ==========================================================

    if solo_vencidos:

        mantenimientos = mantenimientos.filter(
            fecha_programada__lt=hoy
        ).exclude(
            estado=Mantenimiento.Estado.FINALIZADO
        )

    # ==========================================================
    # ORDEN
    # ==========================================================

    mantenimientos = mantenimientos.order_by(
        "fecha_programada",
        "hoja_vida__equipo__nombre",
        "hoja_vida__equipo__serie",
    )

    # ==========================================================
    # DETERMINAR ESTADO VISUAL
    # ==========================================================

    mantenimientos_por_fecha = {}

    for mantenimiento in mantenimientos:

        mantenimiento.vencido = (
            mantenimiento.estado != Mantenimiento.Estado.FINALIZADO
            and mantenimiento.fecha_programada < hoy
        )

        mantenimiento.es_hoy = (
            mantenimiento.fecha_programada == hoy
        )

        if mantenimiento.vencido:

            mantenimiento.clase_calendario = "vencido"

        elif mantenimiento.es_hoy:

            mantenimiento.clase_calendario = "hoy"

        elif mantenimiento.estado == Mantenimiento.Estado.FINALIZADO:

            mantenimiento.clase_calendario = "finalizado"

        elif mantenimiento.estado == Mantenimiento.Estado.EN_PROCESO:

            mantenimiento.clase_calendario = "en-proceso"

        else:

            mantenimiento.clase_calendario = "programado"

        dia = mantenimiento.fecha_programada.day

        if dia not in mantenimientos_por_fecha:

            mantenimientos_por_fecha[dia] = []

        mantenimientos_por_fecha[dia].append(
            mantenimiento
        )

    # ==========================================================
    # GENERAR CALENDARIO DEL MES
    # ==========================================================

    calendario_base = calendar.Calendar(
        firstweekday=0
    ).monthdayscalendar(
        year,
        month,
    )

    semanas = []

    for semana in calendario_base:

        semana_datos = []

        for dia in semana:

            if dia == 0:

                semana_datos.append({
                    "dia": 0,
                    "mantenimientos": [],
                })

            else:

                semana_datos.append({
                    "dia": dia,
                    "mantenimientos": (
                        mantenimientos_por_fecha.get(
                            dia,
                            [],
                        )
                    ),
                })

        semanas.append(
            semana_datos
        )

    # ==========================================================
    # MES ANTERIOR
    # ==========================================================

    if month == 1:

        mes_anterior = 12
        anio_anterior = year - 1

    else:

        mes_anterior = month - 1
        anio_anterior = year

    # ==========================================================
    # MES SIGUIENTE
    # ==========================================================

    if month == 12:

        mes_siguiente = 1
        anio_siguiente = year + 1

    else:

        mes_siguiente = month + 1
        anio_siguiente = year

    # ==========================================================
    # NOMBRES DE LOS MESES
    # ==========================================================

    nombres_meses = [
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

    nombre_mes = nombres_meses[month]

    # ==========================================================
    # CONTADORES
    # ==========================================================

    total_mantenimientos = mantenimientos.count()

    vencidos_mes = sum(
        1
        for mantenimiento in mantenimientos
        if mantenimiento.vencido
    )

    hoy_mes = sum(
        1
        for mantenimiento in mantenimientos
        if mantenimiento.es_hoy
    )

    # ==========================================================
    # CONTEXTO
    # ==========================================================

    contexto = {

        "semanas": semanas,

        "year": year,
        "month": month,

        "nombre_mes": nombre_mes,

        "anio_anterior": anio_anterior,
        "mes_anterior": mes_anterior,

        "anio_siguiente": anio_siguiente,
        "mes_siguiente": mes_siguiente,

        "hoy": hoy,

        "servicios": servicios,

        "servicio_seleccionado": servicio_id,
        "estado_seleccionado": estado,
        "tipo_seleccionado": tipo,

        "solo_vencidos": solo_vencidos,

        "estados": Mantenimiento.Estado.choices,
        "tipos": Mantenimiento.Tipo.choices,

        "total_mantenimientos": total_mantenimientos,

        "vencidos_mes": vencidos_mes,

        "hoy_mes": hoy_mes,
    }

    return render(
        request,
        "mantenimiento/calendario.html",
        contexto,
    )