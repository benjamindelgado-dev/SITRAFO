"""
Alta y edicion de modelos del catalogo (RF-CAT-01 a RF-CAT-04).

El formulario define lo que el cliente ve en la web: nombre, descripcion y
los parametros tecnicos que debera completar al solicitar un presupuesto.
El precio base se versiona en el backend (RN-17) y solo lo puede fijar un
rol con permiso sobre precios.
"""
from cliente_api import ClienteAPI, ErrorAPI
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DialogoModelo(QDialog):
    """Formulario de un modelo; sin id_modelo crea uno nuevo."""

    def __init__(self, cliente: ClienteAPI, id_modelo: int | None = None, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.id_modelo = id_modelo
        self.resultado = None
        self.modelo = cliente.modelo(id_modelo) if id_modelo else None
        self.parametros = cliente.parametros_tecnicos()
        self.setWindowTitle("Editar modelo" if id_modelo else "Nuevo modelo del catalogo")
        self.setMinimumSize(640, 620)
        self._construir()

    # -- Construccion ------------------------------------------------------
    def _construir(self):
        capa = QVBoxLayout(self)

        datos = QGroupBox("Datos del modelo")
        formulario = QFormLayout(datos)

        fila_familia = QHBoxLayout()
        self.familia = QComboBox()
        self._cargar_familias()
        fila_familia.addWidget(self.familia, 1)
        nueva = QPushButton("Nueva familia")
        nueva.setObjectName("secundario")
        nueva.clicked.connect(self._nueva_familia)
        nueva.setVisible(self.cliente.puede("catalogo.crear"))
        fila_familia.addWidget(nueva)
        formulario.addRow("Familia:", fila_familia)

        self.codigo = QLineEdit()
        self.codigo.setPlaceholderText("Ej.: TD-500")
        self.codigo.setMaxLength(40)
        formulario.addRow("Codigo:", self.codigo)
        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Nombre comercial que vera el cliente")
        self.nombre.setMaxLength(150)
        formulario.addRow("Nombre:", self.nombre)
        self.descripcion = QTextEdit()
        self.descripcion.setPlaceholderText("Descripcion tecnica para la ficha del catalogo web")
        self.descripcion.setFixedHeight(80)
        formulario.addRow("Descripcion:", self.descripcion)

        self.precio = QDoubleSpinBox()
        self.precio.setRange(0, 1_000_000)
        self.precio.setDecimals(4)
        self.precio.setSuffix(" UF")
        self.puede_precio = self.cliente.puede("precio.actualizar")
        self.precio.setEnabled(self.puede_precio)
        nota_precio = QLabel(
            "Un cambio de precio abre una nueva vigencia; el anterior se conserva."
            if self.puede_precio else "Su rol no autoriza fijar precios."
        )
        nota_precio.setObjectName("nota")
        formulario.addRow("Precio base:", self.precio)
        formulario.addRow("", nota_precio)
        capa.addWidget(datos)

        grupo = QGroupBox("Parametros tecnicos que el cliente completa al solicitar")
        gp = QVBoxLayout(grupo)
        self.tabla = QTableWidget(len(self.parametros), 4)
        self.tabla.setHorizontalHeaderLabels(["Incluir", "Parametro", "Valor por defecto",
                                              "Obligatorio"])
        self.tabla.verticalHeader().setVisible(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.Stretch)
        cabecera.setSectionResizeMode(2, QHeaderView.Stretch)
        self.filas = []
        for i, p in enumerate(self.parametros):
            incluir = QCheckBox()
            nombre = QTableWidgetItem(f"{p['nombre']}" + (f" ({p['unidad']})" if p["unidad"]
                                                          else ""))
            nombre.setFlags(Qt.ItemIsEnabled)
            if p["tipo_dato"] == "lista":
                valor = QComboBox()
                valor.addItem("")
                valor.addItems([v["valor"] for v in p["valores"]])
            else:
                valor = QLineEdit()
                valor.setPlaceholderText("numero" if p["tipo_dato"] == "numerico" else "texto")
            obligatorio = QCheckBox()
            obligatorio.setChecked(p["obligatorio"])
            self.tabla.setCellWidget(i, 0, self._centrado(incluir))
            self.tabla.setItem(i, 1, nombre)
            self.tabla.setCellWidget(i, 2, valor)
            self.tabla.setCellWidget(i, 3, self._centrado(obligatorio))
            self.filas.append((p, incluir, valor, obligatorio))
        gp.addWidget(self.tabla)
        capa.addWidget(grupo, 1)

        aviso = QLabel("El modelo se crea sin publicar. Revise la ficha y publiquelo desde "
                       "el panel Catalogo cuando este listo.")
        aviso.setObjectName("nota")
        aviso.setWordWrap(True)
        capa.addWidget(aviso)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)

        if self.modelo:
            self._llenar()

    @staticmethod
    def _centrado(widget):
        contenedor = QWidget()
        capa = QHBoxLayout(contenedor)
        capa.addWidget(widget)
        capa.setAlignment(Qt.AlignCenter)
        capa.setContentsMargins(0, 0, 0, 0)
        return contenedor

    def _cargar_familias(self, seleccionar: int | None = None):
        self.familia.clear()
        for f in self.cliente.familias():
            if f["activo"]:
                self.familia.addItem(f["nombre"], f["id_familia"])
        if seleccionar:
            self.familia.setCurrentIndex(self.familia.findData(seleccionar))

    def _llenar(self):
        m = self.modelo
        self.familia.setCurrentIndex(self.familia.findData(m["familia"]["id_familia"]))
        self.codigo.setText(m["codigo"])
        self.codigo.setEnabled(False)     # el codigo identifica al modelo
        self.nombre.setText(m["nombre"])
        self.descripcion.setPlainText(m.get("descripcion", ""))
        self.precio.setValue(float(m.get("precio_vigente") or 0))
        asignados = {a["parametro"]["id_parametro"]: a for a in m["parametros_asignados"]}
        for p, incluir, valor, obligatorio in self.filas:
            asignado = asignados.get(p["id_parametro"])
            incluir.setChecked(asignado is not None)
            if asignado:
                obligatorio.setChecked(asignado["obligatorio"])
                if isinstance(valor, QComboBox):
                    valor.setCurrentText(asignado["valor_defecto"])
                else:
                    valor.setText(asignado["valor_defecto"])

    def _nueva_familia(self):
        nombre, ok = QInputDialog.getText(self, "Nueva familia", "Nombre de la familia:")
        if not ok or not nombre.strip():
            return
        try:
            familia = self.cliente.crear_familia(nombre.strip())
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo crear", error.mensaje)
            return
        self._cargar_familias(familia["id_familia"])

    # -- Guardado ------------------------------------------------------------
    def _guardar(self):
        if not self.nombre.text().strip() or not self.codigo.text().strip():
            QMessageBox.warning(self, "Faltan datos", "Indique el codigo y el nombre.")
            return
        if self.familia.currentData() is None:
            QMessageBox.warning(self, "Faltan datos", "Elija o cree una familia.")
            return

        parametros = []
        for p, incluir, valor, obligatorio in self.filas:
            if incluir.isChecked():
                texto = valor.currentText() if isinstance(valor, QComboBox) else valor.text()
                parametros.append({"parametro": p["id_parametro"],
                                   "valor_defecto": texto.strip(),
                                   "obligatorio": obligatorio.isChecked()})

        datos = {
            "familia": self.familia.currentData(),
            "codigo": self.codigo.text().strip(),
            "nombre": self.nombre.text().strip(),
            "descripcion": self.descripcion.toPlainText().strip(),
            "parametros": parametros,
        }
        if self.puede_precio and self.precio.value() > 0:
            datos["precio_base_uf"] = f"{self.precio.value():.4f}"

        try:
            if self.id_modelo:
                self.resultado = self.cliente.actualizar_modelo(self.id_modelo, datos)
            else:
                self.resultado = self.cliente.crear_modelo(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()
