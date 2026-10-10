"""Hoja de estilo y tema claro de la aplicacion de escritorio."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette

AZUL = "#1f3864"
AZUL_CLARO = "#2e5496"
GRIS_FONDO = "#f5f7fa"
GRIS_BORDE = "#c9d4e2"
TEXTO = "#1a1a1a"

HOJA = f"""
/* El color del texto se fija de forma explicita: de lo contrario el tema
   oscuro de Windows lo pinta en blanco sobre los fondos claros de la
   aplicacion y las etiquetas quedan ilegibles. */
QWidget {{ color: {TEXTO}; }}

QMainWindow, QDialog {{ background-color: {GRIS_FONDO}; color: {TEXTO}; }}

QLabel {{ color: {TEXTO}; background: transparent; }}
QCheckBox {{ color: {TEXTO}; spacing: 8px; }}
QGroupBox {{ color: {TEXTO}; }}

QLabel#titulo {{
    font-size: 20px; font-weight: bold; color: {AZUL};
}}
QLabel#subtitulo {{ color: #6c757d; }}
QLabel#marca {{
    font-size: 26px; font-weight: bold; color: {AZUL};
}}

QPushButton {{
    background-color: {AZUL}; color: white; border: none;
    padding: 8px 16px; border-radius: 4px;
}}
QPushButton:hover {{ background-color: {AZUL_CLARO}; }}
QPushButton:disabled {{ background-color: #9aa5b1; }}
QPushButton#secundario {{
    background-color: white; color: {AZUL}; border: 1px solid {GRIS_BORDE};
}}
QPushButton#secundario:hover {{ background-color: #eef2f7; }}
QPushButton#peligro {{ background-color: #b02a37; }}
QPushButton#peligro:hover {{ background-color: #c9333f; }}
QPushButton#exito {{ background-color: #1a7f37; }}
QPushButton#exito:hover {{ background-color: #1f9442; }}

/* Los botones con variante de color tambien deben verse deshabilitados */
QPushButton#exito:disabled, QPushButton#peligro:disabled {{
    background-color: #9aa5b1; color: #eef2f7;
}}
QPushButton#secundario:disabled {{
    background-color: #eef2f7; color: #9aa5b1; border: 1px solid #dde3ea;
}}

QLabel#cifra {{ font-size: 22px; font-weight: bold; color: {AZUL}; }}
QLabel#nota {{ color: #6c757d; font-size: 12px; }}

QLineEdit, QComboBox, QTextEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox {{
    padding: 7px; border: 1px solid {GRIS_BORDE};
    border-radius: 4px; background: white; color: {TEXTO};
}}
QLineEdit::placeholder {{ color: #9aa5b1; }}

QTableWidget {{
    background: white; border: 1px solid {GRIS_BORDE};
    gridline-color: #e6ebf2; color: {TEXTO};
}}
QHeaderView::section {{
    background-color: {AZUL}; color: white; padding: 7px; border: none;
}}
QTableWidget::item:selected {{ background-color: #dce4ef; color: #000; }}

QListWidget#menu, QListWidget#menu::item {{
    color: white;
}}
QListWidget#menu {{
    background-color: {AZUL}; color: white; border: none;
    outline: 0; font-size: 14px;
}}
QListWidget#menu::item {{ padding: 13px 18px; }}
QListWidget#menu::item:selected {{ background-color: {AZUL_CLARO}; }}
QListWidget#menu::item:hover {{ background-color: #2a4a80; }}

QGroupBox {{
    background: white; border: 1px solid {GRIS_BORDE};
    border-radius: 6px; margin-top: 12px; padding-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 12px; padding: 0 5px;
    font-weight: bold; color: {AZUL};
}}

QStatusBar {{
    background: white; border-top: 1px solid {GRIS_BORDE}; color: #6c757d;
}}

QMessageBox {{ background-color: {GRIS_FONDO}; }}
QMessageBox QLabel {{ color: {TEXTO}; }}

/* Listas desplegables, listas y calendarios: fondo blanco siempre, para que
   el tema oscuro de Windows no los pinte con texto oscuro sobre fondo oscuro. */
QComboBox QAbstractItemView, QListView, QListWidget, QTreeView {{
    background: white; color: {TEXTO}; border: 1px solid {GRIS_BORDE};
    selection-background-color: #dce4ef; selection-color: #000;
    outline: 0;
}}
QComboBox QAbstractItemView::item {{ min-height: 26px; padding: 2px 6px; }}
QPlainTextEdit {{
    padding: 7px; border: 1px solid {GRIS_BORDE}; border-radius: 4px;
    background: white; color: {TEXTO};
}}
QMenu {{ background: white; color: {TEXTO}; border: 1px solid {GRIS_BORDE}; }}
QMenu::item:selected {{ background: #dce4ef; color: #000; }}
QToolTip {{ background: white; color: {TEXTO}; border: 1px solid {GRIS_BORDE}; }}
QCalendarWidget QWidget {{ background: white; color: {TEXTO}; }}
QCalendarWidget QToolButton {{ color: {AZUL}; background: transparent; font-weight: bold; }}
QCalendarWidget QAbstractItemView:disabled {{ color: #9aa5b1; }}
"""


def aplicar_tema(aplicacion) -> None:
    """
    Fija un tema claro independiente de la configuracion de Windows.

    Con el modo oscuro de Windows, Qt entrega una paleta oscura: las listas
    desplegables y algunas listas quedaban con fondo oscuro y texto oscuro.
    Se pide el esquema de color claro (Qt 6.8 o superior) y se fija una paleta
    clara explicita; se conserva el estilo nativo de Windows.
    """
    try:
        aplicacion.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass
    paleta = QPalette()
    claro = {
        QPalette.Window: GRIS_FONDO, QPalette.WindowText: TEXTO,
        QPalette.Base: "#ffffff", QPalette.AlternateBase: "#f2f5fa",
        QPalette.Text: TEXTO, QPalette.Button: "#ffffff", QPalette.ButtonText: TEXTO,
        QPalette.ToolTipBase: "#ffffff", QPalette.ToolTipText: TEXTO,
        QPalette.Highlight: "#dce4ef", QPalette.HighlightedText: "#000000",
        QPalette.PlaceholderText: "#9aa5b1", QPalette.Link: AZUL_CLARO,
        QPalette.BrightText: "#ffffff", QPalette.Light: "#ffffff",
        QPalette.Midlight: "#eef2f7", QPalette.Mid: GRIS_BORDE, QPalette.Dark: "#9aa5b1",
        QPalette.Shadow: "#6c757d",
    }
    for rol, color in claro.items():
        paleta.setColor(rol, QColor(color))
    for rol in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        paleta.setColor(QPalette.Disabled, rol, QColor("#9aa5b1"))
    aplicacion.setPalette(paleta)
    aplicacion.setStyleSheet(HOJA)
