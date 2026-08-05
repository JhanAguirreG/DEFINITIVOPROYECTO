from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [

    path("admin/", admin.site.urls),

    # Login
    path("", include("apps.usuarios.urls")),

    # Instituciones
    path(
        "instituciones/",
        include("apps.instituciones.urls")
    ),

    path(
    "servicios/",
    include("apps.servicios.urls"),),

    path(
    "equipos/",
    include("apps.equipos.urls"),
    ),
    path(
    "catalogo/",
    include("apps.catalogo.urls"),
    ),
    path(
    "hojas-vida/",
    include("apps.hojas_vida.urls"),
    ),
    path(
    "mantenimientos/",
    include("apps.mantenimiento.urls"),
    ),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )