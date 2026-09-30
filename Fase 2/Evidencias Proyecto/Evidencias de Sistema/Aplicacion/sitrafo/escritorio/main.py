"""
SITRAFO — Aplicacion de escritorio.

Administracion interna del sistema. Consume exclusivamente la API REST: esta
aplicacion no tiene ninguna dependencia de Django ni acceso directo a la base
de datos (RNF-05).

Uso:
    python main.py                      (servidor guardado o el de Render)
    python main.py --api http://localhost:8000/api/v1

Tambien se distribuye como SITRAFO.exe (ver construir_exe.bat): la direccion
del servidor se puede cambiar desde la ventana de acceso y queda guardada.
"""
import argparse
import sys
from pathlib import Path

import configuracion_local
from cliente_api import ClienteAPI
from estilos import HOJA
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog
from ventana_login import VentanaLogin
from ventana_principal import VentanaPrincipal

API_POR_DEFECTO = configuracion_local.SERVIDOR_POR_DEFECTO


def recurso(nombre: str) -> str:
    """Ruta de un archivo incluido, tanto en desarrollo como dentro del .exe."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / nombre)


def main() -> int:
    analizador = argparse.ArgumentParser(description="SITRAFO — Administracion interna")
    analizador.add_argument(
        "--api",
        default=None,
        help=f"URL base de la API REST (por defecto la guardada, o {API_POR_DEFECTO})",
    )
    argumentos = analizador.parse_args()
    servidor = (configuracion_local.normalizar_servidor(argumentos.api or "")
                or configuracion_local.leer().get("servidor") or API_POR_DEFECTO)

    aplicacion = QApplication(sys.argv)
    aplicacion.setApplicationName("SITRAFO")
    aplicacion.setStyleSheet(HOJA)
    aplicacion.setWindowIcon(QIcon(recurso("sitrafo.ico")))

    cliente = ClienteAPI(servidor)
    estado = {"ventana": None}

    def ingresar() -> bool:
        """Pide credenciales y abre la ventana que corresponde al rol."""
        login = VentanaLogin(cliente)
        if login.exec() != QDialog.Accepted:
            return False
        ventana = VentanaPrincipal(cliente)
        ventana.sesion_cerrada.connect(volver_al_ingreso)
        estado["ventana"] = ventana
        ventana.show()
        return True

    def volver_al_ingreso():
        # Tras cerrar sesion se vuelve a pedir usuario; si se cancela, se sale
        if not ingresar():
            aplicacion.quit()

    # La aplicacion no termina al cerrar la ventana por cerrar sesion: lo
    # hace la ventana principal al cerrarse con la X, o el ingreso cancelado
    aplicacion.setQuitOnLastWindowClosed(False)
    if not ingresar():
        return 0
    return aplicacion.exec()


if __name__ == "__main__":
    sys.exit(main())
