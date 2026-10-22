"""
Disponibilidad de materiales para la API publica (RF-INV-09, HU-17).

Informa a los proveedores autorizados que materiales estan bajo su stock
minimo y cuanto conviene reponer, para que preparen el despacho antes de que
la planta se quede sin material.

- El stock actual se calcula desde el kardex (suma de los movimientos de
  inventario de todas las bodegas), igual que la alerta de reposicion del
  escritorio (CU-INV-06).
- La cantidad sugerida lleva el stock al doble del minimo:
  sugerida = 2 x minimo - stock actual. Asi el material no queda justo en el
  limite despues de recibir el despacho.
- La respuesta no incluye costos, precios, bodegas ni movimientos: solo lo
  que el proveedor necesita para despachar.
"""
from decimal import ROUND_CEILING, Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.inventario.models import Material, MovimientoInventario

FACTOR_REPOSICION = Decimal("2")
CENTESIMA = Decimal("0.01")


def _redondear_hacia_arriba(cantidad: Decimal, unidad: str) -> Decimal:
    """Las unidades enteras se piden completas; el resto, con dos decimales."""
    paso = Decimal("1") if unidad == Material.UnidadMedida.UNIDAD else CENTESIMA
    return cantidad.quantize(paso, rounding=ROUND_CEILING)


def materiales_a_reponer() -> dict:
    """Materiales activos bajo su stock minimo, con la cantidad sugerida."""
    stocks = dict(
        MovimientoInventario.objects.values("material")
        .annotate(total=Sum("cantidad"))
        .values_list("material", "total")
    )
    materiales = (Material.objects.filter(activo=True, stock_minimo__gt=0)
                  .select_related("categoria").order_by("codigo"))
    resultado = []
    for material in materiales:
        actual = stocks.get(material.pk) or Decimal("0")
        if actual >= material.stock_minimo:
            continue
        sugerida = FACTOR_REPOSICION * material.stock_minimo - actual
        resultado.append({
            "codigo": material.codigo,
            "nombre": material.nombre,
            "categoria": material.categoria.nombre,
            "unidad": material.unidad_medida,
            "stock_minimo": material.stock_minimo,
            "cantidad_sugerida": _redondear_hacia_arriba(sugerida, material.unidad_medida),
        })
    return {
        "materiales": resultado,
        "total": len(resultado),
        "criterio": "Cantidad sugerida = 2 x stock minimo - stock actual (kardex).",
        "calculado_en": timezone.now(),
    }
