"""
Servicios del catalogo: alta y edicion de modelos y versionado de precios.

- RN-17: el precio base no se sobrescribe; cada cambio cierra la vigencia
  anterior y abre una nueva, de modo que las cotizaciones historicas siguen
  explicandose con el precio que regia entonces. Un cambio el mismo dia en
  que se fijo el precio se trata como correccion de ese registro.
- Los parametros tecnicos del modelo definen el formulario que el cliente
  completa al solicitar un presupuesto.
"""
import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.seguridad.models import Auditoria

from .models import ModeloParametro, ModeloProducto, ParametroTecnico, PrecioBaseModelo


class ErrorCatalogo(Exception):
    """Regla de negocio que impide guardar el modelo."""


def _auditar(usuario, modelo, accion, anterior, nuevo):
    Auditoria.objects.create(
        usuario=usuario, entidad="modelo_producto", id_registro=str(modelo.pk),
        accion=accion, valor_anterior=anterior, valor_nuevo=nuevo,
        origen=Auditoria.Origen.ESCRITORIO,
    )


def validar_valor(parametro: ParametroTecnico, valor: str) -> str:
    """El valor por defecto debe ser coherente con el tipo del parametro."""
    valor = (valor or "").strip()
    if not valor:
        return ""
    if parametro.tipo_dato == ParametroTecnico.TipoDato.NUMERICO:
        try:
            Decimal(valor.replace(",", "."))
        except ArithmeticError:
            raise ErrorCatalogo(f"{parametro.nombre}: el valor debe ser numerico.") from None
    if parametro.tipo_dato == ParametroTecnico.TipoDato.LISTA:
        permitidos = list(parametro.valores.filter(activo=True).values_list("valor", flat=True))
        if valor not in permitidos:
            raise ErrorCatalogo(
                f"{parametro.nombre}: el valor debe ser uno de {', '.join(permitidos)}."
            )
    return valor


def _guardar_parametros(modelo: ModeloProducto, parametros: list[dict]):
    vistos = set()
    for item in parametros:
        parametro = ParametroTecnico.objects.get(pk=item["parametro"])
        if parametro.pk in vistos:
            raise ErrorCatalogo(f"El parametro {parametro.nombre} esta repetido.")
        vistos.add(parametro.pk)
        ModeloParametro.objects.update_or_create(
            modelo=modelo, parametro=parametro,
            defaults={"valor_defecto": validar_valor(parametro, item.get("valor_defecto")),
                      "obligatorio": bool(item.get("obligatorio", parametro.obligatorio))},
        )
    modelo.parametros_asignados.exclude(parametro_id__in=vistos).delete()


@transaction.atomic
def fijar_precio(modelo: ModeloProducto, monto: Decimal, usuario) -> PrecioBaseModelo:
    """Versiona el precio base (RN-17)."""
    monto = Decimal(str(monto))
    if monto < 0:
        raise ErrorCatalogo("El precio no puede ser negativo.")
    hoy = timezone.localdate()
    vigente = modelo.precios.filter(vigente_hasta__isnull=True).first()
    if vigente and vigente.monto_uf == monto:
        return vigente

    anterior = str(vigente.monto_uf) if vigente else None
    if vigente and vigente.vigente_desde >= hoy:
        # Correccion el mismo dia: no hay periodo que preservar
        vigente.monto_uf = monto
        vigente.usuario = usuario
        vigente.save(update_fields=["monto_uf", "usuario"])
        precio = vigente
    else:
        if vigente:
            vigente.vigente_hasta = hoy - datetime.timedelta(days=1)
            vigente.save(update_fields=["vigente_hasta"])
        precio = PrecioBaseModelo.objects.create(
            modelo=modelo, monto_uf=monto, vigente_desde=hoy, usuario=usuario
        )
    _auditar(usuario, modelo, Auditoria.Accion.MODIFICACION,
             {"precio_base_uf": anterior}, {"precio_base_uf": str(monto)})
    return precio


@transaction.atomic
def guardar_modelo(datos: dict, usuario, modelo: ModeloProducto | None = None
                   ) -> ModeloProducto:
    """Crea o actualiza un modelo con sus parametros y, si viene, su precio."""
    parametros = datos.pop("parametros", None)
    precio = datos.pop("precio_base_uf", None)

    if modelo is None:
        modelo = ModeloProducto.objects.create(**datos)
        _auditar(usuario, modelo, Auditoria.Accion.CREACION, None,
                 {"codigo": modelo.codigo, "nombre": modelo.nombre})
    else:
        anterior = {campo: str(getattr(modelo, campo)) for campo in datos}
        for campo, valor in datos.items():
            setattr(modelo, campo, valor)
        modelo.save()
        cambios = {c: str(v) for c, v in datos.items() if anterior[c] != str(v)}
        if cambios:
            _auditar(usuario, modelo, Auditoria.Accion.MODIFICACION,
                     {c: anterior[c] for c in cambios}, cambios)

    if parametros is not None:
        _guardar_parametros(modelo, parametros)
    if precio is not None:
        fijar_precio(modelo, precio, usuario)
    return modelo
