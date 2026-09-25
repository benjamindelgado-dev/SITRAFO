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

    login = VentanaLogin(cliente)
    if login.exec() != QDialog.Accepted:
        return 0

    ventana = VentanaPrincipal(cliente)
    ventana.show()
    return aplicacion.exec()


if __name__ == "__main__":
    sys.exit(main())
