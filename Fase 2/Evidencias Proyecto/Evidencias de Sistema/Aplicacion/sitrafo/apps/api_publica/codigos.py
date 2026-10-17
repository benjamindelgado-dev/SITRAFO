"""
Codigo de seguimiento de una orden de compra.

El codigo se deriva de la orden con una firma HMAC, por lo que no se
almacena en la base de datos (no agrega tablas ni columnas) y no se puede
adivinar a partir del numero de la orden. Solo quien recibio el codigo
puede consultar el pedido en la API publica.
"""
import base64
import hashlib
import hmac

from django.conf import settings


def _clave() -> bytes:
    return settings.SEGUIMIENTO_CLAVE.encode()


def codigo_seguimiento(orden_compra) -> str:
    """Devuelve el codigo con el formato XXXXX-XXXXX."""
    mensaje = f"seguimiento:{orden_compra.pk}:{orden_compra.numero}".encode()
    firma = hmac.new(_clave(), mensaje, hashlib.sha256).digest()
    texto = base64.b32encode(firma).decode()[:10]
    return f"{texto[:5]}-{texto[5:]}"


def normalizar(codigo: str) -> str:
    """Acepta el codigo con o sin guion, en mayusculas o minusculas."""
    limpio = "".join(c for c in (codigo or "").upper() if c.isalnum())
    return f"{limpio[:5]}-{limpio[5:]}" if len(limpio) == 10 else limpio


def codigo_valido(orden_compra, codigo: str) -> bool:
    # Comparacion en tiempo constante para no filtrar el codigo por tiempos
    return hmac.compare_digest(codigo_seguimiento(orden_compra), normalizar(codigo))
