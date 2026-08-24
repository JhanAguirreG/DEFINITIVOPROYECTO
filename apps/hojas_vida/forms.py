from django import forms

from .models import HojaVida, ValorCampoTecnico


class HojaVidaForm(forms.ModelForm):
    """
    Formulario principal de la Hoja de Vida.
    """

    class Meta:
        model = HojaVida

        fields = (
            "equipo",
            "forma_adquisicion",
            "numero_factura",
            "fecha_compra",
            "fecha_instalacion",
            "fecha_fabricacion",
            "garantia_hasta",
            "garantia_anios",
            "costo_adquisicion",
            "vida_util",
            "registro_importacion",
            "proveedor",
            "proveedor_telefono",
            "proveedor_ciudad_pais",
            "fabricante_telefono",
            "fabricante_ciudad_pais",
            "riesgo_electrico",
            "alimentacion_electricidad",
            "alimentacion_emergencia",
            "alimentacion_vapor",
            "alimentacion_vacio",
            "alimentacion_regulada",
            "alimentacion_baterias",
            "alimentacion_oxigeno",
            "alimentacion_agua",
            "alimentacion_estandar",
            "alimentacion_servicio",
            "alimentacion_aire",
            "tecnologia_predominante",
            "periodicidad_mantenimiento",
            "periodicidad_calibracion",
            "ubicacion_detallada",
            "fotografia",
            "recomendaciones_fabricante",
            "observaciones",
        )

        widgets = {
            "fecha_compra": forms.DateInput(
                attrs={"type": "date"}
            ),

            "fecha_instalacion": forms.DateInput(
                attrs={"type": "date"}
            ),

            "garantia_hasta": forms.DateInput(
                attrs={"type": "date"}
            ),

            "observaciones": forms.Textarea(
                attrs={"rows": 4}
            ),

            "recomendaciones_fabricante": forms.Textarea(
                attrs={"rows": 4}
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for nombre, campo in self.fields.items():

            if isinstance(
                campo.widget,
                forms.CheckboxInput
            ):
                campo.widget.attrs.update({
                    "class": "form-check-input",
                })

            elif isinstance(
                campo.widget,
                forms.ClearableFileInput
            ):
                campo.widget.attrs.update({
                    "class": "form-control",
                })

            else:
                campo.widget.attrs.update({
                    "class": "form-control",
                })

        self.fields["equipo"].empty_label = (
            "Seleccione un equipo"
        )


# ==========================================================
# CAMPOS TÉCNICOS DINÁMICOS
# ==========================================================

class CamposTecnicosForm(forms.Form):
    """
    Formulario dinámico.

    Los campos se generan automáticamente según
    el CatalogoEquipo asociado al equipo.
    """

    def __init__(
        self,
        *args,
        catalogo=None,
        hoja_vida=None,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        if not catalogo:
            return

        campos = (
            catalogo.campos_tecnicos
            .filter(activo=True)
            .order_by(
                "orden",
                "nombre",
            )
        )

        valores_existentes = {}

        if hoja_vida:

            valores_existentes = {
                valor.campo_id: valor.valor
                for valor in (
                    hoja_vida.valores_tecnicos
                    .select_related("campo")
                    .all()
                )
            }

        for campo in campos:

            nombre = f"campo_{campo.id}"

            valor_inicial = valores_existentes.get(
                campo.id,
                "",
            )

            # ==============================================
            # TIPO TEXTO
            # ==============================================

            if campo.tipo_dato == "TEXTO":

                widget = forms.TextInput(
                    attrs={
                        "class": "form-control",
                    }
                )

            # ==============================================
            # TIPO NÚMERO
            # ==============================================

            elif campo.tipo_dato == "NUMERO":

                widget = forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "step": "1",
                    }
                )

            # ==============================================
            # TIPO DECIMAL
            # ==============================================

            elif campo.tipo_dato == "DECIMAL":

                widget = forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "step": "0.01",
                    }
                )

            # ==============================================
            # TIPO FECHA
            # ==============================================

            elif campo.tipo_dato == "FECHA":

                widget = forms.DateInput(
                    attrs={
                        "class": "form-control",
                        "type": "date",
                    }
                )

            # ==============================================
            # TIPO SÍ / NO
            # ==============================================

            elif campo.tipo_dato == "SI_NO":

                widget = forms.Select(
                    choices=[
                        ("", "Seleccione"),
                        ("SI", "Sí"),
                        ("NO", "No"),
                    ],
                    attrs={
                        "class": "form-control",
                    },
                )

            else:

                widget = forms.TextInput(
                    attrs={
                        "class": "form-control",
                    }
                )

            # ==============================================
            # ETIQUETA
            # ==============================================

            label = campo.nombre

            if campo.unidad:

                label = (
                    f"{campo.nombre} "
                    f"({campo.unidad})"
                )

            # ==============================================
            # CAMPO DINÁMICO
            # ==============================================

            self.fields[nombre] = forms.CharField(
                label=label,
                required=campo.obligatorio,
                initial=valor_inicial,
                widget=widget,
            )

            # Guardamos referencia al CampoTecnico
            self.fields[nombre].campo_tecnico = campo


# ==========================================================
# ACCESORIOS
# ==========================================================

class AccesorioHojaVidaForm(forms.ModelForm):

    class Meta:

        from .models import AccesorioHojaVida

        model = AccesorioHojaVida

        fields = (
            "cantidad",
            "nombre",
            "observaciones",
        )

        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }


# ==========================================================
# DOCUMENTACIÓN
# ==========================================================

class DocumentacionHojaVidaForm(forms.ModelForm):

    class Meta:

        from .models import DocumentacionHojaVida

        model = DocumentacionHojaVida

        fields = (
            "tipo",
            "nombre",
            "archivo",
            "observaciones",
        )

        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }