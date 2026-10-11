"""
Parametros de negocio editables en ejecucion.

Cada funcion lee el parametro vigente de la tabla parametro_sistema (que el
Administrador edita desde el escritorio, panel Canal web) y, si no existe o
su valor no es valido, cae al valor por defecto de settings.SITRAFO. Asi un
cambio en el escritorio rige desde la siguiente operacion, sin redesplegar.

Los rangos de cada parametro se validan al editarlo (RANGOS), de modo que un
valor absurdo no llegue nunca a las reglas de negocio.
"""
from decimal import Decimal, InvalidOperation

from django.conf import settings

# clave: (minimo, maximo, entero)
RANGOS = {
    "comercial.vigencia_cotizacion_dias": (1, 365, True),
    "comercial.umbral_descuento_pct": (0, 100, False),
    "comercial.anticipo_pct": (0, 100, False),
    "comercial.margen_defecto_pct": (0, 500, False),
    "comercial.max_unidades_solicitud": (1, 100000, True),
    "produccion.max_horas_diarias": (1, 24, False),
    "produccion.umbral_desviacion_costo_pct": (0, 1000, False),
    "produccion.costo_indirecto_pct": (0, 500, False),
    "sistema.intentos_fallidos_max": (1, 20, True),
    "sistema.minutos_inactividad": (1, 480, True),
    "sistema.minutos_bloqueo": (1, 1440, True),
}


def _por_defecto(nombre: str, valor):
    return getattr(settings, "SITRAFO", {}).get(nombre, valor)


def decimal(clave: str, por_defecto) -> Decimal:
    from .models import ParametroSistema

    try:
        valor = Decimal(str(ParametroSistema.obtener(clave, por_defecto)))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(str(por_defecto))
    minimo, maximo, _ = RANGOS.get(clave, (None, None, False))
    if (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo):
        return Decimal(str(por_defecto))
    return valor


def umbral_descuento_pct() -> Decimal:
    """Descuento sobre el cual la cotizacion requiere aprobacion (RN-05)."""
    return decimal("comercial.umbral_descuento_pct", _por_defecto("UMBRAL_DESCUENTO_PCT", 10))


def anticipo_pct() -> Decimal:
    """Porcentaje de anticipo que se fija en cada orden de compra nueva (RN-15)."""
    return decimal("comercial.anticipo_pct", _por_defecto("ANTICIPO_PORCENTAJE", 50))


def vigencia_cotizacion_dias() -> int:
    return int(decimal("comercial.vigencia_cotizacion_dias",
                       _por_defecto("VIGENCIA_COTIZACION_DIAS", 30)))


def max_unidades_solicitud() -> int:
    """Tope de unidades por solicitud y por linea de cotizacion."""
    return int(decimal("comercial.max_unidades_solicitud",
                       _por_defecto("MAX_UNIDADES_SOLICITUD", 500)))


def umbral_desviacion_pct() -> Decimal:
    """Desviacion de costo sobre la cual el cierre exige justificacion (RN-11)."""
    return decimal("produccion.umbral_desviacion_costo_pct",
                   _por_defecto("UMBRAL_DESVIACION_COSTO_PCT", 15))


def max_horas_diarias() -> Decimal:
    return decimal("produccion.max_horas_diarias", _por_defecto("MAX_HORAS_DIARIAS", 12))


def validar_valor(clave: str, valor: str) -> str | None:
    """Devuelve el mensaje de error si el valor no es valido para la clave."""
    if clave not in RANGOS:
        return None
    minimo, maximo, entero = RANGOS[clave]
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return "Ingrese un numero."
    if not numero.is_finite():
        return "Ingrese un numero."
    if entero and numero != numero.to_integral_value():
        return "Ingrese un numero entero."
    if numero < minimo or numero > maximo:
        return f"El valor debe estar entre {minimo} y {maximo}."
    return None
