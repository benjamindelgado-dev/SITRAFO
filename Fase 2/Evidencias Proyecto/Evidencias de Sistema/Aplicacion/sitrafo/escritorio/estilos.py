"""Hoja de estilo de la aplicacion de escritorio."""

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

QLineEdit, QComboBox, QTextEdit, QDateTimeEdit {{
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
"""
