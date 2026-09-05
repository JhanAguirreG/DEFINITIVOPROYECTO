from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import JsonResponse
from apps.calibraciones.models import Calibracion
from apps import hojas_vida
from apps.mantenimiento.models import Mantenimiento
from apps.usuarios.decorators import rol_requerido
from apps.inspecciones.models import Inspeccion, DetalleInspeccion
from .forms import (
    AccesorioHojaVidaForm,
    DocumentacionHojaVidaForm,
    DocumentacionHojaVidaFormSet,
    HojaVidaForm,
    CamposTecnicosForm,
)
from .models import (
    HojaVida,
    ValorCampoTecnico,
    DocumentacionHojaVida,
    AccesorioHojaVida,
)
from apps.equipos.models import Equipo
from apps.servicios.models import Servicio
# ==========================================================
# CAMPOS TÉCNICOS DINÁMICOS
# ==========================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def campos_tecnicos_equipo(request):

    equipo_id = request.GET.get("equipo")

    if not equipo_id:

        return render(
            request,
            "hojas_vida/_campos_tecnicos.html",
            {
                "form_tecnico": None,
                "catalogo": None,
            },
        )

    equipo = get_object_or_404(
        Equipo.objects.select_related("catalogo"),
        id=equipo_id,
    )

    catalogo = equipo.catalogo

    # ======================================================
    # EQUIPO SIN CATÁLOGO
    # ======================================================

    if not catalogo:

        return render(
            request,
            "hojas_vida/_campos_tecnicos.html",
            {
                "form_tecnico": None,
                "catalogo": None,
                "mensaje": (
                    "Este equipo no tiene un catálogo asociado. "
                    "Se recomienda crear un catálogo para este "
                    "tipo de equipo, pero no es obligatorio."
                ),
            },
        )

    # ======================================================
    # FORMULARIO TÉCNICO
    # ======================================================

    form_tecnico = CamposTecnicosForm(
        catalogo=catalogo,
    )

    return render(
        request,
        "hojas_vida/_campos_tecnicos.html",
        {
            "form_tecnico": form_tecnico,
            "catalogo": catalogo,
        },
    )
# ==========================================================
# FUNCIÓN AUXILIAR
# ==========================================================

def crear_valores_tecnicos_iniciales(hoja):
    """
    Crea los registros de ValorCampoTecnico correspondientes
    al catálogo del equipo.

    Los campos técnicos vienen definidos en CatalogoEquipo.

    No modifica valores que ya existan.
    """

    catalogo = hoja.equipo.catalogo

    if not catalogo:
        return

    campos = (
        catalogo.campos_tecnicos
        .filter(activo=True)
        .order_by("orden", "nombre")
    )

    for campo in campos:

        ValorCampoTecnico.objects.get_or_create(
            hoja_vida=hoja,
            campo=campo,
            defaults={
                "valor": "",
            },
        )


# ==========================================================
# LISTADO
# ==========================================================

@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def lista_hojas_vida(request):

    hojas = (
        HojaVida.objects
        .select_related(
            "equipo",
            "equipo__institucion",
            "equipo__servicio",
            "equipo__catalogo",
        )
        .prefetch_related(
            "valores_tecnicos__campo",
            "accesorios",
            "documentos",
        )
        .order_by("equipo__nombre")
    )

    # ADMIN y BIOMÉDICO solamente ven
    # equipos de su institución.

    if request.user.es_admin or request.user.es_biomedico:

        hojas = hojas.filter(
            equipo__institucion=request.user.institucion
        )

    return render(
        request,
        "hojas_vida/index.html",
        {
            "hojas": hojas,
        },
    )
# ==========================================================
# CREAR
# ==========================================================
# ==========================================================
# CREAR HOJA DE VIDA
# ==========================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_hoja_vida(request):

    # ==========================================================
    # PASO 1: SELECCIÓN DE SERVICIO Y EQUIPO
    # ==========================================================

    equipo_id = request.GET.get("equipo")

    if not equipo_id and request.method == "GET":

        servicios = Servicio.objects.all().order_by("nombre")

        return render(
            request,
            "hojas_vida/seleccionar_equipo.html",
            {
                "servicios": servicios,
                "titulo": "Nueva Hoja de Vida",
            },
        )

    # ==========================================================
    # EQUIPO SELECCIONADO
    # ==========================================================

    equipo = None
    catalogo = None

    if equipo_id:

        equipo = get_object_or_404(
            Equipo.objects.select_related(
                "catalogo",
                "servicio",
            ),
            id=equipo_id,
        )

        catalogo = equipo.catalogo

    # ==========================================================
    # POST DEL FORMULARIO PRINCIPAL
    # ==========================================================

    if request.method == "POST":

        form = HojaVidaForm(
            request.POST,
            request.FILES,
        )

        equipo_id_post = request.POST.get("equipo")

        if equipo_id_post:

            equipo = get_object_or_404(
                Equipo.objects.select_related(
                    "catalogo",
                    "servicio",
                ),
                id=equipo_id_post,
            )

            catalogo = equipo.catalogo

        form_tecnico = CamposTecnicosForm(
            request.POST,
            catalogo=catalogo,
        )

        formset_documentos = DocumentacionHojaVidaFormSet(
            request.POST,
            request.FILES,
            instance=form.instance,
            prefix="documentos",
        )

        if (
            form.is_valid()
            and form_tecnico.is_valid()
            and formset_documentos.is_valid()
        ):

            with transaction.atomic():

                hoja = form.save(commit=False)
                        # Obtener el equipo seleccionado definitivamente
                equipo_id_post = request.POST.get("equipo")
                if equipo_id_post:
                    equipo = get_object_or_404(
                        Equipo.objects.select_related(
                                "catalogo",
                                "servicio",
                        ),
                        id=equipo_id_post,
                    )
                    
                    hoja.equipo = equipo

                        # Sincronizar catálogo
                if hoja.equipo and hoja.equipo.catalogo:
                    hoja.sincronizar_catalogo()

                hoja.save()

                formset_documentos.instance = hoja
                formset_documentos.save()

                for nombre, campo_form in form_tecnico.fields.items():

                    if not hasattr(
                        campo_form,
                        "campo_tecnico",
                    ):
                        continue

                    campo_tecnico = campo_form.campo_tecnico

                    valor = form_tecnico.cleaned_data.get(
                        nombre,
                        "",
                    )

                    ValorCampoTecnico.objects.update_or_create(
                        hoja_vida=hoja,
                        campo=campo_tecnico,
                        defaults={
                            "valor": valor or "",
                        },
                    )

            if catalogo:

                messages.success(
                    request,
                    "Hoja de vida creada correctamente. "
                    "La información del catálogo y la documentación "
                    "técnica fueron incorporadas.",
                )

            else:

                messages.warning(
                    request,
                    "Hoja de vida creada correctamente. "
                    "Este equipo no tiene un catálogo asociado.",
                )

            return redirect(
                "detalle_hoja_vida",
                hoja.id,
            )

    else:

        form = HojaVidaForm()

        # ======================================================
        # DEJAR EL EQUIPO PRESELECCIONADO
        # ======================================================

        if equipo:

            form.fields["equipo"].initial = equipo

        form_tecnico = CamposTecnicosForm(
            catalogo=catalogo,
        )

        formset_documentos = DocumentacionHojaVidaFormSet(
            instance=form.instance,
            prefix="documentos",
        )

    return render(
        request,
        "hojas_vida/form.html",
        {
            "form": form,
            "form_tecnico": form_tecnico,
            "formset_documentos": formset_documentos,
            "titulo": "Nueva Hoja de Vida",
            "equipo": equipo,
            "catalogo": catalogo,
        },
    )
# ==========================================================
# EDITAR HOJA DE VIDA
# ==========================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_hoja_vida(request, id):

    hoja = get_object_or_404(
        HojaVida.objects.select_related(
            "equipo",
            "equipo__catalogo",
        ),
        id=id,
    )

    catalogo = hoja.equipo.catalogo

    # ==========================================================
    # POST
    # ==========================================================

    if request.method == "POST":

        form = HojaVidaForm(
            request.POST,
            request.FILES,
            instance=hoja,
        )

        form_tecnico = CamposTecnicosForm(
            request.POST,
            catalogo=catalogo,
            hoja_vida=hoja,
        )

        formset_documentos = DocumentacionHojaVidaFormSet(
            request.POST,
            request.FILES,
            instance=hoja,
            prefix="documentos",
        )

        if (
            form.is_valid()
            and form_tecnico.is_valid()
            and formset_documentos.is_valid()
        ):

            with transaction.atomic():

                hoja = form.save()

                # IMPORTANTE:
                # No resincronizamos automáticamente el catálogo,
                # para conservar la información histórica.

                # ==============================================
                # DOCUMENTACIÓN
                # ==============================================

                formset_documentos.save()

                # ==============================================
                # CAMPOS TÉCNICOS
                # ==============================================

                for nombre, campo_form in form_tecnico.fields.items():

                    if not hasattr(
                        campo_form,
                        "campo_tecnico",
                    ):
                        continue

                    campo_tecnico = (
                        campo_form.campo_tecnico
                    )

                    valor = (
                        form_tecnico.cleaned_data.get(
                            nombre,
                            "",
                        )
                    )

                    ValorCampoTecnico.objects.update_or_create(
                        hoja_vida=hoja,
                        campo=campo_tecnico,
                        defaults={
                            "valor": valor or "",
                        },
                    )

            messages.success(
                request,
                "Hoja de vida actualizada correctamente.",
            )

            return redirect(
                "detalle_hoja_vida",
                hoja.id,
            )

    # ==========================================================
    # GET
    # ==========================================================

    else:

        form = HojaVidaForm(
            instance=hoja,
        )

        form_tecnico = CamposTecnicosForm(
            catalogo=catalogo,
            hoja_vida=hoja,
        )

        formset_documentos = DocumentacionHojaVidaFormSet(
            instance=hoja,
            prefix="documentos",
        )

    return render(
        request,
        "hojas_vida/form.html",
        {
            "form": form,
            "form_tecnico": form_tecnico,
            "formset_documentos": formset_documentos,
            "titulo": "Editar Hoja de Vida",
            "editar": True,
            "hoja": hoja,
            "catalogo": catalogo,
        },
    )
# ==========================================================
# DETALLE
# ==========================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN", "BIOMEDICO"])
def detalle_hoja_vida(request, id):

    hoja = get_object_or_404(
        HojaVida.objects
        .select_related(
            "equipo",
            "equipo__institucion",
            "equipo__servicio",
            "equipo__catalogo",
        )
        .prefetch_related(
            "valores_tecnicos__campo",
            "accesorios",
            "documentos",
        ),
        id=id,
    )

    # ==========================================================
    # PERMISOS POR INSTITUCIÓN
    # ==========================================================

    if request.user.es_admin or request.user.es_biomedico:

        if hoja.equipo.institucion != request.user.institucion:

            messages.error(
                request,
                "No tiene permisos para visualizar esta hoja de vida.",
            )

            return redirect("lista_hojas_vida")

    # ==========================================================
    # MANTENIMIENTOS
    # ==========================================================

    mantenimientos = (
        Mantenimiento.objects
        .filter(
            hoja_vida=hoja
        )
        .select_related(
            "ingeniero",
            "orden_trabajo",
        )
        .order_by(
            "-fecha_programada"
        )
    )

    # ==========================================================
    # CARACTERÍSTICAS TÉCNICAS
    # ==========================================================

    valores_tecnicos = hoja.valores_tecnicos.all()

    # ==========================================================
    # ACCESORIOS
    # ==========================================================

    accesorios = hoja.accesorios.all()

    # ==========================================================
    # DOCUMENTACIÓN
    # ==========================================================

    documentos = hoja.documentos.all()
        # ==========================================================
    # INSPECCIONES DEL EQUIPO
    # ==========================================================
    calibraciones = (
        Calibracion.objects
        .filter(equipo=hoja.equipo)
        .order_by("-fecha_calibracion", "-creado")
    )
    inspecciones = (
        Inspeccion.objects
        .filter(
            detalles__equipo=hoja.equipo
        )
        .select_related(
            "institucion",
            "servicio",
            "biomedico",
        )
        .prefetch_related(
            "detalles",
            "firma",
        )
        .distinct()
        .order_by(
            "-fecha",
            "-hora_inicio",
        )
    )
    # ==========================================================
    # INDICADORES
    # ==========================================================

    total_mantenimientos = mantenimientos.count()

    preventivos = mantenimientos.filter(
        tipo=Mantenimiento.Tipo.PREVENTIVO
    ).count()

    correctivos = mantenimientos.filter(
        tipo=Mantenimiento.Tipo.CORRECTIVO
    ).count()

    ultimo_mantenimiento = (
        mantenimientos
        .filter(
            estado=Mantenimiento.Estado.FINALIZADO
        )
        .order_by("-fecha_fin")
        .first()
    )

    proximo_mantenimiento = (
        mantenimientos
        .filter(
            estado=Mantenimiento.Estado.PROGRAMADO
        )
        .order_by("fecha_programada")
        .first()
    )

    equipo_fuera_servicio = (
        hoja.equipo.estado == "FUERA_SERVICIO"
    )

    mantenimiento_vencido = False

    if proximo_mantenimiento:

        if (
            proximo_mantenimiento.fecha_programada
            < timezone.now().date()
        ):
            mantenimiento_vencido = True

    # ==========================================================
    # CONTEXTO
    # ==========================================================

    context = {

        "hoja": hoja,

        "mantenimientos": mantenimientos,

        "valores_tecnicos": valores_tecnicos,

        "accesorios": accesorios,

        "documentos": documentos,

        "calibraciones": calibraciones,

        # Próximos módulos

        "inspecciones": inspecciones,

        "tecnovigilancias": [],
    
        # Indicadores

        "total_mantenimientos": total_mantenimientos,

        "preventivos": preventivos,

        "correctivos": correctivos,

        "ultimo_mantenimiento": ultimo_mantenimiento,

        "proximo_mantenimiento": proximo_mantenimiento,

        "equipo_fuera_servicio": equipo_fuera_servicio,

        "mantenimiento_vencido": mantenimiento_vencido,

    }

    return render(
        request,
        "hojas_vida/detalle.html",
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

    equipos = (
        Equipo.objects
        .filter(servicio_id=servicio_id)
        .order_by("nombre", "codigo")
    )

    data = []

    for equipo in equipos:

        nombre = equipo.nombre

        if equipo.codigo:
            nombre += f" — {equipo.codigo}"

        data.append(
            {
                "id": equipo.id,
                "nombre": nombre,
            }
        )

    return JsonResponse(
        {
            "equipos": data
        }
    )