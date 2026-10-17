"""Rutas de la API publica de SITRAFO (version 1)."""
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import SeguimientoView

app_name = "api_publica"

urlpatterns = [
    path("seguimiento/<str:numero>/", SeguimientoView.as_view(), name="seguimiento"),
    # Documentacion: esquema OpenAPI y pagina interactiva Swagger
    path("esquema/", SpectacularAPIView.as_view(), name="esquema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api_publica:esquema"), name="docs"),
]
