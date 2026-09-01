from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps import hojas_vida
from apps.mantenimiento.models import Mantenimiento
from apps.usuarios.decorators import rol_requerido

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

    equipo = None
    catalogo = None

    # ==========================================================
    # POST
    # ==========================================================

    if request.method == "POST":

        form = HojaVidaForm(
            request.POST,
            request.FILES,
        )

        # ======================================================
        # EQUIPO Y CATÁLOGO
        # ======================================================

        equipo_id = request.POST.get("equipo")

        if equipo_id:

            equipo = get_object_or_404(
                Equipo.objects.select_related("catalogo"),
                id=equipo_id,
            )

            catalogo = equipo.catalogo

        # ======================================================
        # CAMPOS TÉCNICOS
        # ======================================================

        form_tecnico = CamposTecnicosForm(
            request.POST,
            catalogo=catalogo,
        )

        # ======================================================
        # DOCUMENTACIÓN
        # ======================================================

        formset_documentos = DocumentacionHojaVidaFormSet(
            request.POST,
            request.FILES,
            instance=form.instance,
            prefix="documentos",
        )

        # ======================================================
        # VALIDACIÓN
        # ======================================================

        if (
            form.is_valid()
            and form_tecnico.is_valid()
            and formset_documentos.is_valid()
        ):

            with transaction.atomic():

                hoja = form.save(commit=False)

                # ==============================================
                # SINCRONIZAR CATÁLOGO
                # ==============================================

                if equipo and catalogo:

                    hoja.sincronizar_catalogo()

                hoja.save()

                # ==============================================
                # GUARDAR DOCUMENTOS
                # ==============================================

                formset_documentos.instance = hoja

                formset_documentos.save()

                # ==============================================
                # GUARDAR CAMPOS TÉCNICOS
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

    # ==========================================================
    # GET
    # ==========================================================

    else:

        form = HojaVidaForm()

        form_tecnico = CamposTecnicosForm()

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

        # Próximos módulos

        "calibraciones": [],

        "inspecciones": [],

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