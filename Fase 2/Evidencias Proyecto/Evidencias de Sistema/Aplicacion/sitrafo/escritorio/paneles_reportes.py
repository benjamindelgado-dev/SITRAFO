"""
Reportes de gestion (RF-REP-01 a RF-REP-06).

El usuario elige el reporte y el periodo, lo ve en pantalla y lo exporta a
Excel o PDF. Los calculos los hace el backend; aqui solo se muestran.
"""
from cliente_api import ErrorAPI
from paneles import PanelBase
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
)

REPORTES = [
    ("Indicadores comerciales", "comercial"),
    ("Costo estimado contra real", "costos"),
    ("Consumo de materiales", "consumos"),
    ("Horas hombre", "horas"),
    ("Cumplimiento de plazos", "plazos"),
]


class PanelReportes(PanelBase):
    titulo = "Reportes"
    subtitulo = "Indicadores de gestion por periodo, exportables a Excel y PDF."
    columnas = ["-"]

    def construir(self):
        barra = QHBoxLayout()
        self.tipo = QComboBox()
        for nombre, codigo in REPORTES:
            self.tipo.addItem(nombre, codigo)
        self.desde = QDateEdit(QDate.currentDate().addDays(-90))
        self.hasta = QDateEdit(QDate.currentDate())
        for campo in (self.desde, self.hasta):
            campo.setCalendarPopup(True)
            campo.setDisplayFormat("dd-MM-yyyy")
        generar = QPushButton("Generar")
        generar.clicked.connect(self.refrescar)
        barra.addWidget(self.tipo, 1)
        barra.addWidget(QLabel("Desde"))
        barra.addWidget(self.desde)
        barra.addWidget(QLabel("Hasta"))
        barra.addWidget(self.hasta)
        barra.addWidget(generar)
        self.contenedor.addLayout(barra)

        self.descripcion = QLabel("")
        self.descripcion.setObjectName("nota")
        self.descripcion.setWordWrap(True)
        self.contenedor.addWidget(self.descripcion)
        self.tabla = self.crear_tabla()
        self.contenedor.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        for texto, formato in (("Exportar a Excel", "xlsx"), ("Exportar a PDF", "pdf")):
            boton = QPushButton(texto)
            boton.setObjectName("secundario")
            boton.clicked.connect(lambda _=False, f=formato: self._exportar(f))
            acciones.addWidget(boton)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)

    def _periodo(self):
        return (self.desde.date().toString("yyyy-MM-dd"),
                self.hasta.date().toString("yyyy-MM-dd"))

    def refrescar(self):
        desde, hasta = self._periodo()
        try:
            reporte = self.cliente.reporte(self.tipo.currentData(), desde, hasta)
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.descripcion.setText(f"{reporte['descripcion']} Periodo: {reporte['periodo']}.")
        filas = reporte["filas"] + ([reporte["totales"]] if reporte["totales"] else [])
        self.tabla.clear()
        self.tabla.setColumnCount(len(reporte["columnas"]))
        self.tabla.setHorizontalHeaderLabels(reporte["columnas"])
        self.tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                item = QTableWidgetItem(self._formato(valor))
                if reporte["totales"] and i == len(filas) - 1:
                    fuente = item.font()
                    fuente.setBold(True)
                    item.setFont(fuente)
                self.tabla.setItem(i, j, item)

    @staticmethod
    def _formato(valor: str) -> str:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return valor
        if numero.is_integer() and "." not in valor:
            return valor
        texto = f"{numero:,.2f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")

    def _exportar(self, formato: str):
        desde, hasta = self._periodo()
        codigo = self.tipo.currentData()
        sugerido = f"SITRAFO-{codigo}-{desde}-{hasta}.{formato}"
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar reporte", sugerido,
            "Excel (*.xlsx)" if formato == "xlsx" else "PDF (*.pdf)")
        if not ruta:
            return
        try:
            contenido = self.cliente.reporte(codigo, desde, hasta, formato)
        except ErrorAPI as error:
            return self.manejar_error(error)
        with open(ruta, "wb") as archivo:
            archivo.write(contenido)
        QMessageBox.information(self, "Reporte exportado", f"Guardado en:\n{ruta}")
