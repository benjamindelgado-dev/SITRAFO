"""Rutas raiz de SITRAFO."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # API REST: unico punto de acceso a los datos
    path("api/v1/", include("config.api_urls")),
    # Aplicacion web orientada al cliente
    path("", include("apps.web.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
