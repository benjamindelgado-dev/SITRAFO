"""Ficha tecnica del modelo en PDF (RF-CAT-09)."""
from reportlab.platypus import Paragraph

from apps.common.pdf import ESTILOS, construir, datos, espacio, numero, tabla


def ficha_pdf(modelo) -> bytes:
    contenido = [
        Paragraph(modelo.nombre, ESTILOS["titulo"]),
        Paragraph(f"Codigo {modelo.codigo} · Familia {modelo.familia.nombre}",
                  ESTILOS["subtitulo"]),
    ]
    if modelo.descripcion:
        contenido += [Paragraph(modelo.descripcion.replace("\n", "<br/>"), ESTILOS["normal"]),
                      espacio()]
    contenido.append(Paragraph("Especificacion tecnica", ESTILOS["seccion"]))
    filas = [["Parametro", "Valor de referencia", "Obligatorio al solicitar"]]
    for asignado in modelo.parametros_asignados.select_related("parametro"):
        p = asignado.parametro
        valor = asignado.valor_defecto or "A definir por el cliente"
        filas.append([p.nombre, f"{valor} {p.unidad}".strip(),
                      "Si" if asignado.obligatorio else "No"])
    if len(filas) > 1:
        contenido.append(tabla(filas, [70, 64, 40]))
    else:
        contenido.append(Paragraph("Sin parametros tecnicos definidos.", ESTILOS["nota"]))

    precio = modelo.precio_vigente
    if precio:
        contenido += [espacio(), datos([("Precio base de referencia",
                                         f"{numero(precio, 2)} UF + IVA")])]
    contenido += [
        espacio(6),
        Paragraph(
            "Todos los transformadores se fabrican contra pedido (RN-01). El precio final "
            "depende de la especificacion solicitada y se informa en una cotizacion formal. "
            "Solicite su presupuesto en el portal de clientes.", ESTILOS["nota"]),
    ]
    return construir(f"Ficha tecnica {modelo.codigo}", contenido)
