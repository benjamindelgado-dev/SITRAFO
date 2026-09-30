"""
Pruebas de receta del modelo (RF-CAT-04, 05), cotizaciones con varias lineas
(RF-COM-03), versiones (RF-COM-10), empleados y tarifas (RF-OT-11).
"""
import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalogo.models import ModeloProducto
from apps.comercial.models import Cotizacion, OrdenCompraLinea
from apps.comercial.test_flujo import _cotizar, flujo  # noqa: F401
from apps.inventario.models import CategoriaMaterial, Material, PrecioMaterial
from apps.produccion.models import Empleado, TarifaHoraHombre
from apps.seguridad import matriz
from apps.seguridad.models import Rol, Usuario, UsuarioRol


def _api(nombre, rol):
    usuario = Usuario.objects.create_user(nombre, f"{nombre}@s.cl", "Clave123456",
                                          es_interno=True)
    UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    api = APIClient()
    api.force_authenticate(usuario)
    return api


def _cobre():
    cobre = Material.objects.create(categoria=CategoriaMaterial.objects.create(nombre="C"),
                                    codigo="CU", nombre="Cobre", unidad_medida="kg")
    PrecioMaterial.objects.create(material=cobre, costo_uf=Decimal("0.5"),
                                  vigente_desde=datetime.date(2026, 1, 1))
    return cobre


# ---------------------------------------------------------------------------
# Receta del modelo
# ---------------------------------------------------------------------------
def test_produccion_define_la_receta_y_cambia_el_costeo(flujo):  # noqa: F811
    produccion = _api("jefe", matriz.PRODUCCION)
    modelo, cobre = flujo["modelo"], _cobre()
    url = f"/api/v1/modelos/{modelo.pk}"

    respuesta = produccion.post(f"{url}/guardar_receta/", {
        "materiales": [{"material": cobre.pk, "cantidad": "100"}],
        "tareas": [{"nombre": "Bobinado", "horas_estimadas": "2"},
                   {"nombre": "Ensamble", "horas_estimadas": "1.5"}]}, format="json")
    assert respuesta.status_code == 200, respuesta.data
    assert Decimal(respuesta.data["costo_material_uf"]) == Decimal("50")
    assert [t["secuencia"] for t in respuesta.data["tareas"]] == [1, 2]

    costeo = flujo["interno"].get(f"{url}/costeo/").data
    assert costeo["origen_precio"] == "costeo"

    # El comercial la consulta pero no la modifica
    assert flujo["interno"].get(f"{url}/receta/").status_code == 200
    assert flujo["interno"].post(f"{url}/guardar_receta/", {}, format="json"
                                 ).status_code == 403


def test_receta_invalida_se_rechaza(flujo):  # noqa: F811
    produccion = _api("jefe", matriz.PRODUCCION)
    url = f"/api/v1/modelos/{flujo['modelo'].pk}/guardar_receta/"
    sin_horas = produccion.post(url, {"materiales": [], "tareas": [
        {"nombre": "X", "horas_estimadas": "0"}]}, format="json")
    assert sin_horas.status_code == 409


# ---------------------------------------------------------------------------
# Lineas y versiones
# ---------------------------------------------------------------------------
def test_cotizacion_con_varias_lineas_llega_a_la_orden(flujo):  # noqa: F811
    otro = ModeloProducto.objects.create(familia=flujo["modelo"].familia, codigo="TD-250",
                                         nombre="Transformador 250 kVA")
    cotizacion = _cotizar(flujo)
    base = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}"
    respuesta = flujo["interno"].post(f"{base}/lineas/", {"lineas": [
        {"modelo": flujo["modelo"].pk, "cantidad": 2},
        {"modelo": otro.pk, "cantidad": 1, "precio_uf": "300"},
    ]}, format="json")

    assert respuesta.status_code == 200, respuesta.data
    assert Decimal(respuesta.data["total_uf"]) == Decimal("660")   # 2 x 180 + 300
    flujo["interno"].post(f"{base}/emitir/")
    flujo["externo"].post(f"{base}/aceptar/")   # genera la orden de compra (RN-06)
    assert OrdenCompraLinea.objects.count() == 2


def test_solo_un_borrador_cambia_sus_lineas(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    base = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}"
    flujo["interno"].post(f"{base}/emitir/")
    respuesta = flujo["interno"].post(f"{base}/lineas/", {"lineas": [
        {"modelo": flujo["modelo"].pk, "cantidad": 5}]}, format="json")
    assert respuesta.status_code == 409


def test_nueva_version_reemplaza_la_emitida_y_conserva_la_historia(flujo):  # noqa: F811
    cotizacion = _cotizar(flujo)
    base = f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}"
    flujo["interno"].post(f"{base}/emitir/")

    respuesta = flujo["interno"].post(f"{base}/nueva_version/",
                                      {"motivo": "El cliente pidio 3 unidades"}, format="json")
    assert respuesta.status_code == 201
    assert respuesta.data["version"] == 2 and respuesta.data["estado_codigo"] == "borrador"
    versiones = Cotizacion.objects.filter(numero=cotizacion["numero"]).order_by("version")
    assert [c.estado.codigo for c in versiones] == ["anulada", "borrador"]

    # Sobre una version antigua no se crea otra
    assert flujo["interno"].post(f"{base}/nueva_version/").status_code == 409


def test_el_cliente_no_ve_borradores(flujo):  # noqa: F811
    _cotizar(flujo)
    datos = flujo["externo"].get("/api/v1/cotizaciones/").data
    assert datos["results"] == []


# ---------------------------------------------------------------------------
# Empleados y tarifas
# ---------------------------------------------------------------------------
def test_el_administrador_contrata_y_versiona_la_tarifa(flujo):  # noqa: F811
    admin = _api("admin", matriz.ADMIN)
    creado = admin.post("/api/v1/empleados/", {"rut": "16.789.234-5", "nombre": "Pedro Rojas",
                                               "cargo": "Armador"}, format="json")
    assert creado.status_code == 201, creado.data
    url = f"/api/v1/empleados/{creado.data['id_empleado']}/tarifa/"

    ayer = timezone.localdate() - datetime.timedelta(days=10)
    admin.post(url, {"valor_hora_uf": "0.4", "vigente_desde": ayer.isoformat()},
               format="json")
    respuesta = admin.post(url, {"valor_hora_uf": "0.5"}, format="json")

    assert respuesta.status_code == 200
    assert respuesta.data["tarifa_vigente_uf"] == "0.5000"
    empleado = Empleado.objects.get(pk=creado.data["id_empleado"])
    assert TarifaHoraHombre.objects.filter(empleado=empleado).count() == 2
    assert empleado.tarifa_vigente_a(ayer).valor_hora_uf == Decimal("0.4")

    produccion = _api("jefe", matriz.PRODUCCION)
    assert produccion.get("/api/v1/empleados/").status_code == 200
    assert produccion.post(url, {"valor_hora_uf": "9"}, format="json").status_code == 403


def test_tareas_diarias_vencen_cotizaciones(flujo):  # noqa: F811
    from io import StringIO

    from django.core.management import call_command

    Usuario.objects.create_superuser("root", "r@s.cl", "Clave123456")
    cotizacion = _cotizar(flujo)
    flujo["interno"].post(f"/api/v1/cotizaciones/{cotizacion['id_cotizacion']}/emitir/")
    Cotizacion.objects.update(vence_el=timezone.localdate() - datetime.timedelta(days=1))

    call_command("tareas_diarias", stdout=StringIO())   # sin red: degradacion controlada
    assert Cotizacion.objects.get().estado.codigo == "vencida"
