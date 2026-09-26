"""
Servicios de la ejecucion productiva (CU-OT-01 a CU-OT-08).

Concentran las reglas del taller para que la API, la aplicacion de
escritorio y cualquier otra interfaz apliquen exactamente lo mismo:

- RN-07: la orden de trabajo solo nace de una orden de compra confirmada.
- RN-09: el consumo de material descuenta stock mediante un movimiento de
  inventario y no puede dejar el saldo negativo.
- RN-10: las horas se valorizan con la tarifa vigente del empleado a la
  fecha trabajada, y ese valor queda congelado en el registro.
- RN-11: el costo real se consolida en cada registro; al cerrar, una
  desviacion sobre el umbral exige justificacion.
- RN-12: no se cierra una orden con tareas o controles pendientes, ni con no
  conformidades abiertas.
- RN-13: un registro de horas no se corrige ni se borra: se anula.
"""
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.comercial.models import EstadoDocumento, OrdenCompraHistorial
from apps.configuracion.models import ParametroSistema
from apps.inventario.models import MovimientoInventario
from apps.seguridad.models import Auditoria

from .models import (
    ConsumoMaterial,
    OrdenTrabajo,
    OrdenTrabajoHistorial,
    RegistroHoraHombre,
    TareaOT,
)


class ErrorProduccion(Exception):
    """Regla de negocio que impide la operacion productiva."""


def _numero(valor: Decimal) -> str:
    """Decimal legible, sin notacion cientifica ni ceros sobrantes."""
    texto = format(valor.normalize(), "f")
    return texto.rstrip("0").rstrip(".") if "." in texto else texto


def _estado(tipo: str, codigo: str) -> EstadoDocumento:
    return EstadoDocumento.objects.get(tipo_documento=tipo, codigo=codigo)


def _cambiar_estado_ot(ot: OrdenTrabajo, codigo: str, usuario, observacion: str):
    anterior = ot.estado
    ot.estado = _estado("orden_trabajo", codigo)
    ot.save(update_fields=["estado"])
    OrdenTrabajoHistorial.objects.create(
        orden_trabajo=ot, estado_anterior=anterior, estado_nuevo=ot.estado,
        usuario=usuario, observacion=observacion,
    )


def _exigir_estado(ot: OrdenTrabajo, *codigos: str, accion: str):
    if ot.estado.codigo not in codigos:
        raise ErrorProduccion(
            f"La orden {ot.numero} esta {ot.estado.nombre.lower()}: no se puede {accion}."
        )


# ----------------------------------------------------------------------
# Generacion y planificacion (CU-OT-01, CU-OT-02, CU-OT-03)
# ----------------------------------------------------------------------
@transaction.atomic
def generar_ordenes_trabajo(orden_compra, usuario) -> list[OrdenTrabajo]:
    """
    Genera una orden de trabajo por cada linea de la orden de compra.

    Las tareas se copian de las tareas estandar del modelo, con las horas
    multiplicadas por la cantidad. El costo estimado se toma de la linea de
    cotizacion, que es el termino de comparacion del costo real (RN-11).
    """
    if orden_compra.estado.codigo != "confirmada":
        raise ErrorProduccion(
            "Solo una orden de compra confirmada origina ordenes de trabajo (RN-07)."
        )
    if orden_compra.ordenes_trabajo.exists():
        raise ErrorProduccion(f"La orden {orden_compra.numero} ya tiene ordenes de trabajo.")

    planificada = _estado("orden_trabajo", "planificada")
    creadas = []
    for linea in orden_compra.lineas.select_related("cotizacion_linea__modelo"):
        origen = linea.cotizacion_linea
        ot = OrdenTrabajo.objects.create(
            numero=OrdenTrabajo.generar_numero(),
            orden_compra=orden_compra,
            modelo=origen.modelo,
            cantidad=linea.cantidad,
            estado=planificada,
            costo_estimado_uf=(origen.costo_estimado_uf * linea.cantidad).quantize(
                Decimal("0.0001")
            ),
        )
        for tarea in origen.modelo.tareas_estandar.order_by("secuencia"):
            TareaOT.objects.create(
                orden_trabajo=ot, nombre=tarea.nombre, secuencia=tarea.secuencia,
                horas_estimadas=tarea.horas_estimadas * linea.cantidad,
            )
        OrdenTrabajoHistorial.objects.create(
            orden_trabajo=ot, estado_nuevo=planificada, usuario=usuario,
            observacion=f"Generada desde la orden de compra {orden_compra.numero}.",
        )
        creadas.append(ot)

    anterior = orden_compra.estado
    orden_compra.estado = _estado("orden_compra", "en_produccion")
    orden_compra.save(update_fields=["estado"])
    OrdenCompraHistorial.objects.create(
        orden_compra=orden_compra, estado_anterior=anterior,
        estado_nuevo=orden_compra.estado, usuario=usuario,
        observacion=f"{len(creadas)} orden(es) de trabajo generada(s).",
    )
    return creadas


def asignar_empleado(tarea: TareaOT, empleado) -> TareaOT:
    _exigir_estado(tarea.orden_trabajo, "planificada", "en_ejecucion", accion="asignar")
    if tarea.estado == TareaOT.Estado.TERMINADA:
        raise ErrorProduccion("La tarea ya esta terminada.")
    if not empleado.activo:
        raise ErrorProduccion(f"{empleado.nombre} no esta activo.")
    tarea.empleado = empleado
    tarea.save(update_fields=["empleado"])
    return tarea


@transaction.atomic
def iniciar(ot: OrdenTrabajo, usuario) -> OrdenTrabajo:
    _exigir_estado(ot, "planificada", accion="iniciar")
    if not ot.tareas.exists():
        raise ErrorProduccion("La orden no tiene tareas planificadas.")
    ot.fecha_inicio = timezone.localdate()
    ot.save(update_fields=["fecha_inicio"])
    _cambiar_estado_ot(ot, "en_ejecucion", usuario, "Inicio de fabricacion en taller.")
    return ot


# ----------------------------------------------------------------------
# Registro en taller (CU-OT-04, CU-OT-05, CU-OT-06)
# ----------------------------------------------------------------------
def puede_registrar_en(tarea: TareaOT, usuario) -> bool:
    """
    El operario registra solo en las tareas que tiene asignadas; quien puede
    planificar (jefe de produccion) registra en cualquiera, por ejemplo por
    un empleado ausente.
    """
    if usuario.is_superuser or usuario.has_perm("orden_trabajo.actualizar"):
        return True
    empleado = getattr(usuario, "empleado", None)
    return empleado is not None and tarea.empleado_id == empleado.pk


def _exigir_registrable(tarea: TareaOT, usuario):
    _exigir_estado(tarea.orden_trabajo, "en_ejecucion", accion="registrar trabajo")
    if tarea.estado == TareaOT.Estado.TERMINADA:
        raise ErrorProduccion("La tarea ya esta terminada.")
    if not puede_registrar_en(tarea, usuario):
        raise ErrorProduccion("Solo puede registrar en las tareas que tiene asignadas.")


def _max_horas_diarias() -> Decimal:
    return Decimal(str(ParametroSistema.obtener(
        "produccion.max_horas_diarias", settings.SITRAFO["MAX_HORAS_DIARIAS"]
    )))


def _consolidar(ot: OrdenTrabajo):
    ot.recalcular_costo_real()
    ot.recalcular_avance()


@transaction.atomic
def registrar_horas(tarea: TareaOT, empleado, fecha, horas: Decimal, usuario
                    ) -> RegistroHoraHombre:
    """Registra horas valorizadas con la tarifa vigente a la fecha (RN-10)."""
    _exigir_registrable(tarea, usuario)
    horas = Decimal(str(horas))
    if horas <= 0:
        raise ErrorProduccion("Las horas deben ser mayores que cero.")
    if fecha > timezone.localdate():
        raise ErrorProduccion("No se pueden registrar horas futuras.")

    maximo = _max_horas_diarias()
    del_dia = RegistroHoraHombre.objects.filter(
        empleado=empleado, fecha=fecha, anulado=False
    ).aggregate(t=Sum("horas"))["t"] or Decimal("0")
    if del_dia + horas > maximo:
        raise ErrorProduccion(
            f"{empleado.nombre} ya tiene {_numero(del_dia)} h el {fecha:%d-%m-%Y}; "
            f"el maximo es {_numero(maximo)} h diarias."
        )

    tarifa = empleado.tarifa_vigente_a(fecha)
    if tarifa is None:
        raise ErrorProduccion(
            f"{empleado.nombre} no tiene tarifa vigente al {fecha:%d-%m-%Y}."
        )

    registro = RegistroHoraHombre.objects.create(
        tarea=tarea, empleado=empleado, fecha=fecha, horas=horas,
        valor_hora_uf=tarifa.valor_hora_uf, usuario_registro=usuario,
    )
    if tarea.estado == TareaOT.Estado.PENDIENTE:
        tarea.estado = TareaOT.Estado.EN_EJECUCION
        tarea.save(update_fields=["estado"])
    _consolidar(tarea.orden_trabajo)
    return registro


@transaction.atomic
def anular_horas(registro: RegistroHoraHombre, usuario, motivo: str) -> RegistroHoraHombre:
    """Correccion por anulacion, nunca por edicion ni borrado (RN-13)."""
    if registro.anulado:
        raise ErrorProduccion("El registro ya esta anulado.")
    if not motivo.strip():
        raise ErrorProduccion("Indique el motivo de la anulacion.")
    _exigir_estado(registro.tarea.orden_trabajo, "en_ejecucion", accion="anular horas")
    registro.anulado = True
    registro.save(update_fields=["anulado"])
    Auditoria.objects.create(
        usuario=usuario, entidad="registro_hora_hombre", id_registro=str(registro.pk),
        accion=Auditoria.Accion.ANULACION,
        valor_anterior={"horas": str(registro.horas), "anulado": False},
        valor_nuevo={"anulado": True, "motivo": motivo.strip()},
        origen=Auditoria.Origen.ESCRITORIO,
    )
    _consolidar(registro.tarea.orden_trabajo)
    return registro


@transaction.atomic
def registrar_consumo(tarea: TareaOT, material, bodega, cantidad: Decimal,
                      empleado, usuario) -> ConsumoMaterial:
    """
    Registra el consumo y descuenta el stock en el mismo hecho (RN-09).

    Rechaza el consumo si no hay stock suficiente en la bodega, informando el
    saldo disponible. El costo unitario se congela con el precio vigente.
    """
    _exigir_registrable(tarea, usuario)
    cantidad = Decimal(str(cantidad))
    if cantidad <= 0:
        raise ErrorProduccion("La cantidad debe ser mayor que cero.")

    disponible = MovimientoInventario.stock_actual(material, bodega)
    if cantidad > disponible:
        raise ErrorProduccion(
            f"Stock insuficiente de {material.nombre} en {bodega.nombre}: "
            f"disponible {_numero(disponible)} {material.unidad_medida}."
        )

    costo = material.costo_vigente
    if costo is None:
        raise ErrorProduccion(f"{material.nombre} no tiene precio de compra vigente.")

    planificado = tarea.orden_trabajo.modelo.materiales.filter(material=material).exists()
    consumo = ConsumoMaterial.objects.create(
        tarea=tarea, material=material, bodega=bodega, cantidad=cantidad,
        costo_unitario_uf=costo, planificado=planificado, empleado=empleado,
    )
    MovimientoInventario.objects.create(
        material=material, bodega=bodega, tipo=MovimientoInventario.Tipo.CONSUMO,
        cantidad=-cantidad, costo_unitario_uf=costo, consumo=consumo, usuario=usuario,
        observacion=f"{tarea.orden_trabajo.numero} / {tarea.nombre}",
    )
    if tarea.estado == TareaOT.Estado.PENDIENTE:
        tarea.estado = TareaOT.Estado.EN_EJECUCION
        tarea.save(update_fields=["estado"])
    _consolidar(tarea.orden_trabajo)
    return consumo


def terminar_tarea(tarea: TareaOT, usuario) -> TareaOT:
    _exigir_registrable(tarea, usuario)
    if not tarea.registros_hora.filter(anulado=False).exists():
        raise ErrorProduccion("Registre al menos las horas trabajadas antes de terminar.")
    tarea.estado = TareaOT.Estado.TERMINADA
    tarea.save(update_fields=["estado"])
    tarea.orden_trabajo.recalcular_avance()
    return tarea


# ----------------------------------------------------------------------
# Paso a calidad y cierre (CU-OT-07, CU-OT-08)
# ----------------------------------------------------------------------
@transaction.atomic
def enviar_a_calidad(ot: OrdenTrabajo, usuario) -> OrdenTrabajo:
    _exigir_estado(ot, "en_ejecucion", accion="enviar a calidad")
    pendientes = ot.tareas_pendientes.count()
    if pendientes:
        raise ErrorProduccion(f"Quedan {pendientes} tarea(s) sin terminar.")
    _cambiar_estado_ot(ot, "en_calidad", usuario, "Fabricacion terminada; pasa a control de calidad.")
    return ot


@transaction.atomic
def cerrar(ot: OrdenTrabajo, usuario, justificacion: str = "") -> OrdenTrabajo:
    """Cierra la orden verificando calidad (RN-12) y desviacion de costo (RN-11)."""
    _exigir_estado(ot, "en_calidad", accion="cerrar")
    puede, impedimentos = ot.puede_cerrarse()
    if not puede:
        raise ErrorProduccion("No se puede cerrar: " + " ".join(impedimentos))

    ot.recalcular_costo_real()
    if ot.desviacion_requiere_justificacion and not justificacion.strip():
        raise ErrorProduccion(
            f"El costo real se desvia {ot.desviacion_pct}% del estimado: "
            "debe justificar la desviacion para cerrar (RN-11)."
        )

    ot.fecha_cierre = timezone.localdate()
    ot.save(update_fields=["fecha_cierre"])
    observacion = "Orden cerrada."
    if justificacion.strip():
        observacion += f" Desviacion justificada: {justificacion.strip()}"
    _cambiar_estado_ot(ot, "cerrada", usuario, observacion)

    # Si era la ultima orden de trabajo de la compra, se cobra el saldo
    from apps.pagos.services.cobros import ErrorCobro, emitir_saldo

    try:
        emitir_saldo(ot.orden_compra)
    except ErrorCobro:
        pass   # sin UF: se emite despues con el comando emitir_cobros
    return ot
