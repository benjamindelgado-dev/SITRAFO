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


# ---------------------------------------------------------------------------
# Familias de producto (RF-CAT-01)
# ---------------------------------------------------------------------------
def _celdas(tabla: QTableWidget, filas: list[list[str]]):
    tabla.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            tabla.setItem(i, j, QTableWidgetItem(str(valor)))


def _tabla_simple(columnas: list[str]) -> QTableWidget:
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(QTableWidget.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    tabla.setSelectionMode(QTableWidget.SingleSelection)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return tabla


class DialogoFamilias(QDialog):
    """Crear, renombrar, desactivar y reactivar familias de producto."""

    def __init__(self, cliente: ClienteAPI, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.setWindowTitle("Familias de producto")
        self.resize(640, 420)
        capa = QVBoxLayout(self)
        nota = QLabel("Las familias agrupan los modelos del catalogo. Una familia no se elimina: "
                      "se desactiva, y solo si ya no tiene modelos vigentes.")
        nota.setWordWrap(True)
        nota.setObjectName("subtitulo")
        capa.addWidget(nota)
        self.tabla = _tabla_simple(["Nombre", "Descripcion", "Estado"])
        self.tabla.doubleClicked.connect(self._editar)
        capa.addWidget(self.tabla, 1)
        fila = QHBoxLayout()
        for texto, accion, estilo in (("Nueva familia", self._nueva, ""),
                                      ("Editar", self._editar, "secundario"),
                                      ("Desactivar", lambda: self._estado(False), "peligro"),
                                      ("Reactivar", lambda: self._estado(True), "exito")):
            boton = QPushButton(texto)
            if estilo:
                boton.setObjectName(estilo)
            boton.clicked.connect(accion)
            fila.addWidget(boton)
        fila.addStretch()
        cerrar = QPushButton("Cerrar")
        cerrar.setObjectName("secundario")
        cerrar.clicked.connect(self.accept)
        fila.addWidget(cerrar)
        capa.addLayout(fila)
        self.familias = []
        self._cargar()

    def _cargar(self):
        try:
            self.familias = self.cliente.todas_las_familias()
        except ErrorAPI as error:
            QMessageBox.warning(self, "Familias", error.mensaje)
            return
        _celdas(self.tabla, [[f["nombre"], f.get("descripcion", ""),
                              "Activa" if f["activo"] else "Inactiva"] for f in self.familias])

    def _actual(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.familias):
            QMessageBox.information(self, "Familias", "Seleccione una familia.")
            return None
        return self.familias[fila]

    def _pedir(self, titulo, familia=None):
        dialogo = QDialog(self)
        dialogo.setWindowTitle(titulo)
        dialogo.setMinimumWidth(420)
        formulario = QFormLayout(dialogo)
        nombre, descripcion = QLineEdit(), QLineEdit()
        if familia:
            nombre.setText(familia["nombre"])
            descripcion.setText(familia.get("descripcion", ""))
        formulario.addRow("Nombre:", nombre)
        formulario.addRow("Descripcion:", descripcion)
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        formulario.addRow(botones)
        if dialogo.exec() != QDialog.Accepted or not nombre.text().strip():
            return None
        return {"nombre": nombre.text().strip(), "descripcion": descripcion.text().strip()}

    def _nueva(self):
        datos = self._pedir("Nueva familia")
        if datos:
            self._ejecutar(lambda: self.cliente.crear("familias/", datos))

    def _editar(self, *_):
        familia = self._actual()
        if familia:
            datos = self._pedir("Editar familia", familia)
            if datos:
                self._ejecutar(lambda: self.cliente.actualizar_familia(familia["id_familia"],
                                                                       datos))

    def _estado(self, activar: bool):
        familia = self._actual()
        if not familia:
            return
        if activar:
            self._ejecutar(lambda: self.cliente.reactivar_familia(familia["id_familia"]))
        elif QMessageBox.question(self, "Desactivar familia",
                                  f"¿Desactivar la familia «{familia['nombre']}»?"
                                  ) == QMessageBox.Yes:
            self._ejecutar(lambda: self.cliente.desactivar_familia(familia["id_familia"]))

    def _ejecutar(self, operacion):
        try:
            operacion()
        except ErrorAPI as error:
            QMessageBox.warning(self, "Familias", error.mensaje)
        self._cargar()


# ---------------------------------------------------------------------------
# Parametros tecnicos y formulario de solicitud (RF-CAT-03, RF-ADM-04)
# ---------------------------------------------------------------------------
TIPOS = [("numerico", "Numerico"), ("lista", "Lista de valores"), ("texto", "Texto")]


class DialogoParametro(QDialog):
    """Alta o edicion de un parametro tecnico, con su rango y su lista de valores."""

    def __init__(self, cliente: ClienteAPI, parametro: dict | None = None, parent=None):
        super().__init__(parent)
        self.cliente, self.parametro = cliente, parametro
        self.setWindowTitle("Editar parametro tecnico" if parametro else "Nuevo parametro tecnico")
        self.setMinimumWidth(520)
        capa = QVBoxLayout(self)
        formulario = QFormLayout()
        self.codigo, self.nombre, self.unidad = QLineEdit(), QLineEdit(), QLineEdit()
        self.codigo.setPlaceholderText("por ejemplo: frecuencia_hz (sin espacios)")
        self.unidad.setPlaceholderText("vacio si no tiene unidad")
        self.tipo = QComboBox()
        for codigo, nombre in TIPOS:
            self.tipo.addItem(nombre, codigo)
        self.obligatorio = QCheckBox("Obligatorio en el formulario de solicitud web")
        self.fija = QCheckBox("Lo fija el modelo de referencia (debe coincidir con el del modelo)")
        self.con_minimo, self.con_maximo = QCheckBox("Minimo"), QCheckBox("Maximo")
        self.minimo, self.maximo = QDoubleSpinBox(), QDoubleSpinBox()
        for caja in (self.minimo, self.maximo):
            caja.setRange(-1e9, 1e9)
            caja.setDecimals(3)
        rango = QHBoxLayout()
        for check, caja in ((self.con_minimo, self.minimo), (self.con_maximo, self.maximo)):
            check.toggled.connect(caja.setEnabled)
            caja.setEnabled(False)
            rango.addWidget(check)
            rango.addWidget(caja, 1)
        self.fila_rango = QWidget()
        self.fila_rango.setLayout(rango)
        rango.setContentsMargins(0, 0, 0, 0)
        formulario.addRow("Codigo:", self.codigo)
        formulario.addRow("Nombre visible:", self.nombre)
        formulario.addRow("Unidad:", self.unidad)
        formulario.addRow("Tipo de dato:", self.tipo)
        formulario.addRow("Rango:", self.fila_rango)
        self.formulario = formulario
        formulario.addRow("", self.obligatorio)
        formulario.addRow("", self.fija)
        capa.addLayout(formulario)

        self.grupo_valores = QGroupBox("Valores de la lista")
        capa_valores = QVBoxLayout(self.grupo_valores)
        self.tabla_valores = _tabla_simple(["Valor", "Estado"])
        capa_valores.addWidget(self.tabla_valores)
        fila_valores = QHBoxLayout()
        for texto, accion, estilo in (("Agregar valor", self._agregar_valor, ""),
                                      ("Retirar", lambda: self._estado_valor(False), "peligro"),
                                      ("Restituir", lambda: self._estado_valor(True), "exito")):
            boton = QPushButton(texto)
            if estilo:
                boton.setObjectName(estilo)
            boton.clicked.connect(accion)
            fila_valores.addWidget(boton)
        fila_valores.addStretch()
        capa_valores.addLayout(fila_valores)
        capa.addWidget(self.grupo_valores)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Ok).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cerrar")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)
        self.tipo.currentIndexChanged.connect(self._segun_tipo)

        if parametro:
            self.codigo.setText(parametro["codigo"])
            self.codigo.setReadOnly(True)
            self.nombre.setText(parametro["nombre"])
            self.unidad.setText(parametro.get("unidad", ""))
            self.tipo.setCurrentIndex(max(0, self.tipo.findData(parametro["tipo_dato"])))
            self.tipo.setEnabled(not parametro.get("en_uso"))
            self.obligatorio.setChecked(bool(parametro.get("obligatorio")))
            self.fija.setChecked(bool(parametro.get("fija_el_modelo")))
            for check, caja, valor in ((self.con_minimo, self.minimo, parametro.get("valor_minimo")),
                                       (self.con_maximo, self.maximo, parametro.get("valor_maximo"))):
                check.setChecked(valor is not None)
                if valor is not None:
                    caja.setValue(float(valor))
        else:
            self.obligatorio.setChecked(True)
        self._segun_tipo()
        self._llenar_valores()

    def _segun_tipo(self):
        tipo = self.tipo.currentData()
        self.fila_rango.setEnabled(tipo == "numerico")
        if hasattr(self.formulario, "setRowVisible"):      # Qt 6.4 o superior
            self.formulario.setRowVisible(self.fila_rango, tipo == "numerico")
        # Los valores se administran sobre un parametro ya guardado
        self.grupo_valores.setVisible(tipo == "lista")
        self.grupo_valores.setEnabled(self.parametro is not None)
        self.grupo_valores.setTitle("Valores de la lista" if self.parametro else
                                    "Valores de la lista (guarde el parametro para agregarlos)")

    def _llenar_valores(self):
        valores = (self.parametro or {}).get("valores", [])
        self.valores = sorted(valores, key=lambda v: v.get("orden", 0))
        _celdas(self.tabla_valores, [[v["valor"], "Vigente" if v.get("activo", True) else
                                      "Retirado"] for v in self.valores])

    def _datos(self):
        datos = {"codigo": self.codigo.text().strip(), "nombre": self.nombre.text().strip(),
                 "unidad": self.unidad.text().strip(), "tipo_dato": self.tipo.currentData(),
                 "obligatorio": self.obligatorio.isChecked(),
                 "fija_el_modelo": self.fija.isChecked(),
                 "valor_minimo": None, "valor_maximo": None}
        if datos["tipo_dato"] == "numerico":
            if self.con_minimo.isChecked():
                datos["valor_minimo"] = f"{self.minimo.value():.3f}"
            if self.con_maximo.isChecked():
                datos["valor_maximo"] = f"{self.maximo.value():.3f}"
        return datos

    def _guardar(self):
        datos = self._datos()
        if not datos["codigo"] or not datos["nombre"]:
            QMessageBox.warning(self, "Parametro", "Indique el codigo y el nombre.")
            return
        try:
            if self.parametro:
                self.parametro = self.cliente.actualizar_parametro_tecnico(
                    self.parametro["id_parametro"], datos)
            else:
                self.parametro = self.cliente.crear_parametro_tecnico(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        if datos["tipo_dato"] == "lista" and not self.parametro.get("valores"):
            # Recien creado: queda abierto para cargar sus valores
            self.codigo.setReadOnly(True)
            self._segun_tipo()
            QMessageBox.information(self, "Parametro guardado",
                                    "Ahora agregue los valores de la lista.")
            return
        self.accept()

    def _agregar_valor(self):
        valor, aceptado = QInputDialog.getText(self, "Agregar valor", "Valor:")
        if not aceptado or not valor.strip():
            return
        try:
            self.parametro = self.cliente.agregar_valor_parametro(
                self.parametro["id_parametro"], valor.strip())
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo agregar", error.mensaje)
            return
        self._llenar_valores()

    def _estado_valor(self, activo: bool):
        fila = self.tabla_valores.currentRow()
        if not 0 <= fila < len(self.valores):
            QMessageBox.information(self, "Valores", "Seleccione un valor.")
            return
        try:
            self.parametro = self.cliente.estado_valor_parametro(
                self.parametro["id_parametro"], self.valores[fila]["id_valor"], activo)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo cambiar", error.mensaje)
            return
        self._llenar_valores()


class DialogoParametrosTecnicos(QDialog):
    """Listado de parametros tecnicos: definen el formulario de solicitud web."""

    def __init__(self, cliente: ClienteAPI, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.setWindowTitle("Parametros tecnicos y formulario de solicitud")
        self.resize(900, 480)
        capa = QVBoxLayout(self)
        nota = QLabel("Cada parametro es un campo de la especificacion tecnica que el cliente "
                      "completa al pedir un presupuesto en la web. Aqui se define su tipo, si "
                      "es obligatorio, el rango aceptable y los valores de las listas.")
        nota.setWordWrap(True)
        nota.setObjectName("subtitulo")
        capa.addWidget(nota)
        self.tabla = _tabla_simple(["Codigo", "Nombre", "Unidad", "Tipo", "Obligatorio",
                                    "Rango / valores", "En uso"])
        self.tabla.doubleClicked.connect(self._editar)
        capa.addWidget(self.tabla, 1)
        fila = QHBoxLayout()
        for texto, accion, estilo in (("Nuevo parametro", self._nuevo, ""),
                                      ("Editar", self._editar, "secundario"),
                                      ("Eliminar", self._eliminar, "peligro")):
            boton = QPushButton(texto)
            if estilo:
                boton.setObjectName(estilo)
            boton.clicked.connect(accion)
            fila.addWidget(boton)
        fila.addStretch()
        cerrar = QPushButton("Cerrar")
        cerrar.setObjectName("secundario")
        cerrar.clicked.connect(self.accept)
        fila.addWidget(cerrar)
        capa.addLayout(fila)
        self.parametros = []
        self._cargar()

    @staticmethod
    def _detalle(p) -> str:
        if p["tipo_dato"] == "lista":
            return ", ".join(v["valor"] for v in p.get("valores", []) if v.get("activo", True))
        if p["tipo_dato"] == "numerico":
            minimo, maximo = p.get("valor_minimo"), p.get("valor_maximo")
            if minimo is None and maximo is None:
                return "sin limites"
            numero = lambda v: f"{float(v):g}"   # noqa: E731
            return f"{numero(minimo) if minimo is not None else '…'} a " \
                   f"{numero(maximo) if maximo is not None else '…'}"
        return "texto libre"

    def _cargar(self):
        try:
            self.parametros = self.cliente.parametros_tecnicos()
        except ErrorAPI as error:
            QMessageBox.warning(self, "Parametros tecnicos", error.mensaje)
            return
        tipos = dict(TIPOS)
        _celdas(self.tabla, [[p["codigo"], p["nombre"], p.get("unidad", ""),
                              tipos.get(p["tipo_dato"], p["tipo_dato"]),
                              "Si" if p["obligatorio"] else "No", self._detalle(p),
                              "Si" if p.get("en_uso") else "No"] for p in self.parametros])

    def _actual(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.parametros):
            QMessageBox.information(self, "Parametros tecnicos", "Seleccione un parametro.")
            return None
        return self.parametros[fila]

    def _nuevo(self):
        DialogoParametro(self.cliente, None, self).exec()
        self._cargar()

    def _editar(self, *_):
        parametro = self._actual()
        if parametro:
            DialogoParametro(self.cliente, parametro, self).exec()
            self._cargar()

    def _eliminar(self):
        parametro = self._actual()
        if not parametro:
            return
        if QMessageBox.question(self, "Eliminar parametro",
                                f"¿Eliminar el parametro «{parametro['nombre']}»?"
                                ) != QMessageBox.Yes:
            return
        try:
            self.cliente.eliminar_parametro_tecnico(parametro["id_parametro"])
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo eliminar", error.mensaje)
        self._cargar()
