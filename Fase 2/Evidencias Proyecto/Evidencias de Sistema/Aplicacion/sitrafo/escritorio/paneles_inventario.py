"""
Paneles del inventario (HU-10), del Encargado de bodega.

- PanelInventario: stock por material con alerta bajo el minimo, recepcion
  de compras, ajuste por conteo fisico, kardex y alta de materiales.
- PanelProveedores: registro de proveedores.

El stock nunca se escribe directamente: cada operacion es un movimiento que
queda en el kardex (RN-09). Administracion y produccion ven en lectura.
"""
from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import _decimal, fecha, uf
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

UNIDADES = [("un", "Unidad"), ("kg", "Kilogramo"), ("m", "Metro"),
            ("m2", "Metro cuadrado"), ("l", "Litro")]
ALERTA = QColor("#fdecea")


def _num(valor) -> str:
    texto = f"{_decimal(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto[:-3] if texto.endswith(",00") else texto


def _botones(dialogo, aceptar: str):
    botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    botones.button(QDialogButtonBox.Ok).setText(aceptar)
    botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
    botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
    botones.rejected.connect(dialogo.reject)
    return botones


class _DialogoMovimiento(QDialog):
    """Base de recepcion y ajuste: material, bodega y saldo actual."""

    def __init__(self, cliente: ClienteAPI, material: dict, titulo: str, parent=None):
        super().__init__(parent)
        self.cliente, self.material = cliente, material
        self.setWindowTitle(f"{titulo} — {material['nombre']}")
        self.setMinimumWidth(480)
        self.formulario = QFormLayout(self)
        self.bodega = QComboBox()
        for b in cliente.bodegas():
            self.bodega.addItem(b["nombre"], b["id_bodega"])
        self.saldo = QLabel("")
        self.saldo.setObjectName("nota")
        self.bodega.currentIndexChanged.connect(self._saldo)
        self.formulario.addRow("Bodega:", self.bodega)
        self.formulario.addRow("", self.saldo)
        self._saldo()

    def stock_en_bodega(self) -> str:
        return self.material["stock_por_bodega"].get(str(self.bodega.currentData()), "0")

    def _saldo(self):
        self.saldo.setText(f"Stock actual en la bodega: {_num(self.stock_en_bodega())} "
                           f"{self.material['unidad_medida']}")

    def ejecutar(self, operacion, datos):
        try:
            operacion(self.material["id_material"], datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo registrar", error.mensaje)
            return
        self.accept()


class DialogoRecepcion(_DialogoMovimiento):
    """Entrada de material comprado (CU-INV-03)."""

    def __init__(self, cliente, material, parent=None):
        super().__init__(cliente, material, "Recepcion de compra", parent)
        self.cantidad = QDoubleSpinBox()
        self.cantidad.setRange(0.01, 1_000_000)
        self.cantidad.setDecimals(2)
        self.cantidad.setSuffix(f" {material['unidad_medida']}")
        self.proveedor = QComboBox()
        self.proveedor.addItem("Sin indicar", None)
        for p in cliente.proveedores():
            if p["activo"]:
                self.proveedor.addItem(p["razon_social"], p["id_proveedor"])
        self.documento = QLineEdit()
        self.documento.setPlaceholderText("Ej.: Factura 12345 / Guia 678")
        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 100_000)
        self.costo.setDecimals(4)
        self.costo.setSuffix(" UF")
        self.costo.setValue(float(_decimal(material.get("costo_vigente_uf") or 0)))
        self.actualizar = QCheckBox("Usar este costo como nuevo precio vigente")
        self.formulario.addRow("Cantidad recibida:", self.cantidad)
        self.formulario.addRow("Proveedor:", self.proveedor)
        self.formulario.addRow("Documento:", self.documento)
        self.formulario.addRow("Costo unitario:", self.costo)
        self.formulario.addRow("", self.actualizar)
        botones = _botones(self, "Registrar recepcion")
        botones.accepted.connect(self._aceptar)
        self.formulario.addRow(botones)

    def _aceptar(self):
        self.ejecutar(self.cliente.recepcionar, {
            "bodega": self.bodega.currentData(), "cantidad": f"{self.cantidad.value():.4f}",
            "proveedor": self.proveedor.currentData(), "documento": self.documento.text(),
            "costo_unitario_uf": f"{self.costo.value():.4f}",
            "actualizar_precio": self.actualizar.isChecked(),
        })


class DialogoAjuste(_DialogoMovimiento):
    """Ajuste por conteo fisico (CU-INV-04)."""

    def __init__(self, cliente, material, parent=None):
        super().__init__(cliente, material, "Ajuste por conteo fisico", parent)
        self.conteo = QDoubleSpinBox()
        self.conteo.setRange(0, 1_000_000)
        self.conteo.setDecimals(2)
        self.conteo.setSuffix(f" {material['unidad_medida']}")
        self.conteo.setValue(float(_decimal(self.stock_en_bodega())))
        self.bodega.currentIndexChanged.connect(
            lambda: self.conteo.setValue(float(_decimal(self.stock_en_bodega()))))
        self.diferencia = QLabel("")
        self.conteo.valueChanged.connect(self._diferencia)
        self.motivo = QLineEdit()
        self.motivo.setPlaceholderText("Ej.: merma, rotura, error de registro, inventario ciclico")
        self.formulario.addRow("Cantidad contada:", self.conteo)
        self.formulario.addRow("Diferencia:", self.diferencia)
        self.formulario.addRow("Motivo:", self.motivo)
        botones = _botones(self, "Registrar ajuste")
        botones.accepted.connect(self._aceptar)
        self.formulario.addRow(botones)
        self._diferencia()

    def _diferencia(self):
        diferencia = _decimal(self.conteo.value()) - _decimal(self.stock_en_bodega())
        self.diferencia.setText(f"{'+' if diferencia > 0 else ''}{_num(diferencia)} "
                                f"{self.material['unidad_medida']}")

    def _aceptar(self):
        self.ejecutar(self.cliente.ajustar_stock, {
            "bodega": self.bodega.currentData(), "conteo_fisico": f"{self.conteo.value():.4f}",
            "motivo": self.motivo.text(),
        })


class DialogoKardex(QDialog):
    """Movimientos del material con saldo acumulado (CU-INV-05)."""

    COLUMNAS = ["Fecha", "Tipo", "Bodega", "Entrada", "Salida", "Saldo", "Referencia",
                "Usuario"]

    def __init__(self, cliente: ClienteAPI, material: dict, parent=None):
        super().__init__(parent)
        datos = cliente.kardex(material["id_material"])
        self.setWindowTitle(f"Kardex — {material['codigo']} {material['nombre']}")
        self.resize(980, 520)
        capa = QVBoxLayout(self)
        capa.addWidget(QLabel(f"Saldo actual: <b>{_num(datos['saldo'])} {datos['unidad']}</b>"
                              f" · minimo {_num(material['stock_minimo'])}"))
        tabla = QTableWidget(len(datos["movimientos"]), len(self.COLUMNAS))
        tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        cabecera = tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(6, QHeaderView.Stretch)
        for i, m in enumerate(reversed(datos["movimientos"])):   # el mas reciente arriba
            valores = [fecha(m["fecha_hora"]) + " " + m["fecha_hora"][11:16], m["tipo_nombre"],
                       m["bodega"], _num(m["entrada"]) if m["entrada"] else "",
                       _num(m["salida"]) if m["salida"] else "", _num(m["saldo"]),
                       m["referencia"], m["usuario"]]
            for j, valor in enumerate(valores):
                tabla.setItem(i, j, QTableWidgetItem(valor))
        capa.addWidget(tabla, 1)
        cerrar = QPushButton("Cerrar")
        cerrar.setObjectName("secundario")
        cerrar.clicked.connect(self.accept)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(cerrar)
        capa.addLayout(fila)


class DialogoMaterial(QDialog):
    """Alta y edicion de un material (CU-INV-01)."""

    def __init__(self, cliente: ClienteAPI, material: dict | None = None, parent=None):
        super().__init__(parent)
        self.cliente, self.material, self.resultado = cliente, material, None
        self.setWindowTitle("Editar material" if material else "Nuevo material")
        self.setMinimumWidth(460)
        formulario = QFormLayout(self)

        fila = QHBoxLayout()
        self.categoria = QComboBox()
        self._categorias()
        nueva = QPushButton("Nueva")
        nueva.setObjectName("secundario")
        nueva.clicked.connect(self._nueva_categoria)
        fila.addWidget(self.categoria, 1)
        fila.addWidget(nueva)
        self.codigo = QLineEdit()
        self.nombre = QLineEdit()
        self.unidad = QComboBox()
        for codigo, nombre in UNIDADES:
            self.unidad.addItem(nombre, codigo)
        self.minimo = QDoubleSpinBox()
        self.minimo.setRange(0, 1_000_000)
        self.minimo.setDecimals(2)
        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 100_000)
        self.costo.setDecimals(4)
        self.costo.setSuffix(" UF")
        formulario.addRow("Categoria:", fila)
        formulario.addRow("Codigo:", self.codigo)
        formulario.addRow("Nombre:", self.nombre)
        formulario.addRow("Unidad:", self.unidad)
        formulario.addRow("Stock minimo:", self.minimo)
        formulario.addRow("Costo de compra:", self.costo)
        nota = QLabel("El stock no se ingresa aqui: se carga con una recepcion.")
        nota.setObjectName("nota")
        formulario.addRow("", nota)
        botones = _botones(self, "Guardar")
        botones.accepted.connect(self._guardar)
        formulario.addRow(botones)

        if material:
            self.categoria.setCurrentIndex(self.categoria.findData(material["categoria"]))
            self.codigo.setText(material["codigo"])
            self.codigo.setEnabled(False)
            self.nombre.setText(material["nombre"])
            self.unidad.setCurrentIndex(max(0, self.unidad.findData(material["unidad_medida"])))
            self.minimo.setValue(float(_decimal(material["stock_minimo"])))
            self.costo.setValue(float(_decimal(material.get("costo_vigente_uf") or 0)))

    def _categorias(self, seleccionar=None):
        self.categoria.clear()
        for c in self.cliente.categorias_material():
            self.categoria.addItem(c["nombre"], c["id_categoria"])
        if seleccionar:
            self.categoria.setCurrentIndex(self.categoria.findData(seleccionar))

    def _nueva_categoria(self):
        nombre, ok = QInputDialog.getText(self, "Nueva categoria", "Nombre:")
        if ok and nombre.strip():
            try:
                categoria = self.cliente.crear_categoria_material(nombre.strip())
            except ErrorAPI as error:
                QMessageBox.warning(self, "No se pudo crear", error.mensaje)
                return
            self._categorias(categoria["id_categoria"])

    def _guardar(self):
        datos = {"categoria": self.categoria.currentData(), "codigo": self.codigo.text().strip(),
                 "nombre": self.nombre.text().strip(), "unidad_medida": self.unidad.currentData(),
                 "stock_minimo": f"{self.minimo.value():.4f}"}
        if self.costo.value() > 0:
            datos["costo_uf"] = f"{self.costo.value():.4f}"
        try:
            if self.material:
                self.resultado = self.cliente.actualizar_material(self.material["id_material"],
                                                                  datos)
            else:
                self.resultado = self.cliente.crear_material(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class PanelInventario(PanelBase):
    titulo = "Inventario"
    subtitulo = ("Stock por material, calculado desde sus movimientos. Las filas en rojo "
                 "estan bajo su stock minimo y requieren reposicion.")
    columnas = ["Codigo", "Material", "Categoria", "Stock", "Minimo", "Costo UF", "Estado"]

    def construir(self):
        barra = QHBoxLayout()
        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar por codigo o nombre")
        self.buscar.textChanged.connect(self._filtrar)
        barra.addWidget(self.buscar, 1)
        self.solo_alertas = QCheckBox("Solo bajo el minimo")
        self.solo_alertas.toggled.connect(self._filtrar)
        barra.addWidget(self.solo_alertas)
        self.contenedor.addLayout(barra)

        self.resumen = QLabel("")
        self.contenedor.addWidget(self.resumen)
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        self.contenedor.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        self.b_recepcion = QPushButton("Recepcion de compra")
        self.b_recepcion.setObjectName("exito")
        self.b_recepcion.clicked.connect(lambda: self._dialogo(DialogoRecepcion))
        self.b_ajuste = QPushButton("Ajuste por conteo")
        self.b_ajuste.clicked.connect(lambda: self._dialogo(DialogoAjuste))
        self.b_kardex = QPushButton("Ver kardex")
        self.b_kardex.setObjectName("secundario")
        self.b_kardex.clicked.connect(self._kardex)
        self.b_nuevo = QPushButton("Nuevo material")
        self.b_nuevo.setObjectName("secundario")
        self.b_nuevo.clicked.connect(lambda: self._material(None))
        self.b_editar = QPushButton("Editar")
        self.b_editar.setObjectName("secundario")
        self.b_editar.clicked.connect(lambda: self._material(self._actual()))
        for boton in (self.b_recepcion, self.b_ajuste, self.b_kardex, self.b_nuevo,
                      self.b_editar):
            acciones.addWidget(boton)
        acciones.addStretch()
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        self.contenedor.addLayout(acciones)

        puede = self.cliente.puede
        self.b_recepcion.setVisible(puede("bodega.crear"))
        self.b_ajuste.setVisible(puede("bodega.actualizar"))
        self.b_kardex.setVisible(puede("kardex.leer") or puede("bodega.leer"))
        self.b_nuevo.setVisible(puede("material.crear"))
        self.b_editar.setVisible(puede("material.actualizar"))
        self.todos, self.datos = [], []
        self._seleccion()

    def refrescar(self):
        try:
            self.todos = self.cliente.materiales()
        except ErrorAPI as error:
            return self.manejar_error(error)
        alertas = sum(1 for m in self.todos if m["bajo_minimo"])
        self.resumen.setText(
            f"<span style='color:#b42318'><b>{alertas} material(es) bajo el stock minimo."
            "</b></span>" if alertas else "Todos los materiales sobre su stock minimo.")
        self._filtrar()

    def _filtrar(self):
        texto = self.buscar.text().strip().lower()
        self.datos = [m for m in self.todos
                      if (not texto or texto in m["codigo"].lower() or texto in m["nombre"].lower())
                      and (not self.solo_alertas.isChecked() or m["bajo_minimo"])]
        self.llenar(self.tabla, [
            [m["codigo"], m["nombre"], m["categoria_nombre"],
             f"{_num(m['stock_total'])} {m['unidad_medida']}", _num(m["stock_minimo"]),
             uf(m["costo_vigente_uf"], 4) if m["costo_vigente_uf"] else "sin precio",
             "REPONER" if m["bajo_minimo"] else "OK"]
            for m in self.datos
        ])
        for fila, m in enumerate(self.datos):
            if m["bajo_minimo"]:
                for columna in range(self.tabla.columnCount()):
                    self.tabla.item(fila, columna).setBackground(ALERTA)
        self._seleccion()

    def _actual(self):
        fila = self.tabla.currentRow()
        return self.datos[fila] if 0 <= fila < len(getattr(self, "datos", [])) else None

    def _seleccion(self):
        hay = self._actual() is not None
        for boton in (self.b_recepcion, self.b_ajuste, self.b_kardex, self.b_editar):
            boton.setEnabled(hay)

    def _dialogo(self, clase):
        material = self._actual()
        try:
            dialogo = clase(self.cliente, material, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec():
            self.refrescar()

    def _kardex(self):
        try:
            DialogoKardex(self.cliente, self._actual(), self).exec()
        except ErrorAPI as error:
            self.manejar_error(error)

    def _material(self, material):
        try:
            dialogo = DialogoMaterial(self.cliente, material, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec():
            self.refrescar()


class DialogoProveedor(QDialog):
    def __init__(self, cliente: ClienteAPI, proveedor: dict | None = None, parent=None):
        super().__init__(parent)
        self.cliente, self.proveedor = cliente, proveedor
        self.setWindowTitle("Editar proveedor" if proveedor else "Nuevo proveedor")
        self.setMinimumWidth(420)
        formulario = QFormLayout(self)
        self.rut = QLineEdit()
        self.rut.setPlaceholderText("76.123.456-7")
        self.razon = QLineEdit()
        self.email = QLineEdit()
        self.telefono = QLineEdit()
        self.activo = QCheckBox("Activo")
        self.activo.setChecked(True)
        formulario.addRow("RUT:", self.rut)
        formulario.addRow("Razon social:", self.razon)
        formulario.addRow("Correo:", self.email)
        formulario.addRow("Telefono:", self.telefono)
        formulario.addRow("", self.activo)
        botones = _botones(self, "Guardar")
        botones.accepted.connect(self._guardar)
        formulario.addRow(botones)
        if proveedor:
            self.rut.setText(proveedor["rut"])
            self.rut.setEnabled(False)
            self.razon.setText(proveedor["razon_social"])
            self.email.setText(proveedor["email"])
            self.telefono.setText(proveedor["telefono"])
            self.activo.setChecked(proveedor["activo"])

    def _guardar(self):
        datos = {"razon_social": self.razon.text().strip(), "email": self.email.text().strip(),
                 "telefono": self.telefono.text().strip(), "activo": self.activo.isChecked()}
        try:
            if self.proveedor:
                self.cliente.actualizar_proveedor(self.proveedor["id_proveedor"], datos)
            else:
                self.cliente.crear_proveedor({**datos, "rut": self.rut.text().strip()})
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class PanelProveedores(PanelBase):
    titulo = "Proveedores"
    subtitulo = "Empresas que abastecen materiales. Se indican al registrar una recepcion."
    columnas = ["RUT", "Razon social", "Correo", "Telefono", "Estado"]

    def construir(self):
        self.tabla = self.crear_tabla()
        self.tabla.doubleClicked.connect(self._editar)
        self.contenedor.addWidget(self.tabla, 1)
        acciones = QHBoxLayout()
        nuevo = QPushButton("Nuevo proveedor")
        nuevo.setObjectName("exito")
        nuevo.clicked.connect(lambda: self._abrir(None))
        editar = QPushButton("Editar")
        editar.setObjectName("secundario")
        editar.clicked.connect(self._editar)
        acciones.addWidget(nuevo)
        acciones.addWidget(editar)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)
        nuevo.setVisible(self.cliente.puede("material.crear"))
        editar.setVisible(self.cliente.puede("material.actualizar"))
        self.datos = []

    def refrescar(self):
        try:
            self.datos = self.cliente.proveedores()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.llenar(self.tabla, [
            [p["rut"], p["razon_social"], p["email"] or "—", p["telefono"] or "—",
             "Activo" if p["activo"] else "Inactivo"] for p in self.datos
        ])

    def _editar(self, *_):
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self.datos) and self.cliente.puede("material.actualizar"):
            self._abrir(self.datos[fila])

    def _abrir(self, proveedor):
        if DialogoProveedor(self.cliente, proveedor, self).exec():
            self.refrescar()
