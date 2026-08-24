from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.mantenimiento.models import Mantenimiento
from apps.usuarios.decorators import rol_requerido

from .forms import (
    AccesorioHojaVidaForm,
    DocumentacionHojaVidaForm,
    HojaVidaForm,
    CamposTecnicosForm,
)
from .models import (
    HojaVida,
    ValorCampoTecnico,
    DocumentacionHojaVida,
    AccesorioHojaVida,
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
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def crear_hoja_vida(request):

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        form = HojaVidaForm(
            request.POST,
            request.FILES,
        )

        # --------------------------------------------------
        # Determinar catálogo según equipo seleccionado
        # --------------------------------------------------

        catalogo = None

        equipo_id = request.POST.get("equipo")

        if equipo_id:

            from apps.equipos.models import Equipo

            equipo = get_object_or_404(
                Equipo.objects.select_related(
                    "catalogo"
                ),
                id=equipo_id,
            )

            catalogo = equipo.catalogo

        # --------------------------------------------------
        # Formulario técnico
        # --------------------------------------------------

        form_tecnico = CamposTecnicosForm(
            request.POST,
            catalogo=catalogo,
        )

        # --------------------------------------------------
        # Validar ambos formularios
        # --------------------------------------------------

        if form.is_valid() and form_tecnico.is_valid():

            equipo = form.cleaned_data["equipo"]

            # --------------------------------------------------
            # Verificar que no exista Hoja de Vida
            # --------------------------------------------------

            if hasattr(equipo, "hoja_vida"):

                messages.warning(
                    request,
                    "El equipo seleccionado ya tiene una Hoja de Vida.",
                )

                return redirect(
                    "detalle_hoja_vida",
                    equipo.hoja_vida.id,
                )

            # --------------------------------------------------
            # Guardar todo
            # --------------------------------------------------

            with transaction.atomic():

                hoja = form.save()

                for nombre, campo_form in (
                    form_tecnico.fields.items()
                ):

                    campo_tecnico = getattr(
                        campo_form,
                        "campo_tecnico",
                        None,
                    )

                    if not campo_tecnico:
                        continue

                    valor = form_tecnico.cleaned_data.get(
                        nombre,
                        "",
                    )

                    ValorCampoTecnico.objects.create(
                        hoja_vida=hoja,
                        campo=campo_tecnico,
                        valor=valor or "",
                    )

            messages.success(
                request,
                "Hoja de vida creada correctamente.",
            )

            return redirect(
                "detalle_hoja_vida",
                hoja.id,
            )

    # ======================================================
    # GET
    # ======================================================

    else:

        form = HojaVidaForm()

        form_tecnico = CamposTecnicosForm()

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "hojas_vida/form.html",
        {
            "form": form,
            "form_tecnico": form_tecnico,
            "titulo": "Nueva Hoja de Vida",
        },
    )
# ==========================================================
# EDITAR
# ==========================================================
@login_required
@rol_requerido(["SUPERADMIN", "ADMIN"])
def editar_hoja_vida(request, id):

    hoja = get_object_or_404(
        HojaVida.objects.select_related(
            "equipo",
            "equipo__institucion",
            "equipo__servicio",
            "equipo__catalogo",
        ),
        id=id,
    )

    # ======================================================
    # SEGURIDAD
    # ======================================================

    if request.user.es_admin:

        if (
            hoja.equipo.institucion
            != request.user.institucion
        ):

            messages.error(
                request,
                "No tiene permisos para editar esta Hoja de Vida.",
            )

            return redirect(
                "lista_hojas_vida"
            )

    catalogo = hoja.equipo.catalogo

    # ======================================================
    # POST
    # ======================================================

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

        # --------------------------------------------------
        # Validar
        # --------------------------------------------------

        if form.is_valid() and form_tecnico.is_valid():

            with transaction.atomic():

                hoja = form.save()

                # ------------------------------------------
                # Guardar características técnicas
                # ------------------------------------------

                for nombre, campo_form in (
                    form_tecnico.fields.items()
                ):

                    campo_tecnico = getattr(
                        campo_form,
                        "campo_tecnico",
                        None,
                    )

                    if not campo_tecnico:
                        continue

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

            messages.success(
                request,
                "Hoja de vida actualizada correctamente.",
            )

            return redirect(
                "detalle_hoja_vida",
                hoja.id,
            )

    # ======================================================
    # GET
    # ======================================================

    else:

        form = HojaVidaForm(
            instance=hoja,
        )

        form_tecnico = CamposTecnicosForm(
            catalogo=catalogo,
            hoja_vida=hoja,
        )

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "hojas_vida/form.html",
        {
            "form": form,
            "form_tecnico": form_tecnico,
            "titulo": "Editar Hoja de Vida",
            "editar": True,
            "hoja": hoja,
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