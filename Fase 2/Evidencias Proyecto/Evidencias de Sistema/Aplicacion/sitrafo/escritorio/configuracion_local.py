"""
Configuracion local de la aplicacion de escritorio.

Guarda en el equipo del usuario la direccion del servidor y el ultimo
usuario que ingreso, para no pedirlos cada vez. Nunca guarda contrasenas ni
tokens.

Ubicacion: %APPDATA%\\SITRAFO\\config.json en Windows, o
~/.config/sitrafo/config.json en otros sistemas.
"""
import json
import os
from pathlib import Path

SERVIDOR_POR_DEFECTO = "https://sitrafo.onrender.com/api/v1"


def _ruta() -> Path:
    base = os.environ.get("APPDATA")
    carpeta = Path(base) / "SITRAFO" if base else Path.home() / ".config" / "sitrafo"
    return carpeta / "config.json"


def leer() -> dict:
    try:
        return json.loads(_ruta().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def guardar(**valores) -> None:
    datos = leer()
    datos.update({k: v for k, v in valores.items() if v is not None})
    try:
        ruta = _ruta()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass   # sin permisos de escritura: la aplicacion funciona igual


def normalizar_servidor(texto: str) -> str | None:
    """
    Acepta la direccion del sitio o de la API y devuelve la de la API.
    'sitrafo.onrender.com' -> 'https://sitrafo.onrender.com/api/v1'.
    Devuelve None si no parece una direccion valida.
    """
    texto = (texto or "").strip().rstrip("/")
    if not texto or " " in texto or "<" in texto or ">" in texto:
        return None
    if not texto.startswith(("http://", "https://")):
        texto = ("http://" if texto.startswith(("localhost", "127.0.0.1")) else "https://") + texto
    if not texto.endswith("/api/v1"):
        texto += "/api/v1"
    return texto
