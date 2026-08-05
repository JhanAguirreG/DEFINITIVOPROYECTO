from django.core.management.base import BaseCommand

from apps.catalogo.models import CatalogoEquipo
from apps.equipos.models import Equipo


class Command(BaseCommand):
    help = "Asigna automáticamente un CatalogoEquipo a los equipos existentes."

    def handle(self, *args, **options):

        actualizados = 0

        for equipo in Equipo.objects.all():

            if equipo.catalogo:
                continue

            catalogo, creado = CatalogoEquipo.objects.get_or_create(

                nombre=equipo.nombre,

                defaults={
                    "descripcion": equipo.nombre,
                    "riesgo": equipo.riesgo,
                    "tecnologia": equipo.tecnologia,
                    "requiere_mantenimiento": True,
                    "frecuencia_mantenimiento": equipo.frecuencia_mantenimiento,
                },
            )

            equipo.catalogo = catalogo
            equipo.save(update_fields=["catalogo"])

            actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Se actualizaron {actualizados} equipos."
            )
        )