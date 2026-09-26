"""
Pruebas del dominio de ejecucion productiva.

Verifican el costeo real contra el estimado (RN-11), la valorizacion de horas
hombre con la tarifa vigente (RN-10) y el bloqueo de cierre por calidad
(RN-12), que son las reglas que distinguen a SITRAFO de un sistema de venta.
"""
import datetime
from decimal import Decimal

import pytest

from apps.calidad.models import (
    ControlCalidad,
    NoConformidad,
    ProtocoloCalidad,
    PuntoControl,
    ResultadoControl,
)
from apps.catalogo.models import FamiliaProducto, ModeloProducto
from apps.clientes.models import Cliente
from apps.comercial.models import Cotizacion, EstadoDocumento, OrdenCompra, SolicitudPresupuesto
from apps.inventario.models import Bodega, CategoriaMaterial, Material, MovimientoInventario
from apps.produccion.models import (
    ConsumoMaterial,
    Empleado,
    OrdenTrabajo,
    RegistroHoraHombre,
    TareaOT,
    TarifaHoraHombre,
)


@pytest.fixture
def taller(db, django_user_model):
    usuario = django_user_model.objects.create_user(
        "jefe", "j@j.cl", "Clave12345", es_interno=True
    )
    cliente = Cliente.objects.create(
        rut="76543210-3", razon_social="Electrica del Maipo", tipo_persona="juridica"
    )
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    modelo = ModeloProducto.objects.create(
        familia=familia, codigo="TD-100", nombre="Transformador 100 kVA"
    )
    categoria = CategoriaMaterial.objects.create(nombre="Nucleo")
    material = Material.objects.create(
        categoria=categoria, codigo="ACE-001", nombre="Acero al silicio",
        unidad_medida="kg", stock_minimo=Decimal("100"),
    )
    bodega = Bodega.objects.create(codigo="B1", nombre="Bodega central")

    e_sol = EstadoDocumento.objects.create(
        tipo_documento="solicitud", codigo="recibida", nombre="Recibida"
    )
    e_cot = EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="aceptada", nombre="Aceptada"
    )
    e_oc = EstadoDocumento.objects.create(
        tipo_documento="orden_compra", codigo="confirmada", nombre="Confirmada"
    )
    e_ot = EstadoDocumento.objects.create(
        tipo_documento="orden_trabajo", codigo="en_ejecucion", nombre="En ejecucion"
    )

    solicitud = SolicitudPresupuesto.objects.create(
        numero="SP-1", cliente=cliente, modelo=modelo, cantidad=1, estado=e_sol
    )
    cotizacion = Cotizacion.objects.create(
        numero="COT-1", solicitud=solicitud, cliente=cliente, estado=e_cot,
        ejecutivo=usuario, valor_uf=Decimal("40000"),
        fecha_valor_uf=datetime.date(2026, 9, 23),
        vence_el=datetime.date(2026, 10, 23), total_uf=Decimal("50"),
    )
    orden_compra = OrdenCompra.objects.create(
        numero="OC-1", cotizacion=cotizacion, cliente=cliente, estado=e_oc,
        total_uf=Decimal("50"),
    )
    ot = OrdenTrabajo.objects.create(
        numero="OT-1", orden_compra=orden_compra, modelo=modelo, cantidad=1,
        estado=e_ot, costo_estimado_uf=Decimal("40"),
    )
    empleado = Empleado.objects.create(
        rut="20221980-2", nombre="Operario Perez", cargo="Bobinador"
    )
    TarifaHoraHombre.objects.create(
        empleado=empleado, valor_hora_uf=Decimal("0.2000"),
        vigente_desde=datetime.date(2026, 1, 1),
    )
    return {
        "usuario": usuario, "modelo": modelo, "material": material,
        "bodega": bodega, "ot": ot, "empleado": empleado,
    }


# ---------------------------------------------------------------------------
# Tarifas e inventario
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_tarifa_vigente_a_una_fecha(taller):
    """RN-10: se aplica la tarifa vigente a la fecha del registro."""
    TarifaHoraHombre.objects.create(
        empleado=taller["empleado"], valor_hora_uf=Decimal("0.2500"),
        vigente_desde=datetime.date(2026, 7, 1),
    )

    antigua = taller["empleado"].tarifa_vigente_a(datetime.date(2026, 3, 1))
    nueva = taller["empleado"].tarifa_vigente_a(datetime.date(2026, 9, 1))

    assert antigua.valor_hora_uf == Decimal("0.2000")
    assert nueva.valor_hora_uf == Decimal("0.2500")


@pytest.mark.django_db
def test_stock_se_calcula_por_agregacion(taller):
    """El saldo no se almacena: se obtiene de movimiento_inventario."""
    MovimientoInventario.objects.create(
        material=taller["material"], bodega=taller["bodega"], tipo="recepcion",
        cantidad=Decimal("500"), costo_unitario_uf=Decimal("0.085"),
        usuario=taller["usuario"],
    )
    MovimientoInventario.objects.create(
        material=taller["material"], bodega=taller["bodega"], tipo="consumo",
        cantidad=Decimal("-320"), costo_unitario_uf=Decimal("0.085"),
        usuario=taller["usuario"],
    )

    assert MovimientoInventario.stock_actual(taller["material"]) == Decimal("180")


# ---------------------------------------------------------------------------
# Costeo real
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_costo_real_suma_materiales_y_horas(taller):
    """RN-11."""
    tarea = TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Bobinado", secuencia=1,
        horas_estimadas=Decimal("24"),
    )
    ConsumoMaterial.objects.create(
        tarea=tarea, material=taller["material"], bodega=taller["bodega"],
        cantidad=Decimal("320"), costo_unitario_uf=Decimal("0.085"),
        empleado=taller["empleado"],
    )
    RegistroHoraHombre.objects.create(
        tarea=tarea, empleado=taller["empleado"], fecha=datetime.date(2026, 9, 20),
        horas=Decimal("26"), valor_hora_uf=Decimal("0.2000"),
        usuario_registro=taller["usuario"],
    )

    assert taller["ot"].costo_materiales_uf == Decimal("27.200")
    assert taller["ot"].costo_hh_uf == Decimal("5.20000")
    assert taller["ot"].recalcular_costo_real() == Decimal("32.4000")


@pytest.mark.django_db
def test_desviacion_sobre_el_umbral_exige_justificacion(taller):
    tarea = TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Bobinado", secuencia=1,
        horas_estimadas=Decimal("24"),
    )
    ConsumoMaterial.objects.create(
        tarea=tarea, material=taller["material"], bodega=taller["bodega"],
        cantidad=Decimal("320"), costo_unitario_uf=Decimal("0.085"),
        empleado=taller["empleado"],
    )
    taller["ot"].recalcular_costo_real()

    assert taller["ot"].desviacion_uf == Decimal("-12.8000")
    assert taller["ot"].desviacion_requiere_justificacion is True


@pytest.mark.django_db
def test_registro_anulado_no_suma_al_costo(taller):
    """RN-13: la correccion se hace por anulacion, no por modificacion."""
    tarea = TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Bobinado", secuencia=1,
        horas_estimadas=Decimal("24"),
    )
    RegistroHoraHombre.objects.create(
        tarea=tarea, empleado=taller["empleado"], fecha=datetime.date(2026, 9, 20),
        horas=Decimal("26"), valor_hora_uf=Decimal("0.2000"),
        anulado=True, usuario_registro=taller["usuario"],
    )

    assert taller["ot"].costo_hh_uf == Decimal("0")


@pytest.mark.django_db
def test_avance_se_calcula_sobre_tareas_terminadas(taller):
    """Las horas consumidas no mueven el avance; terminar tareas si."""
    bobinado = TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Bobinado", secuencia=1,
        horas_estimadas=Decimal("20"),
    )
    TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Ensamble", secuencia=2,
        horas_estimadas=Decimal("10"),
    )
    RegistroHoraHombre.objects.create(
        tarea=bobinado, empleado=taller["empleado"], fecha=datetime.date(2026, 9, 20),
        horas=Decimal("10"), valor_hora_uf=Decimal("0.2000"),
        usuario_registro=taller["usuario"],
    )
    assert taller["ot"].recalcular_avance() == Decimal("0.00")

    bobinado.estado = TareaOT.Estado.TERMINADA
    bobinado.save()
    assert taller["ot"].recalcular_avance() == Decimal("50.00")


# ---------------------------------------------------------------------------
# Cierre condicionado por calidad
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_no_cierra_con_tareas_pendientes(taller):
    """RN-12."""
    TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Bobinado", secuencia=1,
        horas_estimadas=Decimal("24"),
    )

    puede, impedimentos = taller["ot"].puede_cerrarse()

    assert puede is False
    assert any("tarea" in i for i in impedimentos)


@pytest.mark.django_db
def test_punto_de_control_evalua_la_tolerancia(taller):
    """RF-CAL-03: la conformidad se determina automaticamente."""
    protocolo = ProtocoloCalidad.objects.create(
        modelo=taller["modelo"], nombre="Ensayos de rutina"
    )
    punto = PuntoControl.objects.create(
        protocolo=protocolo, nombre="Relacion de transformacion",
        tipo_ensayo="electrico", unidad="ratio", valor_esperado=Decimal("20"),
        tolerancia_inf=Decimal("19.9"), tolerancia_sup=Decimal("20.1"),
        obligatorio=True, secuencia=1,
    )
    control = ControlCalidad.objects.create(
        orden_trabajo=taller["ot"], protocolo=protocolo, inspector=taller["usuario"]
    )

    dentro = ResultadoControl.objects.create(
        control=control, punto=punto, valor_medido=Decimal("20.0")
    )
    fuera = ResultadoControl.objects.create(
        control=control, punto=punto, valor_medido=Decimal("20.4")
    )

    assert dentro.conforme is True
    assert fuera.conforme is False


@pytest.mark.django_db
def test_no_cierra_con_no_conformidad_abierta(taller):
    """RN-12: la no conformidad abierta bloquea el cierre."""
    TareaOT.objects.create(
        orden_trabajo=taller["ot"], nombre="Bobinado", secuencia=1,
        horas_estimadas=Decimal("24"), estado="terminada",
    )
    protocolo = ProtocoloCalidad.objects.create(
        modelo=taller["modelo"], nombre="Ensayos de rutina"
    )
    punto = PuntoControl.objects.create(
        protocolo=protocolo, nombre="Rigidez dielectrica", tipo_ensayo="electrico",
        unidad="kV", tolerancia_inf=Decimal("30"), obligatorio=True, secuencia=1,
    )
    control = ControlCalidad.objects.create(
        orden_trabajo=taller["ot"], protocolo=protocolo, inspector=taller["usuario"]
    )
    resultado = ResultadoControl.objects.create(
        control=control, punto=punto, valor_medido=Decimal("25")
    )
    nc = NoConformidad.objects.create(
        resultado=resultado, descripcion="Rigidez bajo el minimo",
        severidad="mayor", responsable=taller["usuario"],
    )

    puede, impedimentos = taller["ot"].puede_cerrarse()
    assert puede is False
    assert any("conformidad" in i for i in impedimentos)

    nc.cerrar(taller["usuario"], "Resecado del aislamiento y reensayo")
    puede, impedimentos = taller["ot"].puede_cerrarse()

    assert puede is True
    assert impedimentos == []
    assert nc.cerrada_en is not None
