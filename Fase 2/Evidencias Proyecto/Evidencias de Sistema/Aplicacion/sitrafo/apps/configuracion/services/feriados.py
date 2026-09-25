"""
Integracion de feriados legales de Chile.

Sustenta RF-COM-08 y RN-08.

Historial de proveedores:
- apis.digital.gob.cl/fl (API del Estado): descontinuada, el subdominio ya no
  resuelve por DNS.
- feriadito.cl: documenta una API de archivos JSON estaticos, pero a la fecha
  el sitio en produccion aun no la publica (responde 404).
- date.nager.at (Nager.Date): proveedor actual. API publica, gratuita y sin
  clave, con cobertura de Chile (codigo de pais CL).

El cliente acepta los formatos de ambos proveedores (feriadito y Nager.Date),
de modo que cambiar de proveedor sea solo cambiar FERIADOS_URL en el .env.

Los feriados se almacenan localmente: el calculo de plazos en dias habiles
debe funcionar aun cuando el servicio no responda (RF-INT-03).
"""
from datetime import date

from django.conf import settings

from apps.configuracion.models import Feriado

from .base import ClienteServicioExterno

URL_POR_DEFECTO = "https://date.nager.at/api/v3/PublicHolidays"
CODIGO_PAIS = "CL"

TIPOS = {
    "civil": Feriado.Tipo.CIVIL,
    "religioso": Feriado.Tipo.RELIGIOSO,
    "regional": Feriado.Tipo.REGIONAL,
}


class ClienteFeriados(ClienteServicioExterno):
    nombre_servicio = "feriados"

    def __init__(self, url_base: str | None = None):
        super().__init__(url_base or getattr(settings, "FERIADOS_URL", URL_POR_DEFECTO))

    def _ruta_anio(self, anio: int) -> str:
        """
        Arma la ruta del anio segun el proveedor configurado.

        Nager.Date:  {url_base}/2026/CL
        feriadito:   {url_base}/2026.json
        """
        if "nager" in self.url_base:
            return f"{anio}/{CODIGO_PAIS}"
        return f"{anio}.json"

    @staticmethod
    def _extraer_lista(datos) -> list:
        """
        Normaliza la respuesta.

        feriadito.cl devuelve un objeto con la clave feriados; Nager.Date y
        otros proveedores devuelven la lista directamente.
        """
        if isinstance(datos, dict):
            return datos.get("feriados", [])
        if isinstance(datos, list):
            return datos
        return []

    @staticmethod
    def _normalizar_item(item: dict) -> tuple[date, str, str] | None:
        """
        Convierte un elemento de cualquier proveedor a (fecha, nombre, tipo).

        Devuelve None si el elemento no es un feriado nacional valido. Los
        feriados regionales de Nager.Date (global = false, por ejemplo los de
        Arica o Nuble) se omiten: el calculo de dias habiles excluye todos los
        feriados almacenados, y un feriado regional no debe correr los plazos
        de una empresa ubicada en otra region.
        """
        if item.get("global") is False:
            return None

        try:
            fecha = date.fromisoformat(str(item.get("fecha") or item.get("date"))[:10])
        except (ValueError, TypeError):
            return None

        nombre = item.get("nombre") or item.get("localName") or item.get("name") or "Feriado"
        tipo = TIPOS.get(str(item.get("tipo", "")).strip().lower(), Feriado.Tipo.CIVIL)
        return fecha, str(nombre)[:120], tipo

    def sincronizar_anio(self, anio: int) -> dict:
        """Descarga y almacena los feriados de un anio."""
        respuesta = self.obtener(self._ruta_anio(anio))

        if not respuesta:
            return {
                "exitoso": False,
                "error": respuesta.mensaje_error,
                "creados": 0,
                "total": Feriado.objects.filter(fecha__year=anio).count(),
            }

        creados = 0
        for item in self._extraer_lista(respuesta.datos):
            if not isinstance(item, dict):
                continue
            normalizado = self._normalizar_item(item)
            if normalizado is None:
                continue
            fecha, nombre, tipo = normalizado

            _, nuevo = Feriado.objects.get_or_create(
                fecha=fecha,
                defaults={"nombre": nombre, "tipo": tipo},
            )
            creados += int(nuevo)

        return {
            "exitoso": True,
            "error": "",
            "creados": creados,
            "total": Feriado.objects.filter(fecha__year=anio).count(),
        }


def plazo_en_dias_habiles(fecha_inicio: date, dias: int) -> tuple[date, bool]:
    """
    Calcula la fecha comprometida (RF-COM-08).

    Devuelve la fecha y si el calculo pudo considerar los feriados. Cuando no
    hay feriados almacenados para el periodo, el calculo excluye solo sabados
    y domingos, y la interfaz debe advertir que la fecha requiere
    verificacion (excepcion E8 de CU-COM-03).
    """
    hay_feriados = Feriado.objects.filter(
        fecha__gte=fecha_inicio, fecha__year=fecha_inicio.year
    ).exists()
    return Feriado.sumar_dias_habiles(fecha_inicio, dias), hay_feriados
