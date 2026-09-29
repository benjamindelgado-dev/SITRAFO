"""
Generacion de documentos PDF con la identidad de SITRAFO (reportlab).

Base comun para la cotizacion (RF-COM-09), la ficha tecnica (RF-CAT-09) y
el informe de ensayos (RF-CAL-05): encabezado, pie con fecha y numero de
pagina, tablas con el mismo estilo y formato chileno de numeros y fechas.
"""
from decimal import Decimal
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ACERO = colors.HexColor("#1b242b")
COBRE = colors.HexColor("#8a4b24")
TENUE = colors.HexColor("#4a5760")
LINEA = colors.HexColor("#d5d9d6")

_base = getSampleStyleSheet()
ESTILOS = {
    "titulo": ParagraphStyle("titulo", parent=_base["Title"], fontSize=18, textColor=ACERO,
                             alignment=0, spaceAfter=2),
    "subtitulo": ParagraphStyle("subtitulo", parent=_base["Normal"], fontSize=10,
                                textColor=TENUE, spaceAfter=10),
    "seccion": ParagraphStyle("seccion", parent=_base["Heading3"], textColor=COBRE,
                              spaceBefore=10, spaceAfter=4),
    "normal": ParagraphStyle("normal", parent=_base["Normal"], fontSize=9.5, leading=13),
    "nota": ParagraphStyle("nota", parent=_base["Normal"], fontSize=8, textColor=TENUE,
                           leading=11),
    "derecha": ParagraphStyle("derecha", parent=_base["Normal"], fontSize=9.5,
                              alignment=TA_RIGHT),
}


def numero(valor, decimales: int = 2) -> str:
    """1234567.5 -> '1.234.567,50' (formato chileno)."""
    if valor is None:
        return "-"
    texto = f"{Decimal(valor):,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pesos(valor) -> str:
    return "$" + numero(valor, 0)


def fecha(valor) -> str:
    return valor.strftime("%d-%m-%Y") if valor else "-"


def tabla(filas: list[list], anchos: list[float], encabezado: bool = True) -> Table:
    celdas = []
    for i, fila in enumerate(filas):
        if encabezado and i == 0:
            celdas.append([Paragraph(f"<font color='white'><b>{c}</b></font>", ESTILOS["normal"])
                           for c in fila])
        else:
            celdas.append([c if isinstance(c, Paragraph) else Paragraph(str(c), ESTILOS["normal"])
                           for c in fila])
    t = Table(celdas, colWidths=[a * mm for a in anchos], repeatRows=1 if encabezado else 0)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if encabezado:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), ACERO))
    t.setStyle(TableStyle(estilo))
    return t


def datos(pares: list[tuple[str, str]], anchos=(45, 125)) -> Table:
    """Tabla etiqueta-valor sin encabezado."""
    filas = [[Paragraph(f"<font color='#4a5760'>{e}</font>", ESTILOS["normal"]),
              Paragraph(str(v), ESTILOS["normal"])] for e, v in pares]
    t = Table(filas, colWidths=[a * mm for a in anchos])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.3, LINEA),
                           ("TOPPADDING", (0, 0), (-1, -1), 3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def construir(titulo: str, contenido: list, pagina=A4) -> bytes:
    """Arma el PDF con encabezado y pie comunes y devuelve sus bytes."""
    memoria = BytesIO()
    emitido = timezone.localtime().strftime("%d-%m-%Y %H:%M")

    def marco(lienzo, documento):
        lienzo.saveState()
        lienzo.setFillColor(ACERO)
        ancho, alto = pagina
        lienzo.rect(0, alto - 16 * mm, ancho, 16 * mm, stroke=0, fill=1)
        lienzo.setFillColor(colors.white)
        lienzo.setFont("Helvetica-Bold", 13)
        lienzo.drawString(18 * mm, alto - 10.5 * mm, "SITRAFO")
        lienzo.setFont("Helvetica", 9)
        lienzo.drawRightString(ancho - 18 * mm, alto - 10.5 * mm, titulo)
        lienzo.setFillColor(TENUE)
        lienzo.setFont("Helvetica", 7.5)
        lienzo.drawString(18 * mm, 10 * mm, f"Documento generado por SITRAFO el {emitido}")
        lienzo.drawRightString(ancho - 18 * mm, 10 * mm, f"Pagina {documento.page}")
        lienzo.restoreState()

    documento = SimpleDocTemplate(memoria, pagesize=pagina, title=titulo, author="SITRAFO",
                                  leftMargin=18 * mm, rightMargin=18 * mm,
                                  topMargin=24 * mm, bottomMargin=18 * mm)
    documento.build(contenido, onFirstPage=marco, onLaterPages=marco)
    return memoria.getvalue()


def espacio(alto: float = 4):
    return Spacer(1, alto * mm)
