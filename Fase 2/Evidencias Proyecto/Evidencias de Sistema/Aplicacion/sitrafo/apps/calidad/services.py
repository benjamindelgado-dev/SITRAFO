"""
Servicios del control de calidad (CU-CAL-01 a CU-CAL-05).

Reglas:
- RF-CAL-01/02: el protocolo define los ensayos de un modelo con su rango
  de aceptacion. Un protocolo ya aplicado no se modifica: se crea una nueva
  version, para que los controles historicos sigan mostrando el criterio con
  que se evaluaron.
- RF-CAL-03: los ensayos se ejecutan sobre ordenes en control de calidad. La
  conformidad la calcula el sistema contra el rango, no el inspector.
- RF-CAL-04: todo resultado fuera de rango abre una no conformidad. Repetir
  el ensayo agrega un resultado nuevo; el anterior se conserva.
- RN-12: la no conformidad se cierra solo registrando la accion correctiva,
  y la orden no se cierra con puntos obligatorios sin ejecutar o con no
  conformidades abiertas.
"""
from decimal import Decimal

from django.db import transaction

from apps.seguridad.models import Auditoria

from .models import ControlCalidad, NoConformidad, ProtocoloCalidad, PuntoControl, ResultadoControl


class ErrorCalidad(Exception):
    """Regla que impide la operacion de calidad."""


def _auditar(usuario, entidad, pk, accion, anterior, nuevo):
    Auditoria.objects.create(
        usuario=usuario, entidad=entidad, id_registro=str(pk), accion=accion,
        valor_anterior=anterior, valor_nuevo=nuevo, origen=Auditoria.Origen.ESCRITORIO,
    )


# ----------------------------------------------------------------------
# Protocolos (CU-CAL-01, CU-CAL-02)
# ----------------------------------------------------------------------
def _validar_puntos(puntos: list[dict]):
    if not puntos:
        raise ErrorCalidad("El protocolo debe tener al menos un punto de control.")
    for i, p in enumerate(puntos, start=1):
        if not str(p.get("nombre", "")).strip():
            raise ErrorCalidad(f"El punto {i} no tiene nombre.")
        inf, sup = p.get("tolerancia_inf"), p.get("tolerancia_sup")
        if inf is None and sup is None:
            raise ErrorCalidad(f"«{p['nombre']}»: defina al menos un limite del rango.")
        if inf is not None and sup is not None and Decimal(str(inf)) > Decimal(str(sup)):
            raise ErrorCalidad(f"«{p['nombre']}»: el limite inferior supera al superior.")


def _crear_puntos(protocolo, puntos):
    for secuencia, p in enumerate(puntos, start=1):
        PuntoControl.objects.create(
            protocolo=protocolo, secuencia=secuencia, nombre=p["nombre"].strip(),
            tipo_ensayo=(p.get("tipo_ensayo") or "Rutina").strip(),
            unidad=(p.get("unidad") or "").strip(),
            valor_esperado=p.get("valor_esperado"),
            tolerancia_inf=p.get("tolerancia_inf"), tolerancia_sup=p.get("tolerancia_sup"),
            obligatorio=p.get("obligatorio", True),
        )


@transaction.atomic
def guardar_protocolo(usuario, *, modelo, nombre, norma_referencia="", puntos,
                      protocolo: ProtocoloCalidad | None = None) -> ProtocoloCalidad:
    """
    Crea el protocolo o lo modifica. Si el protocolo ya se aplico en algun
    control, la modificacion genera una version nueva y retira la anterior.
    """
    _validar_puntos(puntos)
    if protocolo is not None and not protocolo.controles.exists():
        protocolo.nombre, protocolo.norma_referencia = nombre, norma_referencia
        protocolo.save(update_fields=["nombre", "norma_referencia"])
        protocolo.puntos.all().delete()
        _crear_puntos(protocolo, puntos)
        _auditar(usuario, "protocolo_calidad", protocolo.pk, Auditoria.Accion.MODIFICACION,
                 None, {"puntos": len(puntos)})
        return protocolo

    version = 1
    if protocolo is not None:
        version = protocolo.version + 1
        protocolo.activo = False
        protocolo.save(update_fields=["activo"])
    else:
        ultima = ProtocoloCalidad.objects.filter(modelo=modelo, nombre=nombre).order_by(
            "-version").first()
        if ultima:
            version = ultima.version + 1
            ProtocoloCalidad.objects.filter(modelo=modelo, nombre=nombre).update(activo=False)

    nuevo = ProtocoloCalidad.objects.create(
        modelo=modelo, nombre=nombre, version=version, norma_referencia=norma_referencia
    )
    _crear_puntos(nuevo, puntos)
    _auditar(usuario, "protocolo_calidad", nuevo.pk, Auditoria.Accion.CREACION, None,
             {"modelo": modelo.codigo, "nombre": nombre, "version": version})
    return nuevo


# ----------------------------------------------------------------------
# Ejecucion de ensayos (CU-CAL-03, CU-CAL-04)
# ----------------------------------------------------------------------
def estado_de_puntos(control: ControlCalidad) -> list[dict]:
    """Ultimo resultado de cada punto del protocolo, con su no conformidad."""
    ultimos = {}
    for resultado in control.resultados.select_related("no_conformidad").order_by(
        "registrado_en", "id_resultado"
    ):
        ultimos[resultado.punto_id] = resultado
    filas = []
    for punto in control.protocolo.puntos.order_by("secuencia"):
        resultado = ultimos.get(punto.pk)
        nc = getattr(resultado, "no_conformidad", None) if resultado else None
        filas.append({"punto": punto, "resultado": resultado, "no_conformidad": nc})
    return filas


def recalcular_estado(control: ControlCalidad) -> str:
    """
    Conforme cuando todos los puntos obligatorios tienen un ultimo resultado
    conforme o una no conformidad cerrada; con NC mientras haya alguna
    abierta; en proceso mientras falten ensayos.
    """
    abiertas = NoConformidad.objects.filter(
        resultado__control=control, estado=NoConformidad.Estado.ABIERTA
    ).exists()
    pendientes = control.puntos_pendientes.exists()
    if abiertas:
        control.estado = ControlCalidad.Estado.CON_NO_CONFORMIDADES
    elif pendientes:
        control.estado = ControlCalidad.Estado.EN_PROCESO
    else:
        control.estado = ControlCalidad.Estado.CONFORME
    control.save(update_fields=["estado"])
    return control.estado


@transaction.atomic
def iniciar_control(orden_trabajo, protocolo: ProtocoloCalidad, inspector) -> ControlCalidad:
    if orden_trabajo.estado.codigo != "en_calidad":
        raise ErrorCalidad(
            f"La orden {orden_trabajo.numero} no esta en control de calidad."
        )
    if protocolo.modelo_id != orden_trabajo.modelo_id or not protocolo.activo:
        raise ErrorCalidad("El protocolo no corresponde al modelo de la orden o esta retirado.")
    existente = orden_trabajo.controles_calidad.filter(protocolo=protocolo).first()
    if existente:
        return existente
    return ControlCalidad.objects.create(orden_trabajo=orden_trabajo, protocolo=protocolo,
                                         inspector=inspector)


@transaction.atomic
def registrar_resultado(control: ControlCalidad, punto: PuntoControl, valor: Decimal,
                        usuario, *, observacion: str = "", severidad: str = "mayor",
                        descripcion: str = "") -> ResultadoControl:
    """Registra la medicion; si esta fuera de rango abre la no conformidad."""
    if control.orden_trabajo.estado.codigo != "en_calidad":
        raise ErrorCalidad("La orden ya no esta en control de calidad.")
    if punto.protocolo_id != control.protocolo_id:
        raise ErrorCalidad("El punto no pertenece al protocolo del control.")
    abierta = NoConformidad.objects.filter(
        resultado__control=control, resultado__punto=punto,
        estado=NoConformidad.Estado.ABIERTA,
    ).first()
    if abierta:
        raise ErrorCalidad(
            f"«{punto.nombre}» tiene una no conformidad abierta: registre la accion "
            "correctiva antes de repetir el ensayo."
        )
    if severidad not in NoConformidad.Severidad.values:
        raise ErrorCalidad("Severidad no valida.")

    resultado = ResultadoControl.objects.create(
        control=control, punto=punto, valor_medido=Decimal(str(valor)),
        conforme=True, observacion=observacion.strip(),
    )
    if not resultado.conforme:
        rango = []
        if punto.tolerancia_inf is not None:
            rango.append(f"min {punto.tolerancia_inf.normalize()}")
        if punto.tolerancia_sup is not None:
            rango.append(f"max {punto.tolerancia_sup.normalize()}")
        NoConformidad.objects.create(
            resultado=resultado, severidad=severidad, responsable=usuario,
            descripcion=(descripcion.strip() or
                         f"{punto.nombre}: {resultado.valor_medido.normalize()} "
                         f"{punto.unidad} fuera de rango ({', '.join(rango)}).")[:300],
        )
    recalcular_estado(control)
    return resultado


@transaction.atomic
def cerrar_no_conformidad(nc: NoConformidad, usuario, accion_correctiva: str) -> NoConformidad:
    """RN-12: la no conformidad se cierra solo con la accion correctiva registrada."""
    if nc.estado == NoConformidad.Estado.CERRADA:
        raise ErrorCalidad("La no conformidad ya esta cerrada.")
    if len(accion_correctiva.strip()) < 10:
        raise ErrorCalidad("Describa la accion correctiva (al menos 10 caracteres).")
    nc.cerrar(usuario, accion_correctiva.strip())
    _auditar(usuario, "no_conformidad", nc.pk, Auditoria.Accion.MODIFICACION,
             {"estado": "abierta"}, {"estado": "cerrada", "accion": accion_correctiva.strip()})
    recalcular_estado(nc.resultado.control)
    return nc
