"""
Rutas de la API REST de SITRAFO.

Unico punto de acceso a los datos. La aplicacion de escritorio y la
aplicacion web consumen estos mismos endpoints (RNF-05).
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.catalogo.views import (
    FamiliaProductoViewSet,
    ModeloProductoViewSet,
    ParametroTecnicoViewSet,
)
from apps.clientes.views import (
    ClienteViewSet,
    ComunaViewSet,
    ContactoClienteViewSet,
    DireccionClienteViewSet,
    RegionViewSet,
)
from apps.comercial.views import (
    CotizacionViewSet,
    EstadoDocumentoViewSet,
    OrdenCompraViewSet,
    SolicitudPresupuestoViewSet,
)
from apps.configuracion.views import (
    AvisoSitioViewSet,
    FeriadoViewSet,
    LogIntegracionViewSet,
    ParametroSistemaViewSet,
)
from apps.inventario.views import BodegaViewSet, MaterialViewSet
from apps.produccion.views import EmpleadoViewSet, OrdenTrabajoViewSet, TareaViewSet
from apps.seguridad.views import yo

router = DefaultRouter()

# Clientes
router.register("regiones", RegionViewSet, basename="region")
router.register("comunas", ComunaViewSet, basename="comuna")
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("contactos", ContactoClienteViewSet, basename="contacto")
router.register("direcciones", DireccionClienteViewSet, basename="direccion")

# Catalogo
router.register("familias", FamiliaProductoViewSet, basename="familia")
router.register("modelos", ModeloProductoViewSet, basename="modelo")
router.register("parametros-tecnicos", ParametroTecnicoViewSet, basename="parametro")

# Comercial
router.register("estados", EstadoDocumentoViewSet, basename="estado")
router.register("solicitudes", SolicitudPresupuestoViewSet, basename="solicitud")
router.register("cotizaciones", CotizacionViewSet, basename="cotizacion")
router.register("ordenes-compra", OrdenCompraViewSet, basename="orden-compra")

# Produccion e inventario
router.register("ordenes-trabajo", OrdenTrabajoViewSet, basename="orden-trabajo")
router.register("tareas", TareaViewSet, basename="tarea")
router.register("empleados", EmpleadoViewSet, basename="empleado")
router.register("materiales", MaterialViewSet, basename="material")
router.register("bodegas", BodegaViewSet, basename="bodega")

# Configuracion y canal web (solo usuarios internos)
router.register("parametros", ParametroSistemaViewSet, basename="parametro-sistema")
router.register("avisos", AvisoSitioViewSet, basename="aviso")
router.register("feriados", FeriadoViewSet, basename="feriado")
router.register("log-integraciones", LogIntegracionViewSet, basename="log-integracion")

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/yo/", yo, name="yo"),
    path("", include(router.urls)),
]
