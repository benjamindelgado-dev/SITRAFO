"""Informe de ensayos de una orden de trabajo (RF-CAL-05)."""
from reportlab.platypus import Paragraph

from apps.common.pdf import ESTILOS, construir, datos, espacio, fecha, numero, tabla

from . import services


def _rango(punto) -> str:
    inf, sup = punto.tolerancia_inf, punto.tolerancia_sup
    if inf is not None and sup is not None:
        return f"{numero(inf, 2)} a {numero(sup, 2)}"
    return f">= {numero(inf, 2)}" if inf is not None else f"<= {numero(sup, 2)}"


def informe_ensayos_pdf(orden_trabajo) -> bytes:
    ot = orden_trabajo
    contenido = [
        Paragraph(f"Informe de ensayos {ot.numero}", ESTILOS["titulo"]),
        Paragraph(f"{ot.cantidad} x {ot.modelo.nombre}", ESTILOS["subtitulo"]),
        datos([
            ("Cliente", ot.orden_compra.cliente.razon_social),
            ("Orden de compra", ot.orden_compra.numero),
            ("Estado de la orden", ot.estado.nombre),
            ("Fecha de cierre", fecha(ot.fecha_cierre)),
        ]),
    ]
    for control in ot.controles_calidad.select_related("protocolo", "inspector"):
        contenido += [
            Paragraph(f"{control.protocolo.nombre} v{control.protocolo.version}"
                      f"{' · ' + control.protocolo.norma_referencia if control.protocolo.norma_referencia else ''}",
                      ESTILOS["seccion"]),
            Paragraph(f"Inspector: {control.inspector.username} · Resultado: "
                      f"<b>{control.get_estado_display()}</b>", ESTILOS["normal"]),
            espacio(2),
        ]
        filas = [["Ensayo", "Unidad", "Rango aceptable", "Medido", "Resultado"]]
        for fila in services.estado_de_puntos(control):
            punto, resultado = fila["punto"], fila["resultado"]
            filas.append([
                punto.nombre, punto.unidad, _rango(punto),
                numero(resultado.valor_medido, 2) if resultado else "-",
                ("Conforme" if resultado.conforme else "No conforme") if resultado
                else "Pendiente",
            ])
        contenido.append(tabla(filas, [62, 18, 36, 24, 34]))
    if not ot.controles_calidad.exists():
        contenido.append(Paragraph("La orden aun no tiene controles de calidad.",
                                   ESTILOS["nota"]))
    contenido += [espacio(6), Paragraph(
        "Se informa el ultimo resultado de cada ensayo. Las mediciones anteriores y las no "
        "conformidades con su accion correctiva quedan registradas en SITRAFO.",
        ESTILOS["nota"])]
    return construir(f"Informe de ensayos {ot.numero}", contenido)
