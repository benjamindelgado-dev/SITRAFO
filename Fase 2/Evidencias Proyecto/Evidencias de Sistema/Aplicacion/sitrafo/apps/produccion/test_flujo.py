"""
Pruebas del flujo productivo operado desde la API: generacion de ordenes de
trabajo, planificacion, registro en taller, consumo con descuento de stock,
anulacion, paso a calidad y bloqueo de cierre.
"""
import datetime
from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.catalogo.models import (
    BomModelo,
    FamiliaProducto,
    ModeloProducto,
    TareaEstandarModelo,
)
from apps.clientes.models import Cliente
from apps.comercial.models import (
    Cotizacion,
    CotizacionLinea,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraLinea,
    SolicitudPresupuesto,
)
from apps.inventario.models import (
    Bodega,
    CategoriaMaterial,
    Material,
    MovimientoInventario,
    PrecioMaterial,
)
from apps.produccion.models import Empleado, OrdenTrabajo, TareaOT, TarifaHoraHombre
from apps.seguridad import matriz
from apps.seguridad.models import Auditoria, Rol, Usuario, UsuarioRol

HOY = datetime.date.today()


def _usuario(nombre, rol, **extra):
    usuario = Usuario.objects.create_user(nombre, f"{nombre}@sitrafo.cl", "Clave123456",
                                          es_interno=True, **extra)
    UsuarioRol.objects.create(usuario=usuario, rol=Rol.objects.get(nombre=rol))
    return usuario


def _api(usuario):
    api = APIClient()
    api.force_authenticate(usuario)
    return api


def _estado(tipo, codigo):
    return EstadoDocumento.objects.get(tipo_documento=tipo, codigo=codigo)


@pytest.fixture
def planta(db):
    call_command("cargar_estados", verbosity=0)
    call_command("cargar_roles", verbosity=0)

    jefe = _usuario("produccion", matriz.PRODUCCION)
    comercial = _usuario("comercial", matriz.COMERCIAL)
    u_juan = _usuario("operario", matriz.OPERARIO)
    u_pedro = _usuario("operario2", matriz.OPERARIO)

    juan = Empleado.objects.create(rut="12345678-5", nombre="Juan Soto", cargo="Bobinador",
                                   usuario=u_juan)
    pedro = Empleado.objects.create(rut="11111111-1", nombre="Pedro Rojas", cargo="Armador",
                                    usuario=u_pedro)
    for empleado in (juan, pedro):
        TarifaHoraHombre.objects.create(empleado=empleado, valor_hora_uf=Decimal("0.5"),
                                        vigente_desde=datetime.date(2026, 1, 1))

    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    modelo = ModeloProducto.objects.create(familia=familia, codigo="TD-100",
                                           nombre="Transformador 100 kVA")
    TareaEstandarModelo.objects.create(modelo=modelo, nombre="Bobinado", secuencia=1,
                                       horas_estimadas=Decimal("8"))
    TareaEstandarModelo.objects.create(modelo=modelo, nombre="Ensamble", secuencia=2,
                                       horas_estimadas=Decimal("4"))
    categoria = CategoriaMaterial.objects.create(nombre="Conductores")
    cobre = Material.objects.create(categoria=categoria, codigo="CU-01", nombre="Cobre",
                                    unidad_medida="kg", stock_minimo=Decimal("10"))
    PrecioMaterial.objects.create(material=cobre, costo_uf=Decimal("0.2"),
                                  vigente_desde=datetime.date(2026, 1, 1))
    BomModelo.objects.create(modelo=modelo, material=cobre, cantidad=Decimal("30"))
    bodega = Bodega.objects.create(codigo="B1", nombre="Bodega central")
    MovimientoInventario.objects.create(material=cobre, bodega=bodega, tipo="recepcion",
                                        cantidad=Decimal("100"),
                                        costo_unitario_uf=Decimal("0.2"), usuario=jefe)

    cliente = Cliente.objects.create(rut="76543210-3", razon_social="Maipo SpA",
                                     tipo_persona="juridica")
    solicitud = SolicitudPresupuesto.objects.create(
        numero="SP-2026-0001", cliente=cliente, modelo=modelo, cantidad=2,
        estado=_estado("solicitud", "cotizada"),
    )
    cotizacion = Cotizacion.objects.create(
        numero="COT-2026-0001", solicitud=solicitud, cliente=cliente,
        estado=_estado("cotizacion", "aceptada"), ejecutivo=comercial,
        valor_uf=Decimal("40000"), fecha_valor_uf=HOY,
        vence_el=HOY + datetime.timedelta(days=30), total_uf=Decimal("50"),
    )
    linea = CotizacionLinea.objects.create(
        cotizacion=cotizacion, modelo=modelo, cantidad=2, costo_material_uf=Decimal("6"),
        costo_hh_uf=Decimal("6"), precio_uf=Decimal("25"),
    )
    orden = OrdenCompra.objects.create(
        numero="OC-2026-0001", cotizacion=cotizacion, cliente=cliente,
        estado=_estado("orden_compra", "confirmada"), total_uf=Decimal("50"),
    )
    OrdenCompraLinea.objects.create(orden_compra=orden, cotizacion_linea=linea, cantidad=2,
                                    precio_uf=Decimal("25"))
    return {"jefe": _api(jefe), "comercial": _api(comercial), "juan": _api(u_juan),
            "pedro": _api(u_pedro), "orden": orden, "cobre": cobre, "bodega": bodega,
            "e_juan": juan, "e_pedro": pedro}


def _generar(planta):
    respuesta = planta["jefe"].post(f"/api/v1/ordenes-compra/{planta['orden'].pk}/"
                                    "generar_ordenes_trabajo/")
    assert respuesta.status_code == 201, respuesta.data
    return OrdenTrabajo.objects.get()


def _en_ejecucion(planta):
    """OT iniciada con Bobinado asignado a Juan y Ensamble a Pedro."""
    ot = _generar(planta)
    bobinado, ensamble = ot.tareas.order_by("secuencia")
    planta["jefe"].post(f"/api/v1/tareas/{bobinado.pk}/asignar/",
                        {"empleado": planta["e_juan"].pk}, format="json")
    planta["jefe"].post(f"/api/v1/tareas/{ensamble.pk}/asignar/",
                        {"empleado": planta["e_pedro"].pk}, format="json")
    assert planta["jefe"].post(f"/api/v1/ordenes-trabajo/{ot.pk}/iniciar/").status_code == 200
    return ot, bobinado, ensamble


def _horas(api, tarea, horas, **extra):
    return api.post(f"/api/v1/tareas/{tarea.pk}/registrar_horas/",
                    {"horas": str(horas), **extra}, format="json")


# ---------------------------------------------------------------------------
# Generacion (CU-OT-01, RN-07)
# ---------------------------------------------------------------------------
def test_generar_copia_tareas_y_pasa_la_oc_a_produccion(planta):
    ot = _generar(planta)

    assert ot.estado.codigo == "planificada"
    assert ot.costo_estimado_uf == Decimal("24")          # (6 + 6) x 2
    horas = list(ot.tareas.order_by("secuencia").values_list("horas_estimadas", flat=True))
    assert horas == [Decimal("16"), Decimal("8")]         # estandar x 2 unidades
    planta["orden"].refresh_from_db()
    assert planta["orden"].estado.codigo == "en_produccion"

    otra_vez = planta["jefe"].post(f"/api/v1/ordenes-compra/{planta['orden'].pk}/"
                                   "generar_ordenes_trabajo/")
    assert otra_vez.status_code == 409


def test_solo_una_oc_confirmada_genera_ot(planta):
    planta["orden"].estado = _estado("orden_compra", "pendiente")
    planta["orden"].save()
    respuesta = planta["jefe"].post(f"/api/v1/ordenes-compra/{planta['orden'].pk}/"
                                    "generar_ordenes_trabajo/")
    assert respuesta.status_code == 409


def test_el_comercial_no_genera_ot_y_el_operario_no_inicia(planta):
    url = f"/api/v1/ordenes-compra/{planta['orden'].pk}/generar_ordenes_trabajo/"
    assert planta["comercial"].post(url).status_code == 403
    ot = _generar(planta)
    assert planta["juan"].post(f"/api/v1/ordenes-trabajo/{ot.pk}/iniciar/").status_code == 403


# ---------------------------------------------------------------------------
# Registro en taller (CU-OT-04, CU-OT-05, RN-09, RN-10)
# ---------------------------------------------------------------------------
def test_operario_registra_horas_en_su_tarea_con_la_tarifa_vigente(planta):
    ot, bobinado, _ = _en_ejecucion(planta)

    assert _horas(planta["juan"], bobinado, 4).status_code == 200
    ot.refresh_from_db()
    assert ot.costo_real_uf == Decimal("2")               # 4 h x 0,5 UF
    assert ot.avance_pct == Decimal("0")                  # ninguna tarea terminada
    bobinado.refresh_from_db()
    assert bobinado.estado == TareaOT.Estado.EN_EJECUCION


def test_operario_no_registra_en_tareas_ajenas_ni_por_otro(planta):
    _, bobinado, _ = _en_ejecucion(planta)
    assert _horas(planta["pedro"], bobinado, 2).status_code == 409
    respuesta = _horas(planta["juan"], bobinado, 2, empleado=planta["e_pedro"].pk)
    assert respuesta.status_code == 409


def test_el_jefe_registra_por_un_ausente(planta):
    _, bobinado, _ = _en_ejecucion(planta)
    respuesta = _horas(planta["jefe"], bobinado, 3, empleado=planta["e_juan"].pk)
    assert respuesta.status_code == 200


def test_tope_de_horas_diarias(planta):
    _, bobinado, _ = _en_ejecucion(planta)
    assert _horas(planta["juan"], bobinado, 10).status_code == 200
    respuesta = _horas(planta["juan"], bobinado, 3)
    assert respuesta.status_code == 409
    assert "maximo" in respuesta.data["detalle"]


def test_consumo_descuenta_stock_y_suma_al_costo(planta):
    ot, bobinado, _ = _en_ejecucion(planta)
    url = f"/api/v1/tareas/{bobinado.pk}/registrar_consumo/"
    datos = {"material": planta["cobre"].pk, "bodega": planta["bodega"].pk, "cantidad": "40"}

    assert planta["juan"].post(url, datos, format="json").status_code == 200
    assert MovimientoInventario.stock_actual(planta["cobre"]) == Decimal("60")
    ot.refresh_from_db()
    assert ot.costo_real_uf == Decimal("8")               # 40 kg x 0,2 UF

    datos["cantidad"] = "70"
    rechazo = planta["juan"].post(url, datos, format="json")
    assert rechazo.status_code == 409
    assert "disponible 60" in rechazo.data["detalle"]


def test_anular_horas_recalcula_y_queda_auditado(planta):
    ot, bobinado, _ = _en_ejecucion(planta)
    _horas(planta["juan"], bobinado, 4)
    registro = bobinado.registros_hora.get()
    url = f"/api/v1/tareas/{bobinado.pk}/anular_horas/"

    assert planta["juan"].post(url, {"registro": registro.pk}, format="json").status_code == 409
    respuesta = planta["juan"].post(url, {"registro": registro.pk, "motivo": "Tarea equivocada"},
                                    format="json")
    assert respuesta.status_code == 200
    ot.refresh_from_db()
    assert ot.costo_real_uf == Decimal("0")
    assert Auditoria.objects.filter(entidad="registro_hora_hombre",
                                    accion="anulacion").exists()


def test_mis_tareas_muestra_solo_las_asignadas(planta):
    _en_ejecucion(planta)
    datos = planta["juan"].get("/api/v1/tareas/?mias=1").data
    tareas = datos.get("results", datos)
    assert [t["nombre"] for t in tareas] == ["Bobinado"]


# ---------------------------------------------------------------------------
# Calidad y cierre (CU-OT-08, RN-12)
# ---------------------------------------------------------------------------
def test_paso_a_calidad_y_cierre_bloqueado_sin_control(planta):
    ot, bobinado, ensamble = _en_ejecucion(planta)
    base = f"/api/v1/ordenes-trabajo/{ot.pk}"

    assert planta["juan"].post(f"/api/v1/tareas/{bobinado.pk}/terminar/").status_code == 409
    assert planta["jefe"].post(f"{base}/enviar_calidad/").status_code == 409

    _horas(planta["juan"], bobinado, 8)
    _horas(planta["pedro"], ensamble, 4)
    assert planta["juan"].post(f"/api/v1/tareas/{bobinado.pk}/terminar/").status_code == 200
    assert planta["pedro"].post(f"/api/v1/tareas/{ensamble.pk}/terminar/").status_code == 200
    assert planta["jefe"].post(f"{base}/enviar_calidad/").status_code == 200

    cierre = planta["jefe"].post(f"{base}/cerrar/", {}, format="json")
    assert cierre.status_code == 409
    assert "control de calidad" in cierre.data["detalle"]
    detalle = planta["jefe"].get(f"{base}/").data
    assert detalle["estado_codigo"] == "en_calidad"
    assert detalle["impedimentos_cierre"]


# ---------------------------------------------------------------------------
# Datos de demostracion
# ---------------------------------------------------------------------------
def test_cargar_demo_produccion_es_repetible(db):
    from io import StringIO

    from apps.inventario.models import Material

    call_command("cargar_estados", verbosity=0)
    call_command("cargar_roles", "--usuarios-demo", verbosity=0)
    salida = StringIO()
    call_command("cargar_demo_produccion", stdout=salida)
    call_command("cargar_demo_produccion", stdout=salida)

    assert Material.objects.count() == 6
    from apps.calidad.models import ProtocoloCalidad

    assert ProtocoloCalidad.objects.count() == 0   # sin modelos de demo no hay protocolos
    assert Empleado.objects.count() == 3
    assert Empleado.objects.get(nombre="Juan Soto").usuario.username == "operario"
    cobre = Material.objects.get(codigo="CU-ESM")
    assert MovimientoInventario.stock_actual(cobre) == Decimal("900")   # una sola recepcion



def test_el_avance_se_mide_por_tareas_terminadas_no_por_horas(planta):
    """Una tarea terminada en menos horas de las estimadas cuenta completa."""
    ot, bobinado, _ = _en_ejecucion(planta)
    _horas(planta["juan"], bobinado, 1)                   # estimadas: 16 h
    planta["juan"].post(f"/api/v1/tareas/{bobinado.pk}/terminar/")

    ot.refresh_from_db()
    assert ot.avance_pct == Decimal("50")                 # 1 de 2 tareas


# ---------------------------------------------------------------------------
# Tareas: responsable habitual, agregar y quitar, modelo sin tareas
# ---------------------------------------------------------------------------
def test_responsable_habitual_se_asigna_al_generar(planta):
    from apps.catalogo.models import TareaEstandarModelo

    TareaEstandarModelo.objects.filter(nombre="Bobinado").update(
        empleado_sugerido=planta["e_juan"])
    ot = _generar(planta)
    bobinado = ot.tareas.get(nombre="Bobinado")
    assert bobinado.empleado == planta["e_juan"]
    assert ot.tareas.get(nombre="Ensamble").empleado is None


def test_modelo_sin_tareas_no_genera_orden_de_trabajo(planta):
    from apps.catalogo.models import TareaEstandarModelo

    TareaEstandarModelo.objects.all().delete()
    respuesta = planta["jefe"].post(f"/api/v1/ordenes-compra/{planta['orden'].pk}/"
                                    "generar_ordenes_trabajo/")
    assert respuesta.status_code == 409
    assert "Materiales y tareas" in respuesta.data["detalle"]


def test_jefe_agrega_y_quita_tareas_de_la_orden(planta):
    ot = _generar(planta)
    base = f"/api/v1/ordenes-trabajo/{ot.pk}"
    agregada = planta["jefe"].post(f"{base}/agregar_tarea/", {
        "nombre": "Pintura", "horas_estimadas": "1.5", "empleado": planta["e_pedro"].pk},
        format="json")
    assert agregada.status_code == 200
    nueva = ot.tareas.get(nombre="Pintura")
    assert nueva.secuencia == 3 and nueva.empleado == planta["e_pedro"]

    quitada = planta["jefe"].post(f"{base}/quitar_tarea/", {"tarea": nueva.pk}, format="json")
    assert quitada.status_code == 200
    assert not ot.tareas.filter(nombre="Pintura").exists()
    assert planta["juan"].post(f"{base}/agregar_tarea/", {"nombre": "X", "horas_estimadas": "1"},
                               format="json").status_code == 403


def test_orden_sin_tareas_carga_las_estandar(planta):
    ot = _generar(planta)
    ot.tareas.all().delete()
    respuesta = planta["jefe"].post(f"/api/v1/ordenes-trabajo/{ot.pk}/cargar_tareas_estandar/")
    assert respuesta.status_code == 200
    assert ot.tareas.count() == 2


# ---------------------------------------------------------------------------
# Generacion automatica al pagarse el anticipo (RN-07)
# ---------------------------------------------------------------------------
def _oc_pendiente_con_anticipo_pagado(planta):
    from apps.pagos.models import DocumentoCobro

    orden = planta["orden"]
    orden.estado = _estado("orden_compra", "pendiente")
    orden.save(update_fields=["estado"])
    documento = DocumentoCobro.objects.create(
        numero="ANT-2026-0001", orden_compra=orden, tipo=DocumentoCobro.Tipo.ANTICIPO,
        estado=DocumentoCobro.Estado.PAGADO, monto_uf=Decimal("25"),
        valor_uf=Decimal("40000"), monto_clp=Decimal("1000000"),
        vence_el=HOY + datetime.timedelta(days=10),
    )
    return orden, documento


def test_pagar_anticipo_genera_las_ot_automaticamente(planta):
    from apps.comercial import services as comercial

    orden, documento = _oc_pendiente_con_anticipo_pagado(planta)
    usuario = Usuario.objects.get(username="comercial")

    comercial.confirmar_si_anticipo(documento, usuario)

    orden.refresh_from_db()
    assert orden.estado.codigo == "en_produccion"
    ot = OrdenTrabajo.objects.get(orden_compra=orden)
    assert ot.estado.codigo == "planificada"
    assert ot.tareas.count() == 2


def test_sin_tareas_estandar_la_oc_queda_confirmada(planta):
    from apps.comercial import services as comercial

    orden, documento = _oc_pendiente_con_anticipo_pagado(planta)
    TareaEstandarModelo.objects.all().delete()

    comercial.confirmar_si_anticipo(documento, Usuario.objects.get(username="comercial"))

    orden.refresh_from_db()
    assert orden.estado.codigo == "confirmada"     # el pago no se pierde
    assert not OrdenTrabajo.objects.exists()       # se generan a mano desde escritorio
