"""
Hoja de estilo y tema claro de la aplicacion de escritorio.

Mismo lenguaje visual que el portal web: chapa grafito, acento cobre (el
material del bobinado), placas blancas con filete suave y la pareja
tipografica Archivo (titulos) + IBM Plex Sans (texto). Las fuentes van en la
carpeta fuentes/ para que la aplicacion se vea igual en cualquier equipo,
tambien dentro de SITRAFO.exe.
"""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette

# -- Paleta (la misma del portal web) ----------------------------------------
GRAFITO = "#1b242b"        # barra lateral, cabeceras, texto principal
GRAFITO_MEDIO = "#26323b"  # seleccion y hover sobre grafito
COBRE = "#8a4b24"          # acento: el material del bobinado
COBRE_MEDIO = "#a65a2a"
COBRE_PLANO = "#c2814a"    # cobre aclarado, legible sobre grafito
COBRE_LUZ = "#f2e6da"      # seleccion sobre fondo claro
PAPEL = "#ecefeb"          # fondo de las ventanas
LINEA = "#e1e4e0"          # filetes suaves
ANSI = "#a8b0ae"           # bordes de campos (gris ANSI 70)
ACERO = "#4a5760"          # texto secundario
TEXTO = GRAFITO
CONFORME = "#2f6b4f"
FALLA = "#8c2f39"

# Nombres anteriores, por compatibilidad con codigo que los importe
AZUL, AZUL_CLARO, GRIS_FONDO, GRIS_BORDE = GRAFITO, COBRE, PAPEL, ANSI

FAMILIA_TEXTO = "IBM Plex Sans"
FAMILIA_TITULO = "Archivo"


def recurso(nombre: str) -> str:
    """Ruta de un archivo incluido, tanto en desarrollo como dentro del .exe."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / nombre)


def cargar_fuentes() -> tuple[str, str]:
    """
    Registra las fuentes de la carpeta fuentes/ y devuelve las familias a usar
    (texto, titulos). Si faltan los archivos se usa la fuente del sistema, de
    modo que la aplicacion nunca deja de abrir por un tema visual.
    """
    familias: set[str] = set()
    carpeta = Path(recurso("fuentes"))
    if carpeta.is_dir():
        for archivo in sorted(carpeta.glob("*.ttf")):
            identificador = QFontDatabase.addApplicationFont(str(archivo))
            if identificador != -1:
                familias.update(QFontDatabase.applicationFontFamilies(identificador))
    texto = FAMILIA_TEXTO if FAMILIA_TEXTO in familias else "Segoe UI"
    titulo = FAMILIA_TITULO if FAMILIA_TITULO in familias else texto
    return texto, titulo


def _imagen(nombre: str) -> str:
    """Ruta para usar dentro de la hoja de estilo (con / tambien en Windows)."""
    return Path(recurso(f"img/{nombre}")).as_posix()


def hoja(texto: str, titulo: str) -> str:
    abajo, arriba = _imagen("flecha_abajo.png"), _imagen("flecha_arriba.png")
    abajo_off, arriba_off = _imagen("flecha_abajo_off.png"), _imagen("flecha_arriba_off.png")
    return f"""
/* El color del texto se fija de forma explicita: de lo contrario el tema
   oscuro de Windows lo pinta en blanco sobre los fondos claros. */
QWidget {{ color: {TEXTO}; }}
QMainWindow, QDialog {{ background-color: {PAPEL}; color: {TEXTO}; }}
QLabel {{ color: {TEXTO}; background: transparent; }}
QCheckBox {{ color: {TEXTO}; spacing: 8px; }}
QGroupBox {{ color: {TEXTO}; }}

/* -- Titulos y cifras ---------------------------------------------------- */
QLabel#titulo {{
    font-family: "{titulo}"; font-size: 24px; font-weight: 700; color: {GRAFITO};
}}
QLabel#subtitulo {{ color: {ACERO}; }}
QLabel#marca {{
    font-family: "{titulo}"; font-size: 30px; font-weight: 700; color: {GRAFITO};
}}
QLabel#cifra {{
    font-family: "{titulo}"; font-size: 24px; font-weight: 700; color: {COBRE};
}}
QLabel#nota {{ color: {ACERO}; font-size: 12px; }}

/* -- Botones ------------------------------------------------------------- */
QPushButton {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 {COBRE_MEDIO}, stop:1 {COBRE});
    color: white; border: 1px solid {COBRE}; border-radius: 7px;
    padding: 8px 13px; font-weight: 600;
}}
QPushButton:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #b6672f, stop:1 #985226);
}}
QPushButton:pressed {{ background-color: {COBRE}; }}
QPushButton:disabled {{ background-color: #c4c9c7; border-color: #c4c9c7; color: #f5f6f5; }}

QPushButton#secundario {{
    background-color: white; color: {GRAFITO}; border: 1px solid {ANSI};
}}
QPushButton#secundario:hover {{ background-color: #f6f7f5; border-color: {GRAFITO}; }}
QPushButton#secundario:disabled {{
    background-color: #f1f2f0; color: #a9b0b4; border: 1px solid {LINEA};
}}
QPushButton#peligro {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #a03a46, stop:1 {FALLA});
    border-color: {FALLA};
}}
QPushButton#peligro:hover {{ background-color: #a8404d; }}
QPushButton#exito {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #377b5c, stop:1 {CONFORME});
    border-color: {CONFORME};
}}
QPushButton#exito:hover {{ background-color: #3a8463; }}
QPushButton#exito:disabled, QPushButton#peligro:disabled {{
    background-color: #c4c9c7; border-color: #c4c9c7; color: #f5f6f5;
}}

/* -- Campos -------------------------------------------------------------- */
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QDateTimeEdit,
QSpinBox, QDoubleSpinBox {{
    padding: 7px 9px; border: 1px solid {ANSI}; border-radius: 7px;
    background: #fcfdfc; color: {TEXTO};
    selection-background-color: {COBRE_LUZ}; selection-color: {TEXTO};
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus,
QDateTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COBRE};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background: #f1f2f0; color: #8c959b;
}}
QLineEdit::placeholder {{ color: #9aa3a8; }}

/* Flechas propias: las nativas se dibujan rotas cuando el campo tiene borde
   redondeado. Se usan las mismas en listas, numeros y fechas. */
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down, QDateTimeEdit::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right;
    width: 26px; border: none; background: transparent;
}}
QComboBox::down-arrow, QDateTimeEdit::down-arrow {{
    image: url("{abajo}"); width: 10px; height: 6px;
}}
QComboBox::down-arrow:disabled, QDateTimeEdit::down-arrow:disabled {{ image: url("{abajo_off}"); }}
QSpinBox, QDoubleSpinBox, QDateTimeEdit {{ padding-right: 26px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QDateTimeEdit::up-button {{
    subcontrol-origin: border; subcontrol-position: top right; width: 24px;
    border: none; border-left: 1px solid {LINEA}; border-top-right-radius: 7px;
    background: #f4f5f3;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button, QDateTimeEdit::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right; width: 24px;
    border: none; border-left: 1px solid {LINEA}; border-bottom-right-radius: 7px;
    background: #f4f5f3;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QDateTimeEdit::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover,
QDateTimeEdit::down-button:hover {{ background: {COBRE_LUZ}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QDateTimeEdit::up-arrow {{
    image: url("{arriba}"); width: 9px; height: 5px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QDateTimeEdit::down-arrow {{
    image: url("{abajo}"); width: 9px; height: 5px;
}}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled,
QSpinBox::up-arrow:off, QDoubleSpinBox::up-arrow:off {{ image: url("{arriba_off}"); }}
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled,
QSpinBox::down-arrow:off, QDoubleSpinBox::down-arrow:off {{ image: url("{abajo_off}"); }}

/* -- Tablas -------------------------------------------------------------- */
QTableWidget, QTableView {{
    background: white; border: 1px solid {LINEA}; border-radius: 4px;
    gridline-color: {LINEA}; color: {TEXTO};
    selection-background-color: {COBRE_LUZ}; selection-color: {TEXTO};
}}
QHeaderView::section {{
    background-color: {GRAFITO}; color: white; padding: 8px 9px;
    border: none; border-right: 1px solid {GRAFITO_MEDIO};
    border-bottom: 2px solid {COBRE}; font-weight: 600;
}}
QTableCornerButton::section {{ background: {GRAFITO}; border: none; }}
QTableWidget::item:selected {{ background-color: {COBRE_LUZ}; color: {TEXTO}; }}

/* -- Barra lateral -------------------------------------------------------- */
QWidget#lateral {{ background-color: {GRAFITO}; }}
QLabel#marcaLateral {{
    color: #f3efe9; font-family: "{titulo}"; font-size: 23px; font-weight: 700;
    padding: 24px 22px 0 22px;
}}
QLabel#lineaLateral {{
    color: {COBRE_PLANO}; font-size: 10px; font-weight: 600;
    padding: 6px 22px 20px 22px;
}}
QListWidget#menu, QListWidget#menu::item {{ color: #c8cfcd; }}
QListWidget#menu {{
    background-color: {GRAFITO}; border: none; outline: 0; font-size: 14px;
    border-top: 1px solid {GRAFITO_MEDIO};
}}
QListWidget#menu::item {{
    padding: 10px 18px; border-left: 3px solid transparent;
}}
QListWidget#menu::item:hover {{ background-color: {GRAFITO_MEDIO}; color: white; }}
QListWidget#menu::item:selected {{
    background-color: {GRAFITO_MEDIO}; color: white; border-left: 3px solid {COBRE_PLANO};
}}
QListWidget#menu QScrollBar:vertical {{ background: {GRAFITO}; width: 8px; margin: 0; }}
QListWidget#menu QScrollBar::handle:vertical {{ background: #3b4953; border-radius: 3px; }}
QListWidget#menu QScrollBar::handle:vertical:hover {{ background: #4d5d68; }}
QLabel#sesionLateral {{
    color: #9fabb3; padding: 14px 18px; font-size: 12px;
    border-top: 1px solid {GRAFITO_MEDIO};
}}
QPushButton#salirLateral {{
    background: transparent; color: #c8cfcd; border: 1px solid #3b4953;
    border-radius: 7px; margin: 0 18px 18px 18px; padding: 8px; font-weight: 500;
}}
QPushButton#salirLateral:hover {{
    background: {GRAFITO_MEDIO}; color: white; border-color: {COBRE_PLANO};
}}

/* -- Vista de taller (operario) ------------------------------------------ */
QWidget#barraTaller {{ background-color: {GRAFITO}; border-bottom: 3px solid {COBRE}; }}
QLabel#tituloTaller {{
    color: white; font-family: "{titulo}"; font-size: 18px; font-weight: 700;
}}
QPushButton#salirTaller {{
    background: transparent; color: white; border: 1px solid #5a6a74;
    border-radius: 7px; font-size: 16px; padding: 10px 18px;
}}
QPushButton#salirTaller:hover {{ background: {GRAFITO_MEDIO}; border-color: {COBRE_PLANO}; }}

/* -- Ventana de acceso ---------------------------------------------------- */
QLabel#imagenLogin {{ background-color: {GRAFITO}; }}
QLabel#marcaLogin {{
    color: #f3efe9; font-family: "{titulo}"; font-size: 34px; font-weight: 700;
}}
QLabel#lineaLogin {{ color: {COBRE_PLANO}; font-size: 11px; font-weight: 600; }}
QLabel#notaLogin {{ color: #c5cdd2; font-size: 13px; }}
QFrame#filete {{ background-color: {COBRE_PLANO}; border: none; }}
QWidget#formularioLogin {{ background-color: white; }}
QLabel#tituloLogin {{
    font-family: "{titulo}"; font-size: 26px; font-weight: 700; color: {GRAFITO};
}}
QLabel#etiquetaLogin {{ color: {ACERO}; font-size: 13px; font-weight: 500; }}
QLabel#mensajeLogin {{ color: {FALLA}; }}
QLabel#pieLogin {{ color: #8c959b; font-size: 11px; }}
QWidget#formularioLogin QLineEdit {{ padding: 10px 11px; font-size: 14px; }}
QPushButton#botonLogin {{ padding: 11px 16px; font-size: 14px; }}

/* -- Placas (QGroupBox) --------------------------------------------------- */
QGroupBox {{
    background: white; border: 1px solid {LINEA}; border-radius: 11px;
    margin-top: 18px; padding: 14px 12px 12px 12px;
    font-family: "{titulo}"; font-size: 14px; font-weight: 700;
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 14px; padding: 0 6px; color: {GRAFITO};
    font-family: "{titulo}"; font-weight: 700;
}}

/* -- Pestanas ------------------------------------------------------------- */
QTabWidget::pane {{
    border: 1px solid {LINEA}; border-radius: 9px; background: white; top: -1px;
}}
QTabBar::tab {{
    background: transparent; color: {ACERO}; padding: 8px 16px; margin-right: 2px;
    border: none; border-bottom: 2px solid transparent; font-weight: 500;
}}
QTabBar::tab:selected {{ color: {GRAFITO}; border-bottom: 2px solid {COBRE}; }}
QTabBar::tab:hover {{ color: {GRAFITO}; }}

/* -- Barras de desplazamiento --------------------------------------------- */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #c4c9c7; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:horizontal {{ background: #c4c9c7; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:hover {{ background: {ANSI}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* -- Barra de estado, mensajes y emergentes ------------------------------- */
QStatusBar {{ background: white; border-top: 1px solid {LINEA}; color: {ACERO}; }}
QMessageBox {{ background-color: {PAPEL}; }}
QMessageBox QLabel {{ color: {TEXTO}; }}

/* Listas desplegables, listas y calendarios: fondo blanco siempre, para que
   el tema oscuro de Windows no los pinte con texto oscuro sobre fondo oscuro. */
QComboBox QAbstractItemView, QListView, QListWidget, QTreeView {{
    background: white; color: {TEXTO}; border: 1px solid {LINEA};
    selection-background-color: {COBRE_LUZ}; selection-color: {TEXTO};
    outline: 0;
}}
QComboBox QAbstractItemView::item {{ min-height: 26px; padding: 2px 6px; }}
QMenu {{ background: white; color: {TEXTO}; border: 1px solid {LINEA}; }}
QMenu::item {{ padding: 6px 18px; }}
QMenu::item:selected {{ background: {COBRE_LUZ}; color: {TEXTO}; }}
QToolTip {{ background: white; color: {TEXTO}; border: 1px solid {ANSI}; padding: 4px; }}
QCalendarWidget QWidget {{ background: white; color: {TEXTO}; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: {GRAFITO}; }}
QCalendarWidget QToolButton {{ color: white; background: transparent; font-weight: 600; }}
QCalendarWidget QAbstractItemView {{
    selection-background-color: {COBRE}; selection-color: white;
}}
QCalendarWidget QAbstractItemView:disabled {{ color: #a9b0b4; }}
"""


def aplicar_tema(aplicacion) -> None:
    """
    Fija un tema claro independiente de la configuracion de Windows, con las
    fuentes y colores de SITRAFO.

    Con el modo oscuro de Windows, Qt entrega una paleta oscura: las listas
    desplegables y algunas listas quedaban con fondo oscuro y texto oscuro.
    Se pide el esquema de color claro (Qt 6.8 o superior) y se fija una paleta
    clara explicita; se conserva el estilo nativo de Windows.
    """
    try:
        aplicacion.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass
    texto, titulo = cargar_fuentes()
    fuente = QFont(texto)
    fuente.setPointSizeF(10)
    aplicacion.setFont(fuente)

    paleta = QPalette()
    claro = {
        QPalette.Window: PAPEL, QPalette.WindowText: TEXTO,
        QPalette.Base: "#ffffff", QPalette.AlternateBase: "#f6f7f5",
        QPalette.Text: TEXTO, QPalette.Button: "#ffffff", QPalette.ButtonText: TEXTO,
        QPalette.ToolTipBase: "#ffffff", QPalette.ToolTipText: TEXTO,
        QPalette.Highlight: COBRE_LUZ, QPalette.HighlightedText: TEXTO,
        QPalette.PlaceholderText: "#9aa3a8", QPalette.Link: COBRE,
        QPalette.BrightText: "#ffffff", QPalette.Light: "#ffffff",
        QPalette.Midlight: "#eef0ee", QPalette.Mid: ANSI, QPalette.Dark: "#8c959b",
        QPalette.Shadow: ACERO,
    }
    for rol, color in claro.items():
        paleta.setColor(rol, QColor(color))
    for rol in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        paleta.setColor(QPalette.Disabled, rol, QColor("#a9b0b4"))
    aplicacion.setPalette(paleta)
    aplicacion.setStyleSheet(hoja(texto, titulo))
