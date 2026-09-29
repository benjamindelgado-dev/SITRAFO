"""
Servicios del proceso comercial.

Concentran las reglas para elaborar una cotizacion desde una solicitud
(CU-COM-03 a CU-COM-06), de modo que la API y cualquier interfaz que la use
(la aplicacion de escritorio) apliquen exactamente las mismas reglas.

Costeo (RF-COM-04):
- Materiales: lista de materiales del modelo (bom_modelo) valorizada con el
  costo vigente de cada material.
- Horas hombre: horas estandar del modelo (tarea_estandar_modelo) por la
  tarifa de referencia, que es el promedio de las tarifas vigentes de los
  empleados activos.
- Precio sugerido: costo estimado mas el margen. Si el modelo aun no tiene
  costeo cargado, se sugiere el precio base del catalogo. El ejecutivo puede
  ajustar el precio antes de crear la cotizacion.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import Avg, Q
from django.utils import timezone

from apps.configuracion.models import ParametroSistema
from apps.configuracion.services.feriados import plazo_en_dias_habiles
from apps.configuracion.services.indicadores import valor_uf

from .models import (
    Cotizacion,
    CotizacionHistorial,
    CotizacionLinea,
    EstadoDocumento,
    OrdenCompraHistorial,
    SolicitudHistorial,
)

CUATRO = Decimal("0.0001")
PLAZO_DEFECTO_DIAS_HABILES = 30


class ErrorComercial(Exception):
    """Regla de negocio que impide la operacion comercial."""


@dataclass
class Costeo:
    costo_material_uf: Decimal
    costo_hh_uf: Decimal
    horas_estandar: Decimal
    tarifa_referencia_uf: Decimal | None
    margen_pct: Decimal
    precio_base_uf: Decimal | None
    precio_sugerido_uf: Decimal | None
    origen_precio: str  # "costeo", "precio_base" o "sin_precio"

    @property
    def costo_estimado_uf(self) -> Decimal:
        return self.costo_material_uf + self.costo_hh_uf


def tarifa_referencia_uf() -> Decimal | None:
    """Promedio de las tarifas de hora hombre vigentes de empleados activos."""
    from apps.produccion.models import TarifaHoraHombre

    hoy = timezone.localdate()
    promedio = TarifaHoraHombre.objects.filter(
        empleado__activo=True, vigente_desde__lte=hoy,
    ).filter(
        Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)
    ).aggregate(p=Avg("valor_hora_uf"))["p"]
    return Decimal(promedio).quantize(CUATRO) if promedio else None


def margen_defecto() -> Decimal:
    return Decimal(str(ParametroSistema.obtener("comercial.margen_defecto_pct", 25)))


def costear_modelo(modelo, margen_pct: Decimal | None = None) -> Costeo:
    """Costo unitario estimado de un modelo y precio sugerido (RF-COM-04)."""
    margen = margen_defecto() if margen_pct is None else Decimal(str(margen_pct))

    material = Decimal("0")
    for item in modelo.materiales.select_related("material"):
        costo = item.material.costo_vigente
        if costo:
            material += item.cantidad * costo

    horas = Decimal(str(modelo.horas_estandar_totales or 0))
    tarifa = tarifa_referencia_uf()
    hh = horas * tarifa if tarifa else Decimal("0")

    costo = (material + hh).quantize(CUATRO)
    precio_base = modelo.precio_vigente
    if costo > 0:
        sugerido = (costo * (1 + margen / 100)).quantize(CUATRO)
        origen = "costeo"
    elif precio_base:
        sugerido, origen = Decimal(precio_base), "precio_base"
    else:
        sugerido, origen = None, "sin_precio"

    return Costeo(
        costo_material_uf=material.quantize(CUATRO),
        costo_hh_uf=hh.quantize(CUATRO),
        horas_estandar=horas,
        tarifa_referencia_uf=tarifa,
        margen_pct=margen,
        precio_base_uf=precio_base,
        precio_sugerido_uf=sugerido,
        origen_precio=origen,
    )


def _estado(tipo: str, codigo: str) -> EstadoDocumento:
    return EstadoDocumento.objects.get(tipo_documento=tipo, codigo=codigo)


@transaction.atomic
def cotizar_solicitud(
    solicitud,
    usuario,
    *,
    precio_uf: Decimal | None = None,
    margen_pct: Decimal | None = None,
    descuento_pct: Decimal = Decimal("0"),
    plazo_dias_habiles: int | None = None,
) -> Cotizacion:
    """
    Crea la cotizacion en borrador a partir de una solicitud (CU-COM-03).

    - Congela el valor de la UF del dia (RN-03).
    - Calcula el vencimiento y la fecha de entrega en dias habiles (RN-08).
    - Deja la solicitud en estado cotizada, con su historial.
    """
    if solicitud.estado.codigo not in ("recibida", "asignada"):
        raise ErrorComercial(
            f"La solicitud {solicitud.numero} esta {solicitud.estado.nombre.lower()} "
            "y no admite una nueva cotizacion."
        )
    if solicitud.modelo is None:
        raise ErrorComercial("La solicitud no indica un modelo del catalogo.")

    costeo = costear_modelo(solicitud.modelo, margen_pct)
    precio = Decimal(str(precio_uf)) if precio_uf is not None else costeo.precio_sugerido_uf
    if not precio or precio <= 0:
        raise ErrorComercial(
            "El modelo no tiene costeo ni precio base: indique el precio unitario."
        )

    uf, fecha_uf, _ = valor_uf()
    if uf is None:
        raise ErrorComercial("No hay valor de UF disponible. Sincronice los indicadores.")

    hoy = timezone.localdate()
    plazo = plazo_dias_habiles or PLAZO_DEFECTO_DIAS_HABILES
    entrega, _ = plazo_en_dias_habiles(hoy, plazo)
    vigencia = int(ParametroSistema.obtener("comercial.vigencia_cotizacion_dias", 30))

    borrador = _estado("cotizacion", "borrador")
    cotizacion = Cotizacion.objects.create(
        numero=Cotizacion.generar_numero(),
        solicitud=solicitud,
        cliente=solicitud.cliente,
        estado=borrador,
        ejecutivo=usuario,
        valor_uf=uf,
        fecha_valor_uf=fecha_uf,
        descuento_pct=Decimal(str(descuento_pct or 0)),
        plazo_dias_habiles=plazo,
        fecha_entrega=entrega,
        vence_el=Cotizacion.calcular_vencimiento(hoy, vigencia),
    )
    CotizacionLinea.objects.create(
        cotizacion=cotizacion,
        modelo=solicitud.modelo,
        cantidad=solicitud.cantidad,
        costo_material_uf=costeo.costo_material_uf,
        costo_hh_uf=costeo.costo_hh_uf,
        margen_pct=costeo.margen_pct,
        precio_uf=precio.quantize(CUATRO),
    )
    cotizacion.recalcular_total()
    CotizacionHistorial.objects.create(
        cotizacion=cotizacion, estado_nuevo=borrador, usuario=usuario,
        observacion=f"Elaborada desde la solicitud {solicitud.numero}.",
    )

    anterior = solicitud.estado
    solicitud.estado = _estado("solicitud", "cotizada")
    if solicitud.ejecutivo_id is None:
        solicitud.ejecutivo = usuario
    solicitud.save(update_fields=["estado", "ejecutivo"])
    SolicitudHistorial.objects.create(
        solicitud=solicitud, estado_anterior=anterior, estado_nuevo=solicitud.estado,
        usuario=usuario, observacion=f"Cotizada en {cotizacion.numero}.",
    )
    return cotizacion


# ----------------------------------------------------------------------
# Anulacion de documentos (RF-COM-15, RN-13, RN-14)
# ----------------------------------------------------------------------
def _motivo_valido(motivo: str) -> str:
    motivo = (motivo or "").strip()
    if len(motivo) < 10:
        raise ErrorComercial("Indique el motivo de la anulacion (al menos 10 caracteres).")
    return motivo[:300]


def _auditar_anulacion(usuario, entidad, documento, anterior, motivo):
    from apps.seguridad.models import Auditoria

    Auditoria.objects.create(
        usuario=usuario, entidad=entidad, id_registro=str(documento.pk),
        accion=Auditoria.Accion.ANULACION,
        valor_anterior={"numero": documento.numero, "estado": anterior},
        valor_nuevo={"estado": documento.estado.codigo, "motivo": motivo},
        origen=Auditoria.Origen.ESCRITORIO,
    )


@transaction.atomic
def anular_solicitud(solicitud, usuario, motivo: str):
    """
    La solicitud se desestima (su estado de anulacion). Si ya tiene una
    cotizacion vigente, primero debe anularse esa cotizacion.
    """
    motivo = _motivo_valido(motivo)
    if solicitud.estado.es_final:
        raise ErrorComercial(f"La solicitud ya esta {solicitud.estado.nombre.lower()}.")
    vigentes = solicitud.cotizaciones.exclude(
        estado__codigo__in=["anulada", "rechazada", "vencida"])
    if vigentes.exists():
        raise ErrorComercial(
            f"La solicitud tiene la cotizacion {vigentes.first().numero} vigente: "
            "anulela primero."
        )
    anterior = solicitud.estado
    solicitud.estado = _estado("solicitud", "desestimada")
    solicitud.save(update_fields=["estado"])
    SolicitudHistorial.objects.create(
        solicitud=solicitud, estado_anterior=anterior, estado_nuevo=solicitud.estado,
        usuario=usuario, observacion=f"Desestimada: {motivo}",
    )
    _auditar_anulacion(usuario, "solicitud_presupuesto", solicitud, anterior.codigo, motivo)
    return solicitud


@transaction.atomic
def anular_cotizacion(cotizacion, usuario, motivo: str):
    """Una cotizacion con orden de compra no se anula: se anula la orden."""
    motivo = _motivo_valido(motivo)
    if cotizacion.estado.codigo in ("anulada", "rechazada", "vencida"):
        raise ErrorComercial(f"La cotizacion ya esta {cotizacion.estado.nombre.lower()}.")
    if cotizacion.ordenes_compra.exclude(estado__codigo="anulada").exists():
        raise ErrorComercial("La cotizacion ya origino una orden de compra: anule la orden.")
    anterior = cotizacion.estado
    cotizacion.estado = _estado("cotizacion", "anulada")
    cotizacion.save(update_fields=["estado"])
    CotizacionHistorial.objects.create(
        cotizacion=cotizacion, estado_anterior=anterior, estado_nuevo=cotizacion.estado,
        usuario=usuario, observacion=f"Anulada: {motivo}",
    )
    # La solicitud vuelve a quedar disponible para cotizar de nuevo
    solicitud = cotizacion.solicitud
    if solicitud.estado.codigo == "cotizada":
        estado_sol = solicitud.estado
        solicitud.estado = _estado("solicitud", "asignada")
        solicitud.save(update_fields=["estado"])
        SolicitudHistorial.objects.create(
            solicitud=solicitud, estado_anterior=estado_sol, estado_nuevo=solicitud.estado,
            usuario=usuario, observacion=f"Cotizacion {cotizacion.numero} anulada.",
        )
    _auditar_anulacion(usuario, "cotizacion", cotizacion, anterior.codigo, motivo)
    return cotizacion


@transaction.atomic
def anular_orden_compra(orden, usuario, motivo: str):
    """
    Anula la orden de compra, sus ordenes de trabajo aun planificadas y sus
    cobros pendientes. No se anula si hay pagos registrados (su devolucion es
    un proceso financiero externo) ni si la fabricacion ya comenzo.
    """
    from apps.pagos.models import DocumentoCobro
    from apps.produccion.models import OrdenTrabajoHistorial

    motivo = _motivo_valido(motivo)
    if orden.estado.codigo in ("anulada", "entregada"):
        raise ErrorComercial(f"La orden ya esta {orden.estado.nombre.lower()}.")
    if orden.documentos_cobro.filter(estado=DocumentoCobro.Estado.PAGADO).exists():
        raise ErrorComercial(
            "La orden tiene pagos registrados: gestione la devolucion antes de anularla."
        )
    iniciadas = orden.ordenes_trabajo.exclude(estado__codigo__in=["planificada", "anulada"])
    if iniciadas.exists():
        raise ErrorComercial(
            f"La orden de trabajo {iniciadas.first().numero} ya inicio su fabricacion."
        )

    anulada_ot = _estado("orden_trabajo", "anulada")
    for ot in orden.ordenes_trabajo.filter(estado__codigo="planificada"):
        anterior_ot = ot.estado
        ot.estado = anulada_ot
        ot.save(update_fields=["estado"])
        OrdenTrabajoHistorial.objects.create(
            orden_trabajo=ot, estado_anterior=anterior_ot, estado_nuevo=anulada_ot,
            usuario=usuario, observacion=f"Anulada con la orden de compra: {motivo}",
        )
    orden.documentos_cobro.filter(estado=DocumentoCobro.Estado.PENDIENTE).update(
        estado=DocumentoCobro.Estado.ANULADO)

    anterior = orden.estado
    orden.estado = _estado("orden_compra", "anulada")
    orden.save(update_fields=["estado"])
    OrdenCompraHistorial.objects.create(
        orden_compra=orden, estado_anterior=anterior, estado_nuevo=orden.estado,
        usuario=usuario, observacion=f"Anulada: {motivo}",
    )
    _auditar_anulacion(usuario, "orden_compra", orden, anterior.codigo, motivo)
    return orden
