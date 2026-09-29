"""Cotizacion en PDF (RF-COM-09)."""
from reportlab.platypus import Paragraph

from apps.common.pdf import ESTILOS, construir, datos, espacio, fecha, numero, pesos, tabla


def cotizacion_pdf(cotizacion) -> bytes:
    c = cotizacion
    contenido = [
        Paragraph(f"Cotizacion {c.numero}", ESTILOS["titulo"]),
        Paragraph(f"Version {c.version} · {c.estado.nombre}", ESTILOS["subtitulo"]),
        datos([
            ("Cliente", f"{c.cliente.razon_social} (RUT {c.cliente.rut})"),
            ("Solicitud", c.solicitud.numero),
            ("Ejecutivo", c.ejecutivo.email or c.ejecutivo.username),
            ("Fecha de emision", fecha(c.fecha_valor_uf)),
            ("Valida hasta", fecha(c.vence_el)),
            ("Plazo de fabricacion", f"{c.plazo_dias_habiles} dias habiles"
             if c.plazo_dias_habiles else "-"),
            ("Entrega comprometida", fecha(c.fecha_entrega)),
        ]),
        Paragraph("Detalle", ESTILOS["seccion"]),
    ]
    filas = [["Modelo", "Cantidad", "Precio unitario", "Subtotal"]]
    for linea in c.lineas.select_related("modelo"):
        filas.append([f"{linea.modelo.codigo} — {linea.modelo.nombre}", linea.cantidad,
                      f"{numero(linea.precio_uf, 4)} UF",
                      f"{numero(linea.precio_uf * linea.cantidad, 4)} UF"])
    contenido.append(tabla(filas, [82, 20, 34, 38]))
    contenido.append(espacio())

    bruto = sum((linea.precio_uf * linea.cantidad for linea in c.lineas.all()), 0)
    resumen = [("Subtotal", f"{numero(bruto, 4)} UF")]
    if c.descuento_pct:
        resumen.append(("Descuento", f"{numero(c.descuento_pct)} %"))
    resumen += [
        ("<b>Total</b>", f"<b>{numero(c.total_uf, 4)} UF</b>"),
        ("Valor UF congelado", f"{pesos(c.valor_uf)} ({fecha(c.fecha_valor_uf)})"),
        ("<b>Total en pesos</b>", f"<b>{pesos(c.total_clp)}</b>"),
    ]
    contenido.append(datos(resumen, anchos=(120, 54)))
    contenido += [
        espacio(6),
        Paragraph("Condiciones", ESTILOS["seccion"]),
        Paragraph(
            "Los montos se expresan en Unidades de Fomento. El valor en pesos se calculo con "
            "la UF del dia de emision, que queda congelada en este documento. La cotizacion "
            "puede aceptarse o rechazarse desde el portal de clientes mientras este vigente. "
            "La aceptacion origina una orden de compra con un anticipo segun las condiciones "
            "vigentes y el saldo contra entrega.", ESTILOS["nota"]),
    ]
    return construir(f"Cotizacion {c.numero}", contenido)
