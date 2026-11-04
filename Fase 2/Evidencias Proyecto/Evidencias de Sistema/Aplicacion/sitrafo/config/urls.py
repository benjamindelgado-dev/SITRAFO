"""Rutas raiz de SITRAFO."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as url_estatica
from django.urls import include, path
from django.views.generic import RedirectView


class FaviconView(RedirectView):
    """
    /favicon.ico: los navegadores lo piden siempre en la raiz, tambien en
    paginas que no usan la plantilla base (admin, PDF, errores). La URL se
    resuelve en cada peticion para que tome el nombre con hash de WhiteNoise.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return url_estatica("img/favicon.ico")


urlpatterns = [
    path("favicon.ico", FaviconView.as_view()),
    path("admin/", admin.site.urls),
    # API REST: unico punto de acceso a los datos
    path("api/v1/", include("config.api_urls")),
    # API publica: sistemas externos y portal web, con clave de API
    path("api/publica/v1/", include("apps.api_publica.urls")),
    # Aplicacion web orientada al cliente
    path("", include("apps.web.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
