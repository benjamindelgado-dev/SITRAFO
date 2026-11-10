"""
Integracion con mindicador.cl — indicadores economicos de Chile.

Sustenta RF-PAG-05 y RF-PAG-06. La serie historica almacenada es lo que
permite que el sistema siga cotizando cuando el servicio no responde: se
opera con el ultimo valor conocido, informando su fecha (RN-03, RF-INT-03).
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.cache import cache
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

    # Sin registro, o con el de un dia anterior cuando se pide la UF de hoy
    # (por ejemplo, antes de que corra la tarea diaria), se intenta traer el
    # valor vigente. Si el servicio no responde se opera con el ultimo conocido.
    desactualizado = registro is not None and registro.fecha != fecha
    if registro is None or (desactualizado and _corresponde_actualizar(fecha)):
        resultado = ClienteIndicadores().sincronizar_dia(fecha)
        if resultado["exitoso"]:
            registro = IndicadorEconomico.valor_a(fecha, "UF")

    if registro is None:
        return None, None, False

    return registro.valor, registro.fecha, registro.fecha == fecha


# Si mindicador no responde, no se vuelve a intentar en cada cotizacion: un
# reintento cada media hora basta y evita sumar la espera de un servicio caido
# a cada pantalla que muestra montos en UF.
INTERVALO_ACTUALIZACION_UF = 30 * 60


def _corresponde_actualizar(fecha: date) -> bool:
    """Solo la UF de hoy se puede traer del servicio, y a lo mas cada 30 min."""
    if fecha != timezone.localdate():
        return False
    return cache.add(f"uf-actualizacion-{fecha.isoformat()}", True,
                     INTERVALO_ACTUALIZACION_UF)
