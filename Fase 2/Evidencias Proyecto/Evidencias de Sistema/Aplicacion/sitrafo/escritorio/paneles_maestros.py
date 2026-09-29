"""
Datos maestros de produccion desde el escritorio.

- DialogoReceta: lista de materiales y tareas estandar de un modelo
  (RF-CAT-04, 05). Es la base del costeo y de las ordenes de trabajo.
- DialogoLineas: lineas de una cotizacion en borrador (RF-COM-03).
- PanelEmpleados: empleados, cargos y tarifas versionadas (RF-OT-11).
"""
from decimal import Decimal, InvalidOperation

from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import fecha, uf
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


def _dec(valor) -> Decimal:
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _tabla(columnas, estirar=0) -> QTableWidget:
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    cabecera = tabla.horizontalHeader()
    cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
    cabecera.setSectionResizeMode(estirar, QHeaderView.Stretch)
    return tabla


def _botones(dialogo, aceptar, editable=True):
    botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    botones.button(QDialogButtonBox.Ok).setText(aceptar)
    botones.button(QDialogButtonBox.Ok).setVisible(editable)
    botones.button(QDialogButtonBox.Cancel).setText("Cancelar" if editable else "Cerrar")
    botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
    botones.rejected.connect(dialogo.reject)
    return botones


# ---------------------------------------------------------------------------
# Receta del modelo (RF-CAT-04, 05)
# ---------------------------------------------------------------------------
class DialogoReceta(QDialog):
    def __init__(self, api: ClienteAPI, modelo: dict, parent=None):
        super().__init__(parent)
        self.api, self.modelo = api, modelo
        self.editable = api.puede("bom.actualizar")
        self.materiales = [m for m in api.materiales() if m["activo"]]
        receta = api.receta(modelo["id_modelo"])
        self.setWindowTitle(f"Materiales y tareas — {modelo['codigo']} {modelo['nombre']}")
        self.resize(820, 600)
        capa = QVBoxLayout(self)

        grupo_m = QGroupBox("Lista de materiales (por unidad fabricada)")
        gm = QVBoxLayout(grupo_m)
        self.t_materiales = _tabla(["Material", "Cantidad", "Unidad", "Costo unitario"], 0)
        gm.addWidget(self.t_materiales)
        fila = QHBoxLayout()
        for texto, funcion in (("Agregar material", self._agregar_material),
                               ("Quitar", lambda: self._quitar(self.t_materiales))):
            boton = QPushButton(texto)
            boton.setObjectName("secundario")
            boton.clicked.connect(funcion)
            boton.setVisible(self.editable)
            fila.addWidget(boton)
        fila.addStretch()
        gm.addLayout(fila)
        capa.addWidget(grupo_m, 3)

        grupo_t = QGroupBox("Tareas estandar (en orden de ejecucion)")
        gt = QVBoxLayout(grupo_t)
        self.t_tareas = _tabla(["Tarea", "Horas estimadas"], 0)
        gt.addWidget(self.t_tareas)
        fila = QHBoxLayout()
        for texto, funcion in (("Agregar tarea", self._agregar_tarea),
                               ("Quitar", lambda: self._quitar(self.t_tareas))):
            boton = QPushButton(texto)
            boton.setObjectName("secundario")
            boton.clicked.connect(funcion)
            boton.setVisible(self.editable)
            fila.addWidget(boton)
        fila.addStretch()
        gt.addLayout(fila)
        capa.addWidget(grupo_t, 2)

        self.resumen = QLabel("")
        capa.addWidget(self.resumen)
        nota = QLabel("Los cambios aplican a las cotizaciones y ordenes de trabajo nuevas; "
                      "las ya generadas conservan su copia.")
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        capa.addWidget(nota)
        botones = _botones(self, "Guardar", self.editable)
        botones.accepted.connect(self._guardar)
        capa.addWidget(botones)

        for m in receta["materiales"]:
            self._agregar_material(m)
        for t in receta["tareas"]:
            self._agregar_tarea(t)
        self._mostrar_resumen(receta)

    def _mostrar_resumen(self, receta):
        tarifa = receta.get("tarifa_referencia_uf")
        self.resumen.setText(
            f"Costo unitario estimado: materiales <b>{uf(receta['costo_material_uf'], 4)}</b> · "
            f"horas hombre <b>{uf(receta['costo_hh_uf'], 4)}</b> "
            f"({receta['horas_estandar']} h"
            + (f" x {uf(tarifa, 4)}" if tarifa else ", sin tarifa de referencia") + ")")

    def _agregar_material(self, dato=None):
        fila = self.t_materiales.rowCount()
        self.t_materiales.insertRow(fila)
        combo = QComboBox()
        for m in self.materiales:
            combo.addItem(f"{m['codigo']} — {m['nombre']}", m["id_material"])
        cantidad = QDoubleSpinBox()
        cantidad.setRange(0.0001, 100000)
        cantidad.setDecimals(4)
        cantidad.setValue(float(_dec((dato or {}).get("cantidad", 1))))
        if dato:
            combo.setCurrentIndex(max(0, combo.findData(dato["material"])))
        combo.currentIndexChanged.connect(lambda _=0, f=fila: self._datos_material(f))
        combo.setEnabled(self.editable)
        cantidad.setEnabled(self.editable)
        self.t_materiales.setCellWidget(fila, 0, combo)
        self.t_materiales.setCellWidget(fila, 1, cantidad)
        self._datos_material(fila)

    def _datos_material(self, fila):
        combo = self.t_materiales.cellWidget(fila, 0)
        if combo is None:
            return
        m = next((x for x in self.materiales if x["id_material"] == combo.currentData()), None)
        if m:
            self.t_materiales.setItem(fila, 2, QTableWidgetItem(m["unidad_medida"]))
            self.t_materiales.setItem(fila, 3, QTableWidgetItem(
                uf(m["costo_vigente_uf"], 4) if m["costo_vigente_uf"] else "sin precio"))

    def _agregar_tarea(self, dato=None):
        fila = self.t_tareas.rowCount()
        self.t_tareas.insertRow(fila)
        nombre = QLineEdit((dato or {}).get("nombre", ""))
        nombre.setPlaceholderText("Ej.: Bobinado de alta tension")
        horas = QDoubleSpinBox()
        horas.setRange(0.25, 200)
        horas.setDecimals(2)
        horas.setSuffix(" h")
        horas.setValue(float(_dec((dato or {}).get("horas_estimadas", 2))))
        nombre.setEnabled(self.editable)
        horas.setEnabled(self.editable)
        self.t_tareas.setCellWidget(fila, 0, nombre)
        self.t_tareas.setCellWidget(fila, 1, horas)

    @staticmethod
    def _quitar(tabla):
        if tabla.currentRow() >= 0:
            tabla.removeRow(tabla.currentRow())

    def _guardar(self):
        materiales = [{"material": self.t_materiales.cellWidget(i, 0).currentData(),
                       "cantidad": f"{self.t_materiales.cellWidget(i, 1).value():.4f}"}
                      for i in range(self.t_materiales.rowCount())]
        tareas = [{"nombre": self.t_tareas.cellWidget(i, 0).text().strip(),
                   "horas_estimadas": f"{self.t_tareas.cellWidget(i, 1).value():.2f}"}
                  for i in range(self.t_tareas.rowCount())]
        try:
            receta = self.api.guardar_receta(self.modelo["id_modelo"], materiales, tareas)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self._mostrar_resumen(receta)
        QMessageBox.information(self, "Receta guardada",
                                f"{len(materiales)} material(es) y {len(tareas)} tarea(s).")
        self.accept()


# ---------------------------------------------------------------------------
# Lineas de una cotizacion en borrador (RF-COM-03)
# ---------------------------------------------------------------------------
class DialogoLineas(QDialog):
    def __init__(self, api: ClienteAPI, cotizacion: dict, parent=None):
        super().__init__(parent)
        self.api, self.cotizacion = api, cotizacion
        self.resultado = None
        respuesta = api.modelos({"page_size": 500})
        self.modelos = respuesta.get("results", respuesta)
        self.setWindowTitle(f"Lineas de {cotizacion['numero']} v{cotizacion['version']}")
        self.resize(780, 420)
        capa = QVBoxLayout(self)
        self.tabla = _tabla(["Modelo", "Unidades", "Precio unitario UF", "Subtotal"], 0)
        capa.addWidget(self.tabla, 1)
        fila = QHBoxLayout()
        agregar = QPushButton("Agregar linea")
        agregar.setObjectName("secundario")
        agregar.clicked.connect(lambda: self._agregar())
        quitar = QPushButton("Quitar linea")
        quitar.setObjectName("secundario")
        quitar.clicked.connect(lambda: self.tabla.removeRow(self.tabla.currentRow())
                               if self.tabla.currentRow() >= 0 else None)
        fila.addWidget(agregar)
        fila.addWidget(quitar)
        fila.addStretch()
        self.total = QLabel("")
        fila.addWidget(self.total)
        capa.addLayout(fila)
        nota = QLabel("Al elegir un modelo se propone su precio sugerido (costo mas margen, o "
                      "precio base). Puede ajustarlo antes de guardar.")
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        capa.addWidget(nota)
        botones = _botones(self, "Guardar lineas")
        botones.accepted.connect(self._guardar)
        capa.addWidget(botones)
        for linea in cotizacion["lineas"]:
            self._agregar(linea)
        self._recalcular()

    def _agregar(self, linea=None):
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        modelo = QComboBox()
        for m in self.modelos:
            modelo.addItem(f"{m['codigo']} — {m['nombre']}", m["id_modelo"])
        cantidad = QSpinBox()
        cantidad.setRange(1, 1000)
        precio = QDoubleSpinBox()
        precio.setRange(0, 1_000_000)
        precio.setDecimals(4)
        if linea:
            modelo.setCurrentIndex(max(0, modelo.findData(linea["modelo"])))
            cantidad.setValue(int(linea["cantidad"]))
            precio.setValue(float(_dec(linea["precio_uf"])))
        self.tabla.setCellWidget(fila, 0, modelo)
        self.tabla.setCellWidget(fila, 1, cantidad)
        self.tabla.setCellWidget(fila, 2, precio)
        modelo.currentIndexChanged.connect(lambda _=0, p=precio, m=modelo: self._sugerir(m, p))
        cantidad.valueChanged.connect(self._recalcular)
        precio.valueChanged.connect(self._recalcular)
        if linea is None:
            self._sugerir(modelo, precio)
        self._recalcular()

    def _sugerir(self, combo, precio):
        try:
            costeo = self.api.costeo_modelo(combo.currentData())
        except ErrorAPI:
            return
        precio.setValue(float(_dec(costeo.get("precio_sugerido_uf") or 0)))

    def _recalcular(self):
        total = Decimal("0")
        for i in range(self.tabla.rowCount()):
            subtotal = (_dec(self.tabla.cellWidget(i, 2).value())
                        * self.tabla.cellWidget(i, 1).value())
            self.tabla.setItem(i, 3, QTableWidgetItem(uf(subtotal, 4)))
            total += subtotal
        self.total.setText(f"Total antes de descuento: <b>{uf(total, 4)}</b>")

    def _guardar(self):
        lineas = [{"modelo": self.tabla.cellWidget(i, 0).currentData(),
                   "cantidad": self.tabla.cellWidget(i, 1).value(),
                   "precio_uf": f"{self.tabla.cellWidget(i, 2).value():.4f}"}
                  for i in range(self.tabla.rowCount())]
        try:
            self.resultado = self.api.guardar_lineas(self.cotizacion["id_cotizacion"], lineas)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


# ---------------------------------------------------------------------------
# Empleados y tarifas (RF-OT-11)
# ---------------------------------------------------------------------------
class DialogoEmpleado(QDialog):
    def __init__(self, api: ClienteAPI, empleado: dict | None = None, parent=None):
        super().__init__(parent)
        self.api, self.empleado = api, empleado
        self.setWindowTitle("Editar empleado" if empleado else "Nuevo empleado")
        self.setMinimumWidth(420)
        formulario = QFormLayout(self)
        self.rut, self.nombre, self.cargo = QLineEdit(), QLineEdit(), QLineEdit()
        self.rut.setPlaceholderText("16.789.234-5")
        self.cargo.setPlaceholderText("Ej.: Bobinador, Armador, Tecnico de ensayos")
        self.activo = QCheckBox("Activo")
        self.activo.setChecked(True)
        self.tarifa = QDoubleSpinBox()
        self.tarifa.setRange(0, 10)
        self.tarifa.setDecimals(4)
        self.tarifa.setSuffix(" UF/h")
        formulario.addRow("RUT:", self.rut)
        formulario.addRow("Nombre completo:", self.nombre)
        formulario.addRow("Cargo:", self.cargo)
        formulario.addRow("", self.activo)
        if empleado is None:
            formulario.addRow("Tarifa inicial:", self.tarifa)
        botones = _botones(self, "Guardar")
        botones.accepted.connect(self._guardar)
        formulario.addRow(botones)
        if empleado:
            self.rut.setText(empleado["rut"])
            self.rut.setEnabled(False)
            self.nombre.setText(empleado["nombre"])
            self.cargo.setText(empleado["cargo"])
            self.activo.setChecked(empleado["activo"])

    def _guardar(self):
        datos = {"nombre": self.nombre.text().strip(), "cargo": self.cargo.text().strip(),
                 "activo": self.activo.isChecked()}
        try:
            if self.empleado:
                self.api.actualizar_empleado(self.empleado["id_empleado"], datos)
            else:
                nuevo = self.api.crear_empleado({**datos, "rut": self.rut.text().strip()})
                if self.tarifa.value() > 0:
                    self.api.fijar_tarifa(nuevo["id_empleado"], f"{self.tarifa.value():.4f}")
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class DialogoTarifa(QDialog):
    def __init__(self, api: ClienteAPI, empleado: dict, parent=None):
        super().__init__(parent)
        self.api, self.empleado = api, empleado
        self.setWindowTitle(f"Tarifa de {empleado['nombre']}")
        self.setMinimumWidth(460)
        capa = QVBoxLayout(self)
        historial = _tabla(["Valor UF/h", "Desde", "Hasta"], 0)
        historial.setEditTriggers(QTableWidget.NoEditTriggers)
        historial.setRowCount(len(empleado["tarifas"]))
        for i, t in enumerate(empleado["tarifas"]):
            for j, v in enumerate([uf(t["valor_hora_uf"], 4), fecha(t["vigente_desde"]),
                                   fecha(t["vigente_hasta"]) if t["vigente_hasta"]
                                   else "vigente"]):
                historial.setItem(i, j, QTableWidgetItem(v))
        capa.addWidget(QLabel("Historial de tarifas"))
        capa.addWidget(historial)
        formulario = QFormLayout()
        self.valor = QDoubleSpinBox()
        self.valor.setRange(0.0001, 10)
        self.valor.setDecimals(4)
        self.valor.setSuffix(" UF/h")
        self.valor.setValue(float(_dec(empleado.get("tarifa_vigente_uf") or 0.4)))
        self.desde = QDateEdit(QDate.currentDate())
        self.desde.setCalendarPopup(True)
        self.desde.setDisplayFormat("dd-MM-yyyy")
        formulario.addRow("Nueva tarifa:", self.valor)
        formulario.addRow("Vigente desde:", self.desde)
        capa.addLayout(formulario)
        nota = QLabel("Las horas ya registradas conservan la tarifa con que se registraron.")
        nota.setObjectName("nota")
        capa.addWidget(nota)
        botones = _botones(self, "Guardar tarifa")
        botones.accepted.connect(self._guardar)
        capa.addWidget(botones)

    def _guardar(self):
        try:
            self.api.fijar_tarifa(self.empleado["id_empleado"], f"{self.valor.value():.4f}",
                                  self.desde.date().toString("yyyy-MM-dd"))
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class PanelEmpleados(PanelBase):
    titulo = "Empleados y tarifas"
    subtitulo = ("Personal del taller con su tarifa de hora hombre vigente. Las tarifas "
                 "se versionan: un cambio no altera las horas ya valorizadas.")
    columnas = ["RUT", "Nombre", "Cargo", "Tarifa vigente", "Usuario", "Estado"]

    def construir(self):
        self.tabla = self.crear_tabla()
        self.contenedor.addWidget(self.tabla, 1)
        acciones = QHBoxLayout()
        nuevo = QPushButton("Nuevo empleado")
        nuevo.setObjectName("exito")
        nuevo.clicked.connect(self._nuevo)
        editar = QPushButton("Editar")
        editar.setObjectName("secundario")
        editar.clicked.connect(self._editar)
        tarifa = QPushButton("Tarifa")
        tarifa.clicked.connect(self._tarifa)
        for boton in (nuevo, editar, tarifa):
            acciones.addWidget(boton)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)
        nuevo.setVisible(self.cliente.puede("empleado.crear"))
        editar.setVisible(self.cliente.puede("empleado.actualizar"))
        tarifa.setVisible(self.cliente.puede("empleado.actualizar"))
        self.datos = []

    def refrescar(self):
        try:
            self.datos = self.cliente.empleados_todos()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.llenar(self.tabla, [
            [e["rut"], e["nombre"], e["cargo"],
             uf(e["tarifa_vigente_uf"], 4) + "/h" if e["tarifa_vigente_uf"] else "sin tarifa",
             e["username"] or "—", "Activo" if e["activo"] else "Inactivo"]
            for e in self.datos])

    def _actual(self):
        fila = self.tabla.currentRow()
        return self.datos[fila] if 0 <= fila < len(self.datos) else None

    # Cada boton tiene su propio metodo: con conexiones lambda, sender() puede
    # devolver None y el clic fallaba sin aviso
    def _nuevo(self):
        self._abrir(DialogoEmpleado, None)

    def _editar(self):
        if self._actual() is None:
            QMessageBox.information(self, "Empleados", "Seleccione un empleado.")
            return
        self._abrir(DialogoEmpleado, self._actual())

    def _tarifa(self):
        if self._actual() is None:
            QMessageBox.information(self, "Empleados", "Seleccione un empleado.")
            return
        self._abrir(DialogoTarifa, self._actual())

    def _abrir(self, clase, empleado):
        try:
            dialogo = clase(self.cliente, empleado, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec():
            self.refrescar()
