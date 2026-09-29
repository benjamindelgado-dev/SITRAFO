"""
Administracion: matriz de permisos editable (RF-SEG-02) y avisos del sitio
web con periodo de vigencia (RF-ADM-05).
"""
from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import fecha
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QWidget,
)

OPERACIONES = ["leer", "crear", "actualizar", "anular"]


class PanelRoles(PanelBase):
    titulo = "Matriz de permisos"
    subtitulo = ("Operaciones que otorga cada rol sobre cada modulo. El cambio rige desde "
                 "la siguiente accion de cada usuario y queda en la auditoria.")
    columnas = ["Modulo"]

    def construir(self):
        barra = QHBoxLayout()
        barra.addWidget(QLabel("Rol:"))
        self.rol = QComboBox()
        self.rol.currentIndexChanged.connect(self._cargar_matriz)
        barra.addWidget(self.rol, 1)
        self.contenedor.addLayout(barra)
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Modulo", "Leer", "Crear", "Actualizar",
                                              "Anular", "Especial"])
        self.tabla.verticalHeader().setVisible(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(0, QHeaderView.Stretch)
        self.contenedor.addWidget(self.tabla, 1)
        self.editable = self.cliente.puede("rol.actualizar")
        self._cargando = False

    def refrescar(self):
        try:
            roles = self.cliente.roles_disponibles()
        except ErrorAPI as error:
            return self.manejar_error(error)
        actual = self.rol.currentData()
        self.rol.blockSignals(True)
        self.rol.clear()
        for r in roles:
            self.rol.addItem(f"{r['nombre']} ({r['cantidad_permisos']} permisos)", r["id_rol"])
        if actual:
            self.rol.setCurrentIndex(max(0, self.rol.findData(actual)))
        self.rol.blockSignals(False)
        self._cargar_matriz()

    def _cargar_matriz(self):
        if self.rol.currentData() is None:
            return
        try:
            datos = self.cliente.matriz_rol(self.rol.currentData())
        except ErrorAPI as error:
            return self.manejar_error(error)
        self._cargando = True
        self.tabla.setRowCount(len(datos["modulos"]))
        for i, m in enumerate(datos["modulos"]):
            self.tabla.setItem(i, 0, QTableWidgetItem(m["descripcion"]))
            especiales = [op for op in m["operaciones"] if op not in OPERACIONES]
            for j, op in enumerate(OPERACIONES + especiales[:1], start=1):
                if op not in m["operaciones"]:
                    continue
                casilla = QCheckBox(op if j == 5 else "")
                casilla.setChecked(m["operaciones"][op])
                casilla.setEnabled(self.editable)
                casilla.toggled.connect(
                    lambda marcado, codigo=f"{m['modulo']}.{op}": self._cambiar(codigo, marcado))
                contenedor = QWidget()
                capa = QHBoxLayout(contenedor)
                capa.addWidget(casilla)
                capa.setAlignment(Qt.AlignCenter)
                capa.setContentsMargins(0, 0, 0, 0)
                self.tabla.setCellWidget(i, j, contenedor)
        self._cargando = False

    def _cambiar(self, codigo: str, otorgar: bool):
        if self._cargando:
            return
        try:
            self.cliente.cambiar_permiso_rol(self.rol.currentData(), codigo, otorgar)
        except ErrorAPI as error:
            self.manejar_error(error)
        self.refrescar()


class DialogoAviso(QDialog):
    TIPOS = [("informativo", "Informativo"), ("advertencia", "Advertencia"),
             ("mantencion", "Mantencion")]

    def __init__(self, api: ClienteAPI, parent=None):
        super().__init__(parent)
        self.api = api
        self.setWindowTitle("Nuevo aviso del sitio")
        self.setMinimumWidth(480)
        formulario = QFormLayout(self)
        self.titulo = QLineEdit()
        self.cuerpo = QTextEdit()
        self.cuerpo.setFixedHeight(90)
        self.tipo = QComboBox()
        for codigo, nombre in self.TIPOS:
            self.tipo.addItem(nombre, codigo)
        self.desde = QDateTimeEdit(QDateTime.currentDateTime())
        self.hasta = QDateTimeEdit(QDateTime.currentDateTime().addDays(7))
        for campo in (self.desde, self.hasta):
            campo.setCalendarPopup(True)
            campo.setDisplayFormat("dd-MM-yyyy HH:mm")
        formulario.addRow("Titulo:", self.titulo)
        formulario.addRow("Mensaje:", self.cuerpo)
        formulario.addRow("Tipo:", self.tipo)
        formulario.addRow("Publicar desde:", self.desde)
        formulario.addRow("Hasta:", self.hasta)
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Ok).setText("Publicar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        formulario.addRow(botones)

    def _guardar(self):
        if self.hasta.dateTime() <= self.desde.dateTime():
            QMessageBox.warning(self, "Vigencia", "La fecha final debe ser posterior al inicio.")
            return
        try:
            self.api.crear_aviso({
                "titulo": self.titulo.text().strip(), "cuerpo": self.cuerpo.toPlainText().strip(),
                "tipo": self.tipo.currentData(),
                "vigente_desde": self.desde.dateTime().toString(Qt.ISODate),
                "vigente_hasta": self.hasta.dateTime().toString(Qt.ISODate), "activo": True})
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo publicar", error.mensaje)
            return
        self.accept()


class PanelAvisos(PanelBase):
    titulo = "Avisos del sitio"
    subtitulo = ("Mensajes que el cliente ve en la web solo durante su periodo de vigencia "
                 "(por ejemplo, cierre por feriado o cambio de horario).")
    columnas = ["Titulo", "Tipo", "Desde", "Hasta", "Estado"]

    def construir(self):
        self.tabla = self.crear_tabla()
        self.contenedor.addWidget(self.tabla, 1)
        acciones = QHBoxLayout()
        nuevo = QPushButton("Nuevo aviso")
        nuevo.setObjectName("exito")
        nuevo.clicked.connect(self._nuevo)
        retirar = QPushButton("Retirar aviso")
        retirar.setObjectName("peligro")
        retirar.clicked.connect(self._retirar)
        for boton in (nuevo, retirar):
            boton.setVisible(self.cliente.puede("canal_web.actualizar"))
            acciones.addWidget(boton)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)
        self.datos = []

    def refrescar(self):
        try:
            self.datos = self.cliente.avisos()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.llenar(self.tabla, [
            [a["titulo"], a["tipo"].capitalize(),
             fecha(a["vigente_desde"]) + " " + a["vigente_desde"][11:16],
             (fecha(a["vigente_hasta"]) + " " + a["vigente_hasta"][11:16])
             if a["vigente_hasta"] else "sin termino",
             "Publicado" if a["esta_publicado"] else ("Retirado" if not a["activo"]
                                                      else "Fuera de vigencia")]
            for a in self.datos])

    def _nuevo(self):
        if DialogoAviso(self.cliente, self).exec():
            self.refrescar()

    def _retirar(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.datos):
            QMessageBox.information(self, "Avisos", "Seleccione un aviso.")
            return
        try:
            self.cliente.actualizar_aviso(self.datos[fila]["id_aviso"], {"activo": False})
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.refrescar()
