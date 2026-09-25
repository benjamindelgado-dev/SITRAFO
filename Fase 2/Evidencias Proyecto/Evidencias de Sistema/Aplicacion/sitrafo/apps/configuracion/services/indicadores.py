"""
Integracion con mindicador.cl — indicadores economicos de Chile.

Sustenta RF-PAG-05 y RF-PAG-06. La serie historica almacenada es lo que
permite que el sistema siga cotizando cuando el servicio no responde: se
opera con el ultimo valor conocido, informando su fecha (RN-03, RF-INT-03).
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone

from apps.pagos.models import IndicadorEconomico

from .base import ClienteServicioExterno


class ClienteIndicadores(ClienteServicioExterno):
    nombre_servicio = "mindicador"

    def __init__(self, url_base: str | None = None):
        super().__init__(url_base or getattr(settings, "MINDICADOR_URL", "https://mindicador.cl/api"))

    def sincronizar_dia(self, fecha: date | None = None) -> dict:
        """
        Descarga los indicadores del dia y los almacena.

        Devuelve un resumen con los indicadores obtenidos y si hubo fallo.
        """
        fecha = fecha or timezone.localdate()
        respuesta = self.obtener()

        if not respuesta:
            return {
                "exitoso": False,
                "error": respuesta.mensaje_error,
                "almacenados": [],
            }

        almacenados = []
        for codigo, clave in (("UF", "uf"), ("UTM", "utm"), ("USD", "dolar")):
            bloque = respuesta.datos.get(clave)
            if not isinstance(bloque, dict):
                continue
            try:
                valor = Decimal(str(bloque["valor"]))
            except (KeyError, InvalidOperation, TypeError):
                continue

            fecha_valor = fecha
            if bloque.get("fecha"):
                fecha_valor = date.fromisoformat(bloque["fecha"][:10])

            IndicadorEconomico.objects.update_or_create(
                codigo=codigo,
                fecha=fecha_valor,
                defaults={"valor": valor},
            )
            almacenados.append((codigo, fecha_valor, valor))

        return {"exitoso": True, "error": "", "almacenados": almacenados}


def valor_uf(fecha: date | None = None) -> tuple[Decimal | None, date | None, bool]:
    """
    Valor de la UF a una fecha, con degradacion controlada (RF-PAG-06).

    Devuelve el valor, la fecha efectiva del valor y si corresponde
    exactamente a la fecha pedida. Si el registro es de una fecha anterior,
    la interfaz debe advertirlo al usuario.
    """
    fecha = fecha or timezone.localdate()
    registro = IndicadorEconomico.valor_a(fecha, "UF")

    if registro is None:
        resultado = ClienteIndicadores().sincronizar_dia(fecha)
        if resultado["exitoso"]:
            registro = IndicadorEconomico.valor_a(fecha, "UF")

    if registro is None:
        return None, None, False

    return registro.valor, registro.fecha, registro.fecha == fecha
