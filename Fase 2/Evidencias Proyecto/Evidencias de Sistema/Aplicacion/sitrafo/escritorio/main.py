"""
SITRAFO — Aplicacion de escritorio.

Administracion interna del sistema. Consume exclusivamente la API REST: esta
aplicacion no tiene ninguna dependencia de Django ni acceso directo a la base
de datos (RNF-05).

Uso:
    python main.py
    python main.py --api http://192.168.1.10:8000/api/v1
"""
import argparse
import sys

from cliente_api import ClienteAPI
from estilos import HOJA
from PySide6.QtWidgets import QApplication, QDialog
from ventana_login import VentanaLogin
from ventana_principal import VentanaPrincipal

API_POR_DEFECTO = "http://localhost:8000/api/v1"


def main() -> int:
    analizador = argparse.ArgumentParser(description="SITRAFO — Administracion interna")
    analizador.add_argument(
        "--api",
        default=API_POR_DEFECTO,
        help=f"URL base de la API REST (por defecto {API_POR_DEFECTO})",
    )
    argumentos = analizador.parse_args()

    aplicacion = QApplication(sys.argv)
    aplicacion.setApplicationName("SITRAFO")
    aplicacion.setStyleSheet(HOJA)

    cliente = ClienteAPI(argumentos.api)
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
