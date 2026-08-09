import base64
import uuid
import os


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q

from reportlab.platypus import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from io import BytesIO
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
        .prefetch_related(
            "detalles",
            "detalles__resultados",
        )
        .order_by(
            "-fecha",
            "-hora_inicio",
        )
    )

    # ==========================================================
    # PERMISOS POR INSTITUCIÓN
    # ==========================================================

    if request.user.es_admin or request.user.es_biomedico:

        inspecciones = inspecciones.filter(
            institucion=request.user.institucion
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

                inspecciones = inspecciones.filter(
                    fecha__year=anio,
                    fecha__month=mes,
                )

        except (ValueError, TypeError):

            pass

    # ==========================================================
    # FILTRO: INSPECCIONES CON NOVEDADES
    # ==========================================================

    if request.GET.get("novedades") == "1":

        inspecciones = inspecciones.filter(

            Q(
                detalles__estado__in=[
                    DetalleInspeccion.EstadoEquipo.OBSERVACION,
                    DetalleInspeccion.EstadoEquipo.FUERA_SERVICIO,
                ]
            )

            |

            Q(
                detalles__resultados__cumple=False
            )

        ).distinct()

    # ==========================================================
    # FILTRO: CHECKLIST NO CUMPLE
    # ==========================================================

    if request.GET.get("checklist") == "1":

        inspecciones = inspecciones.filter(
            detalles__resultados__cumple=False
        ).distinct()

    # ==========================================================
    # CONTADORES
    # ==========================================================

    inspecciones_abiertas = inspecciones.filter(
        estado=Inspeccion.Estado.ABIERTA
    ).count()

    inspecciones_finalizadas = inspecciones.filter(
        estado=Inspeccion.Estado.FINALIZADA
    ).count()

    inspecciones_hoy = inspecciones.filter(
        fecha=timezone.localdate()
    ).count()

    # ==========================================================
    # CONTEXTO
    # ==========================================================

    context = {

        "inspecciones": inspecciones,

        "inspecciones_abiertas":
            inspecciones_abiertas,

        "inspecciones_finalizadas":
            inspecciones_finalizadas,

        "inspecciones_hoy":
            inspecciones_hoy,

        "mes_filtro":
            mes,

        "anio_filtro":
            anio,

        "filtro_novedades":
            request.GET.get("novedades") == "1",

        "filtro_checklist":
            request.GET.get("checklist") == "1",

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
@login_required
@rol_requerido([
    "SUPERADMIN",
    "ADMIN",
    "BIOMEDICO",
])
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

    resultados = (
        ResultadoItem.objects
        .filter(
            detalle__inspeccion=inspeccion
        )
        .select_related(
            "detalle",
            "item",
        )
        .order_by(
            "detalle__equipo__nombre",
            "item__orden",
        )
    )

    # ======================================================
    # FIRMA DE LA INSPECCIÓN
    # ======================================================

    firma, _ = FirmaInspeccion.objects.get_or_create(
        inspeccion=inspeccion,
        defaults={
            "responsable_servicio": "",
            "observaciones_finales": "",
        },
    )

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        # --------------------------------------------------
        # EVITAR MODIFICAR UNA INSPECCIÓN FINALIZADA
        # --------------------------------------------------

        if inspeccion.estado == Inspeccion.Estado.FINALIZADA:

            messages.warning(
                request,
                "Esta inspección ya está finalizada y no puede modificarse.",
            )

            return redirect(
                "inspecciones:detalle_inspeccion",
                inspeccion.id,
            )

        # ==================================================
        # CHECKLIST
        # ==================================================

        formset = ResultadoItemFormSet(
            request.POST,
            queryset=resultados,
        )

        if formset.is_valid():

            formset.save()

        else:

            messages.error(
                request,
                "Hay errores en el checklist. Revise la información.",
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

        # ==================================================
        # OBSERVACIONES POR EQUIPO
        # ==================================================

        for detalle in detalles:

            observacion = request.POST.get(
                f"observaciones_{detalle.id}",
                "",
            )

            detalle.observaciones = observacion.strip()

            detalle.save(
                update_fields=[
                    "observaciones",
                ]
            )

        # ==================================================
        # RESPONSABLE DEL SERVICIO
        # ==================================================

        responsable_servicio = request.POST.get(
            "responsable_servicio",
            "",
        ).strip()

        firma.responsable_servicio = (
            responsable_servicio
        )

        # ==================================================
        # OBSERVACIONES FINALES
        # ==================================================

        observaciones_finales = request.POST.get(
            "observaciones_finales",
            "",
        ).strip()

        firma.observaciones_finales = (
            observaciones_finales
        )

        # ==================================================
        # FIRMA BIOMÉDICO
        # ==================================================

        firma_biomedico_data = request.POST.get(
            "firma_biomedico",
            "",
        )

        if firma_biomedico_data:

            firma_biomedico = guardar_firma_base64(
                firma_biomedico_data
            )

            if firma_biomedico:

                firma.firma_biomedico.save(
                    firma_biomedico.name,
                    firma_biomedico,
                    save=False,
                )

        # ==================================================
        # FIRMA RESPONSABLE
        # ==================================================

        firma_responsable_data = request.POST.get(
            "firma_responsable",
            "",
        )

        if firma_responsable_data:

            firma_responsable = guardar_firma_base64(
                firma_responsable_data
            )

            if firma_responsable:

                firma.firma_responsable.save(
                    firma_responsable.name,
                    firma_responsable,
                    save=False,
                )

        # ==================================================
        # GUARDAR FIRMA
        # ==================================================

        firma.save()

        # ==================================================
        # ACCIÓN
        # ==================================================

        accion = request.POST.get(
            "accion",
            "guardar",
        )

        # ==================================================
        # FINALIZAR
        # ==================================================

        if accion == "finalizar":

            # ----------------------------------------------
            # VALIDAR RESPONSABLE
            # ----------------------------------------------

            if not firma.responsable_servicio:

                messages.error(
                    request,
                    "Debe ingresar el responsable del servicio.",
                )

                return redirect(
                    "inspecciones:detalle_inspeccion",
                    inspeccion.id,
                )

            # ----------------------------------------------
            # VALIDAR FIRMA BIOMÉDICO
            # ----------------------------------------------

            if not firma.firma_biomedico:

                messages.error(
                    request,
                    "Debe registrar la firma del biomédico.",
                )

                return redirect(
                    "inspecciones:detalle_inspeccion",
                    inspeccion.id,
                )

            # ----------------------------------------------
            # VALIDAR FIRMA RESPONSABLE
            # ----------------------------------------------

            if not firma.firma_responsable:

                messages.error(
                    request,
                    "Debe registrar la firma del responsable del servicio.",
                )

                return redirect(
                    "inspecciones:detalle_inspeccion",
                    inspeccion.id,
                )

            # ----------------------------------------------
            # FECHA Y HORA DE FINALIZACIÓN
            # ----------------------------------------------

            inspeccion.hora_fin = timezone.now()

            inspeccion.estado = (
                Inspeccion.Estado.FINALIZADA
            )

            inspeccion.save(
                update_fields=[
                    "hora_fin",
                    "estado",
                    "actualizado",
                ]
            )

            messages.success(
                request,
                "Inspección finalizada correctamente.",
            )

        else:

            messages.success(
                request,
                "Cambios guardados correctamente.",
            )

        return redirect(
            "inspecciones:detalle_inspeccion",
            inspeccion.id,
        )

    # ======================================================
    # GET
    # ======================================================

    formset = ResultadoItemFormSet(
        queryset=resultados,
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
# funciones anteriores...
@login_required
def eliminar_inspeccion(request, id):

    inspeccion = get_object_or_404(
        Inspeccion,
        id=id,
    )

    if request.method == "POST":

        with transaction.atomic():

            inspeccion.delete()

        messages.success(
            request,
            "La inspección fue eliminada correctamente.",
        )

        return redirect(
            "inspecciones:lista_inspecciones"
        )

    return render(
        request,
        "inspecciones/confirmar_eliminacion.html",
        {
            "inspeccion": inspeccion,
        },
    )
def cargar_firma_pdf(campo_firma):
    """
    Carga una firma almacenada en MEDIA_ROOT
    para utilizarla directamente en ReportLab.
    """

    if not campo_firma:
        return None

    try:
        ruta = campo_firma.path

        print("FIRMA CARGADA:", ruta)

        if not os.path.isfile(ruta):
            print("NO EXISTE:", ruta)
            return None

        imagen = Image(
            ruta,
            width=6 * cm,
            height=2.2 * cm,
        )

        imagen.hAlign = "CENTER"

        return imagen

    except Exception as e:

        print("ERROR CARGANDO FIRMA:", e)

        return None
# ==========================================================
# GENERAR PDF
# ==========================================================

@login_required
@rol_requerido([
    "SUPERADMIN",
    "ADMIN",
    "BIOMEDICO",
])
def generar_pdf(request, id):

    inspeccion = get_object_or_404(
        Inspeccion.objects.select_related(
            "institucion",
            "servicio",
            "biomedico",
        ),
        id=id,
    )

    detalles = (
        DetalleInspeccion.objects
        .filter(inspeccion=inspeccion)
        .select_related("equipo")
        .prefetch_related(
            "resultados",
            "resultados__item",
        )
        .order_by("equipo__nombre")
    )

    try:
        firma = inspeccion.firma
    except FirmaInspeccion.DoesNotExist:
        firma = None

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="Inspeccion_{inspeccion.id}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    estilos = getSampleStyleSheet()

    titulo = estilos["Heading1"]
    titulo.alignment = TA_CENTER

    subtitulo = estilos["Heading2"]

    normal = estilos["BodyText"]

    elementos = []

    elementos.append(
        Paragraph(
            "INSPECCIÓN DIARIA DE EQUIPOS BIOMÉDICOS",
            titulo,
        )
    )

    elementos.append(Spacer(1, 0.4 * cm))

    datos = [
        [
            "Institución",
            inspeccion.institucion.nombre,
        ],
        [
            "Servicio",
            inspeccion.servicio.nombre,
        ],
        [
            "Fecha",
            str(inspeccion.fecha),
        ],
        [
            "Biomédico",
            inspeccion.biomedico.get_full_name()
            or inspeccion.biomedico.username,
        ],
        [
            "Estado",
            inspeccion.estado,
        ],
    ]

    tabla = Table(
        datos,
        colWidths=[
            5 * cm,
            11 * cm,
        ],
    )

    tabla.setStyle(
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
                    colors.HexColor("#0d6efd"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (0, -1),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica-Bold",
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

    elementos.append(tabla)

    elementos.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )
    # ======================================================
    # EQUIPOS INSPECCIONADOS
    # ======================================================

    elementos.append(
        Paragraph(
            "EQUIPOS INSPECCIONADOS",
            subtitulo,
        )
    )

    elementos.append(
        Spacer(
            1,
            0.2 * cm,
        )
    )

    for detalle in detalles:

        equipo = detalle.equipo

        # ----------------------------------------------
        # ENCABEZADO DEL EQUIPO
        # ----------------------------------------------

        elementos.append(
            Paragraph(
                f"<b>{equipo.nombre}</b>",
                subtitulo,
            )
        )

        informacion_equipo = [
            [
                "Código",
                equipo.codigo or "",
                "Inventario",
                equipo.inventario or "",
            ],
            [
                "Marca",
                equipo.marca or "",
                "Modelo",
                equipo.modelo or "",
            ],
            [
                "Serie",
                equipo.serie or "",
                "Ubicación",
                equipo.ubicacion or "",
            ],
            [
                "Estado",
                detalle.get_estado_display(),
                "Resultado",
                (
                    "CON OBSERVACIONES"
                    if detalle.observaciones
                    else "OPERATIVO"
                ),
            ],
        ]

        tabla_equipo = Table(
            informacion_equipo,
            colWidths=[
                2.5 * cm,
                5.5 * cm,
                2.5 * cm,
                5.5 * cm,
            ],
        )

        tabla_equipo.setStyle(
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
                        colors.HexColor("#e9ecef"),
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, -1),
                        colors.HexColor("#e9ecef"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, -1),
                        "Helvetica",
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (2, 0),
                        (2, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
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
                ]
            )
        )

        elementos.append(tabla_equipo)

        elementos.append(
            Spacer(
                1,
                0.2 * cm,
            )
        )

        # ----------------------------------------------
        # CHECKLIST
        # ----------------------------------------------

        elementos.append(
            Paragraph(
                "Checklist de inspección",
                normal,
            )
        )

        elementos.append(
            Spacer(
                1,
                0.1 * cm,
            )
        )

        checklist_data = [
            [
                "Ítem",
                "Cumple",
                "Observación",
            ]
        ]

        resultados = detalle.resultados.all()

        for resultado in resultados:

            checklist_data.append(
                [
                    resultado.item.descripcion,
                    "SI" if resultado.cumple else "NO",
                    resultado.observacion or "",
                ]
            )

        if len(checklist_data) == 1:

            checklist_data.append(
                [
                    "No hay ítems registrados",
                    "",
                    "",
                ]
            )

        tabla_checklist = Table(
            checklist_data,
            colWidths=[
                7 * cm,
                2.5 * cm,
                6 * cm,
            ],
            repeatRows=1,
        )

        tabla_checklist.setStyle(
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
                        (-1, 0),
                        colors.HexColor("#0d6efd"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (1, -1),
                        "CENTER",
                    ),
                    (
                        "BOTTOMPADDING",
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
                ]
            )
        )

        elementos.append(
            tabla_checklist
        )

        elementos.append(
            Spacer(
                1,
                0.2 * cm,
            )
        )

        # ----------------------------------------------
        # OBSERVACIONES DEL EQUIPO
        # ----------------------------------------------

        elementos.append(
            Paragraph(
                "<b>Observaciones del equipo:</b>",
                normal,
            )
        )

        elementos.append(
            Paragraph(
                detalle.observaciones
                or "Sin observaciones.",
                normal,
            )
        )

        elementos.append(
            Spacer(
                1,
                0.5 * cm,
            )
        )
    # ======================================================
    # CIERRE DE LA INSPECCIÓN
    # ======================================================

    elementos.append(
        Paragraph(
            "CIERRE DE LA INSPECCIÓN",
            subtitulo,
        )
    )

    elementos.append(
        Spacer(
            1,
            0.2 * cm,
        )
    )

    # ------------------------------------------------------
    # DATOS DE CIERRE
    # ------------------------------------------------------

    responsable = ""

    observaciones_finales = ""

    if firma:

        responsable = (
            firma.responsable_servicio
            or ""
        )

        observaciones_finales = (
            firma.observaciones_finales
            or ""
        )

    datos_cierre = [
        [
            "Responsable del servicio",
            responsable,
        ],
        [
            "Hora de inicio",
            (
                timezone.localtime(inspeccion.hora_inicio).strftime(
                    "%d/%m/%Y %H:%M"
                )
                if inspeccion.hora_inicio
                else ""
            ),
        ],
        [
            "Hora de finalización",
            (
                timezone.localtime(inspeccion.hora_fin).strftime(
                    "%d/%m/%Y %H:%M"
                )
                if inspeccion.hora_fin
                else ""
            ),
        ],
        [
            "Estado",
            inspeccion.get_estado_display(),
        ],
    ]

    tabla_cierre = Table(
        datos_cierre,
        colWidths=[
            5 * cm,
            11 * cm,
        ],
    )

    tabla_cierre.setStyle(
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
                    colors.HexColor("#e9ecef"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "BOTTOMPADDING",
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
            ]
        )
    )

    elementos.append(
        tabla_cierre
    )

    elementos.append(
        Spacer(
            1,
            0.3 * cm,
        )
    )

    # ======================================================
    # OBSERVACIONES FINALES
    # ======================================================

    elementos.append(
        Paragraph(
            "<b>Observaciones finales:</b>",
            normal,
        )
    )

    elementos.append(
        Spacer(
            1,
            0.1 * cm,
        )
    )

    elementos.append(
        Paragraph(
            observaciones_finales
            or "Sin observaciones finales.",
            normal,
        )
    )

    elementos.append(
        Spacer(
            1,
            0.6 * cm,
        )
    )
    # ======================================================
    # FIRMAS
    # ======================================================

    elementos.append(
        Paragraph(
            "FIRMAS",
            subtitulo,
        )
    )

    elementos.append(
        Spacer(
            1,
            0.2 * cm,
        )
    )

    # ------------------------------------------------------
    # CARGAR FIRMA BIOMÉDICO
    # ------------------------------------------------------

    imagen_firma_biomedico = None

    if firma and firma.firma_biomedico:

        imagen_firma_biomedico = cargar_firma_pdf(
            firma.firma_biomedico
        )

    if imagen_firma_biomedico is None:

        imagen_firma_biomedico = Paragraph(
            "Sin firma registrada",
            normal,
        )


    # ------------------------------------------------------
    # CARGAR FIRMA RESPONSABLE
    # ------------------------------------------------------

    imagen_firma_responsable = None

    if firma and firma.firma_responsable:

        imagen_firma_responsable = cargar_firma_pdf(
            firma.firma_responsable
        )

    if imagen_firma_responsable is None:

        imagen_firma_responsable = Paragraph(
            "Sin firma registrada",
            normal,
        )


    # ------------------------------------------------------
    # NOMBRES
    # ------------------------------------------------------

    nombre_biomedico = (
        inspeccion.biomedico.get_full_name()
        or inspeccion.biomedico.username
    )

    nombre_responsable = (
        responsable
        or "No registrado"
    )


    # ------------------------------------------------------
    # TABLA DE FIRMAS
    # ------------------------------------------------------

    datos_firmas = [

        [
            imagen_firma_biomedico,
            imagen_firma_responsable,
        ],

        [
            "________________________________",
            "________________________________",
        ],

        [
            Paragraph(
                f"<b>Biomédico responsable</b><br/>{nombre_biomedico}",
                normal,
            ),

            Paragraph(
                f"<b>Responsable del servicio</b><br/>{nombre_responsable}",
                normal,
            ),
        ],
    ]


    tabla_firmas = Table(
        datos_firmas,
        colWidths=[
            8 * cm,
            8 * cm,
        ],
    )


    tabla_firmas.setStyle(
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
                    "MIDDLE",
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )


    elementos.append(
        tabla_firmas
    )

    elementos.append(
        Spacer(
            1,
            0.3 * cm,
        )
    )
    # ======================================================
    # CONSTRUIR PDF
    # ======================================================

    try:

        doc.build(elementos)

    except Exception as e:

        return HttpResponse(
            f"Error al generar el PDF: {str(e)}",
            status=500,
            content_type="text/plain",
        )

    return response