"""
Paneles del area productiva.

- PanelOrdenesTrabajo: el jefe de produccion planifica (asigna tareas),
  inicia, registra por un ausente, envia a calidad y cierra. Los demas roles
  con lectura ven el avance y el costo real contra el estimado.
- VistaTaller: pantalla del operario, diferenciada segun la ERS: campos y
  botones grandes, sin menu lateral, solo sus tareas asignadas.

Todas las reglas (tarifa vigente, tope diario, stock, anulacion) las aplica
el backend; esta capa muestra el motivo cuando rechaza una operacion.
"""

from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import _decimal, fecha, uf
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

ESTADO_TAREA = {"pendiente": "Pendiente", "en_ejecucion": "En ejecucion",
                "terminada": "Terminada"}


def _lista(respuesta):
    return respuesta.get("results", respuesta) if isinstance(respuesta, dict) else respuesta


def _horas(valor) -> str:
    texto = f"{_decimal(valor):.2f}".rstrip("0").rstrip(".")
    return f"{texto} h"


# ---------------------------------------------------------------------------
# Dialogo de registro (horas o consumo), usado por el jefe de produccion
# ---------------------------------------------------------------------------
class DialogoRegistro(QDialog):
    """Registrar horas o consumo en una tarea, eligiendo el empleado."""

    def __init__(self, cliente: ClienteAPI, tarea: dict, tipo: str, parent=None):
        super().__init__(parent)
        self.cliente, self.tarea, self.tipo = cliente, tarea, tipo
        titulo = "Registrar horas" if tipo == "horas" else "Registrar consumo de material"
        self.setWindowTitle(f"{titulo} — {tarea['nombre']}")
        self.setMinimumWidth(460)

        formulario = QFormLayout(self)
        self.empleado = QComboBox()
        for e in cliente.empleados():
            self.empleado.addItem(f"{e['nombre']} ({e['cargo']})", e["id_empleado"])
        if tarea.get("empleado"):
            self.empleado.setCurrentIndex(max(0, self.empleado.findData(tarea["empleado"])))
        formulario.addRow("Empleado:", self.empleado)

        if tipo == "horas":
            self.cantidad = QDoubleSpinBox()
            self.cantidad.setRange(0.25, 24)
            self.cantidad.setSingleStep(0.5)
            self.cantidad.setValue(1)
            self.cantidad.setSuffix(" h")
            formulario.addRow("Horas trabajadas hoy:", self.cantidad)
        else:
            self.materiales = cliente.materiales()
            self.bodegas = cliente.bodegas()
            self.material = QComboBox()
            for m in self.materiales:
                self.material.addItem(f"{m['nombre']} ({m['unidad_medida']})", m["id_material"])
            self.bodega = QComboBox()
            for b in self.bodegas:
                self.bodega.addItem(b["nombre"], b["id_bodega"])
            self.cantidad = QDoubleSpinBox()
            self.cantidad.setRange(0.0001, 1_000_000)
            self.cantidad.setDecimals(2)
            self.disponible = QLabel("")
            self.disponible.setObjectName("nota")
            self.material.currentIndexChanged.connect(self._stock)
            self.bodega.currentIndexChanged.connect(self._stock)
            formulario.addRow("Material:", self.material)
            formulario.addRow("Bodega:", self.bodega)
            formulario.addRow("Cantidad:", self.cantidad)
            formulario.addRow("", self.disponible)
            self._stock()

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Ok).setText("Registrar")
        botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
        botones.accepted.connect(self._registrar)
        botones.rejected.connect(self.reject)
        formulario.addRow(botones)

    def _stock(self):
        material = next((m for m in self.materiales
                         if m["id_material"] == self.material.currentData()), None)
        if material:
            saldo = material["stock_por_bodega"].get(str(self.bodega.currentData()), "0")
            self.disponible.setText(
                f"Disponible en la bodega: {_decimal(saldo):.2f} {material['unidad_medida']}"
            )

    def _registrar(self):
        try:
            if self.tipo == "horas":
                self.cliente.registrar_horas(self.tarea["id_tarea"], self.cantidad.value(),
                                             empleado=self.empleado.currentData())
            else:
                self.cliente.registrar_consumo(
                    self.tarea["id_tarea"], self.material.currentData(),
                    self.bodega.currentData(), self.cantidad.value(),
                    empleado=self.empleado.currentData(),
                )
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo registrar", error.mensaje)
            return
        self.accept()


# ---------------------------------------------------------------------------
# Panel de ordenes de trabajo (CU-OT-01 a CU-OT-08)
# ---------------------------------------------------------------------------
class PanelOrdenesTrabajo(PanelBase):
    titulo = "Ordenes de trabajo"
    subtitulo = ("Planifique las tareas, siga el avance en taller y compare el costo "
                 "real con el estimado. La orden se cierra solo con calidad aprobada.")
    columnas = ["Numero", "Cliente", "Modelo", "Avance", "Real / estimado", "Estado"]

    def construir(self):
        division = QSplitter(Qt.Vertical)
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        division.addWidget(self.tabla)

        detalle = QWidget()
        capa = QHBoxLayout(detalle)
        capa.setContentsMargins(0, 0, 0, 0)

        grupo_tareas = QGroupBox("Tareas")
        gt = QVBoxLayout(grupo_tareas)
        self.tareas = QTableWidget()
        self.tareas.setColumnCount(5)
        self.tareas.setHorizontalHeaderLabels(
            ["Tarea", "Responsable", "Horas reg. / est.", "Estado", ""]
        )
        self.tareas.verticalHeader().setVisible(False)
        self.tareas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tareas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tareas.setSelectionMode(QTableWidget.SingleSelection)
        cabecera = self.tareas.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(0, QHeaderView.Stretch)
        self.tareas.setColumnHidden(4, True)
        self.tareas.itemSelectionChanged.connect(self._habilitar_tarea)
        gt.addWidget(self.tareas)

        acciones_tarea = QHBoxLayout()
        self.b_asignar = QPushButton("Asignar responsable")
        self.b_asignar.setObjectName("secundario")
        self.b_asignar.clicked.connect(self._asignar)
        self.b_horas = QPushButton("Registrar horas")
        self.b_horas.setObjectName("secundario")
        self.b_horas.clicked.connect(lambda: self._registrar("horas"))
        self.b_consumo = QPushButton("Registrar consumo")
        self.b_consumo.setObjectName("secundario")
        self.b_consumo.clicked.connect(lambda: self._registrar("consumo"))
        for boton in (self.b_asignar, self.b_horas, self.b_consumo):
            acciones_tarea.addWidget(boton)
        acciones_tarea.addStretch()
        gt.addLayout(acciones_tarea)
        capa.addWidget(grupo_tareas, 3)

        grupo_costo = QGroupBox("Costo y cierre")
        gc = QVBoxLayout(grupo_costo)
        self.resumen = QLabel("Seleccione una orden.")
        self.resumen.setWordWrap(True)
        self.resumen.setAlignment(Qt.AlignTop)
        gc.addWidget(self.resumen)
        gc.addStretch()
        capa.addWidget(grupo_costo, 2)

        division.addWidget(detalle)
        division.setSizes([220, 300])
        self.contenedor.addWidget(division, 1)

        acciones = QHBoxLayout()
        self.b_iniciar = QPushButton("Iniciar fabricacion")
        self.b_iniciar.setObjectName("exito")
        self.b_iniciar.clicked.connect(self._iniciar)
        self.b_calidad = QPushButton("Enviar a calidad")
        self.b_calidad.clicked.connect(self._enviar_calidad)
        self.b_cerrar = QPushButton("Cerrar la orden")
        self.b_cerrar.setObjectName("exito")
        self.b_cerrar.clicked.connect(self._cerrar)
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        for boton in (self.b_iniciar, self.b_calidad, self.b_cerrar):
            acciones.addWidget(boton)
        acciones.addStretch()
        acciones.addWidget(recargar)
        self.contenedor.addLayout(acciones)

        # Solo lectura para los roles con L en la matriz
        self.planifica = self.cliente.puede("orden_trabajo.actualizar")
        self.registra = self.cliente.puede("taller.crear")
        for boton in (self.b_iniciar, self.b_calidad, self.b_cerrar, self.b_asignar):
            boton.setVisible(self.planifica)
        for boton in (self.b_horas, self.b_consumo):
            boton.setVisible(self.planifica and self.registra)

        self.datos = []
        self._seleccion()

    # -- Datos -------------------------------------------------------------
    def refrescar(self):
        seleccion = self._actual()
        try:
            self.datos = _lista(self.cliente.ordenes_trabajo())
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.llenar(self.tabla, [
            [o["numero"], o["cliente_nombre"], f"{o['cantidad']} x {o['modelo_nombre']}",
             f"{_decimal(o['avance_pct']):.0f} %",
             f"{uf(o['costo_real_uf'])} / {uf(o['costo_estimado_uf'])}", o["estado_nombre"]]
            for o in self.datos
        ])
        if seleccion:
            fila = next((i for i, o in enumerate(self.datos)
                         if o["id_orden_trabajo"] == seleccion["id_orden_trabajo"]), -1)
            if fila >= 0:
                self.tabla.selectRow(fila)
        self._seleccion()

    def _actual(self):
        fila = self.tabla.currentRow() if hasattr(self, "tabla") else -1
        datos = getattr(self, "datos", [])
        return datos[fila] if 0 <= fila < len(datos) else None

    def _tarea(self):
        ot = self._actual()
        fila = self.tareas.currentRow()
        if ot and 0 <= fila < len(ot["tareas"]):
            return ot["tareas"][fila]
        return None

    def _seleccion(self):
        ot = self._actual()
        codigo = ot["estado_codigo"] if ot else ""
        self.b_iniciar.setEnabled(codigo == "planificada")
        self.b_calidad.setEnabled(codigo == "en_ejecucion")
        self.b_cerrar.setEnabled(codigo == "en_calidad")

        if ot is None:
            self.tareas.setRowCount(0)
            self.resumen.setText("Seleccione una orden.")
            self._habilitar_tarea()
            return

        self.tareas.setRowCount(len(ot["tareas"]))
        for i, t in enumerate(ot["tareas"]):
            valores = [f"{t['secuencia']}. {t['nombre']}", t.get("empleado_nombre") or "—",
                       f"{_horas(t['horas_registradas'])} / {_horas(t['horas_estimadas'])}",
                       ESTADO_TAREA.get(t["estado"], t["estado"]), ""]
            for j, valor in enumerate(valores):
                self.tareas.setItem(i, j, QTableWidgetItem(valor))
        self._habilitar_tarea()

        desviacion = _decimal(ot["desviacion_pct"])
        # Mientras la orden se fabrica el costo real es parcial: la desviacion
        # solo se marca como problema cuando ya no quedan registros por hacer
        final = codigo in ("en_calidad", "cerrada")
        color = ("#b42318" if ot["desviacion_requiere_justificacion"] else "#1a7f37") \
            if final else "#6c757d"
        nota_parcial = "" if final else " (parcial, en fabricacion)"
        lineas = [
            f"<b>{ot['numero']}</b> · OC {ot['orden_compra_numero']}",
            f"Inicio: {fecha(ot.get('fecha_inicio'))}"
            + (f" · Cierre: {fecha(ot['fecha_cierre'])}" if ot.get("fecha_cierre") else ""),
            "",
            f"Materiales: {uf(ot['costo_materiales_uf'], 4)}",
            f"Horas hombre: {uf(ot['costo_hh_uf'], 4)}",
            f"<b>Costo real: {uf(ot['costo_real_uf'], 4)}</b>",
            f"Costo estimado: {uf(ot['costo_estimado_uf'], 4)}",
            f"Desviacion: <span style='color:{color}'><b>{desviacion:+.2f} %</b></span>"
            f"{nota_parcial}",
        ]
        if ot["impedimentos_cierre"] and codigo in ("en_ejecucion", "en_calidad"):
            lineas += ["", "<b>Pendiente para cerrar:</b>"]
            lineas += [f"• {texto}" for texto in ot["impedimentos_cierre"]]
        self.resumen.setText("<br>".join(lineas))

    def _habilitar_tarea(self):
        ot, tarea = self._actual(), self._tarea()
        activa = bool(tarea) and tarea["estado"] != "terminada"
        codigo = ot["estado_codigo"] if ot else ""
        self.b_asignar.setEnabled(activa and codigo in ("planificada", "en_ejecucion"))
        self.b_horas.setEnabled(activa and codigo == "en_ejecucion")
        self.b_consumo.setEnabled(activa and codigo == "en_ejecucion")

    # -- Acciones ------------------------------------------------------------
    def _ejecutar(self, operacion, *args, exito: str):
        try:
            operacion(*args)
        except ErrorAPI as error:
            QMessageBox.warning(self, "Operacion rechazada", error.mensaje)
            return False
        if exito:
            QMessageBox.information(self, "Listo", exito)
        self.refrescar()
        return True

    def _asignar(self):
        tarea = self._tarea()
        if not tarea:
            return
        try:
            empleados = self.cliente.empleados()
        except ErrorAPI as error:
            return self.manejar_error(error)
        opciones = [f"{e['nombre']} ({e['cargo']})" for e in empleados]
        elegido, ok = QInputDialog.getItem(self, "Asignar responsable",
                                           f"Responsable de «{tarea['nombre']}»:",
                                           opciones, 0, False)
        if ok:
            empleado = empleados[opciones.index(elegido)]
            self._ejecutar(self.cliente.asignar_tarea, tarea["id_tarea"],
                           empleado["id_empleado"], exito="")

    def _registrar(self, tipo: str):
        tarea = self._tarea()
        if not tarea:
            return
        try:
            dialogo = DialogoRegistro(self.cliente, tarea, tipo, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec():
            self.refrescar()

    def _iniciar(self):
        ot = self._actual()
        sin_responsable = [t["nombre"] for t in ot["tareas"] if not t.get("empleado")]
        if sin_responsable and QMessageBox.question(
            self, "Tareas sin responsable",
            f"{len(sin_responsable)} tarea(s) no tienen responsable. ¿Iniciar igual?",
        ) != QMessageBox.Yes:
            return
        self._ejecutar(self.cliente.iniciar_ot, ot["id_orden_trabajo"],
                       exito=f"{ot['numero']} en ejecucion.")

    def _enviar_calidad(self):
        ot = self._actual()
        self._ejecutar(self.cliente.enviar_ot_a_calidad, ot["id_orden_trabajo"],
                       exito=f"{ot['numero']} paso a control de calidad.")

    def _cerrar(self):
        ot = self._actual()
        justificacion = ""
        if ot["desviacion_requiere_justificacion"]:
            justificacion, ok = QInputDialog.getMultiLineText(
                self, "Justificar desviacion",
                f"El costo real se desvia {ot['desviacion_pct']} % del estimado.\n"
                "Explique la causa (RN-11):",
            )
            if not ok:
                return
        self._ejecutar(self.cliente.cerrar_ot, ot["id_orden_trabajo"], justificacion,
                       exito=f"{ot['numero']} cerrada.")


# ---------------------------------------------------------------------------
# Vista de taller del operario (CU-OT-04, CU-OT-05)
# ---------------------------------------------------------------------------
ESTILO_TALLER = """
QLabel#tarea_titulo { font-size: 22px; font-weight: bold; color: #1f3864; }
QLabel#tarea_detalle { font-size: 16px; color: #394b59; }
QListWidget#lista_tareas { font-size: 17px; }
QListWidget#lista_tareas::item { padding: 16px 10px; border-bottom: 1px solid #dde3ea; }
QListWidget#lista_tareas::item:selected { background: #2f5597; color: white; }
QPushButton#grande { font-size: 18px; padding: 18px 20px; min-height: 30px; }
QDoubleSpinBox#grande, QComboBox#grande { font-size: 18px; padding: 10px; min-height: 32px; }
QFrame#tarjeta { background: white; border: 1px solid #dde3ea; border-radius: 6px; }
"""


class VistaTaller(QWidget):
    """
    Pantalla del operario: sus tareas a la izquierda y, para la elegida, dos
    registros grandes (horas y material) y el boton de terminar.
    """

    def __init__(self, cliente: ClienteAPI):
        super().__init__()
        self.cliente = cliente
        self.tareas_datos: list[dict] = []
        self.materiales: list[dict] = []
        self.bodegas: list[dict] = []
        self.setStyleSheet(ESTILO_TALLER)
        self._construir()

    def _construir(self):
        capa = QHBoxLayout(self)
        capa.setContentsMargins(24, 20, 24, 20)
        capa.setSpacing(20)

        izquierda = QVBoxLayout()
        titulo = QLabel("Mis tareas")
        titulo.setObjectName("tarea_titulo")
        izquierda.addWidget(titulo)
        self.lista = QListWidget()
        self.lista.setObjectName("lista_tareas")
        self.lista.currentRowChanged.connect(self._mostrar)
        izquierda.addWidget(self.lista, 1)
        recargar = QPushButton("Actualizar")
        recargar.setObjectName("grande")
        recargar.clicked.connect(self.refrescar)
        izquierda.addWidget(recargar)
        capa.addLayout(izquierda, 2)

        self.tarjeta = QFrame()
        self.tarjeta.setObjectName("tarjeta")
        derecha = QVBoxLayout(self.tarjeta)
        derecha.setContentsMargins(24, 20, 24, 20)
        derecha.setSpacing(14)
        self.nombre = QLabel("Elija una tarea")
        self.nombre.setObjectName("tarea_titulo")
        self.nombre.setWordWrap(True)
        self.detalle = QLabel("")
        self.detalle.setObjectName("tarea_detalle")
        self.detalle.setWordWrap(True)
        derecha.addWidget(self.nombre)
        derecha.addWidget(self.detalle)

        cuadro_horas = QGroupBox("Horas trabajadas hoy")
        gh = QHBoxLayout(cuadro_horas)
        self.horas = QDoubleSpinBox()
        self.horas.setObjectName("grande")
        self.horas.setRange(0.5, 24)
        self.horas.setSingleStep(0.5)
        self.horas.setValue(1)
        self.horas.setSuffix(" h")
        self.b_horas = QPushButton("Registrar horas")
        self.b_horas.setObjectName("grande")
        self.b_horas.clicked.connect(self._registrar_horas)
        gh.addWidget(self.horas, 1)
        gh.addWidget(self.b_horas, 1)
        derecha.addWidget(cuadro_horas)

        cuadro_material = QGroupBox("Material utilizado")
        gm = QGridLayout(cuadro_material)
        self.material = QComboBox()
        self.material.setObjectName("grande")
        self.bodega = QComboBox()
        self.bodega.setObjectName("grande")
        self.cantidad = QDoubleSpinBox()
        self.cantidad.setObjectName("grande")
        self.cantidad.setRange(0.01, 100000)
        self.cantidad.setDecimals(2)
        self.b_consumo = QPushButton("Registrar material")
        self.b_consumo.setObjectName("grande")
        self.b_consumo.clicked.connect(self._registrar_consumo)
        gm.addWidget(self.material, 0, 0, 1, 2)
        gm.addWidget(self.bodega, 1, 0)
        gm.addWidget(self.cantidad, 1, 1)
        gm.addWidget(self.b_consumo, 2, 0, 1, 2)
        derecha.addWidget(cuadro_material)

        derecha.addStretch()
        self.b_terminar = QPushButton("Marcar la tarea como terminada")
        self.b_terminar.setObjectName("grande")
        self.b_terminar.setStyleSheet("background:#1a7f37;")
        self.b_terminar.clicked.connect(self._terminar)
        derecha.addWidget(self.b_terminar)
        capa.addWidget(self.tarjeta, 3)

        self._habilitar(False)

    # -- Datos -------------------------------------------------------------
    def refrescar(self):
        actual = self._tarea()
        try:
            self.tareas_datos = _lista(self.cliente.tareas({"mias": 1}))
            if not self.materiales:
                self.materiales = self.cliente.materiales()
                self.bodegas = self.cliente.bodegas()
                for m in self.materiales:
                    self.material.addItem(f"{m['nombre']} ({m['unidad_medida']})",
                                          m["id_material"])
                for b in self.bodegas:
                    self.bodega.addItem(b["nombre"], b["id_bodega"])
        except ErrorAPI as error:
            QMessageBox.warning(self, "Error", error.mensaje)
            return

        self.lista.clear()
        for t in self.tareas_datos:
            item = QListWidgetItem(f"{t['orden_trabajo_numero']}\n{t['nombre']}")
            self.lista.addItem(item)
        if not self.tareas_datos:
            self.nombre.setText("No tiene tareas pendientes")
            self.detalle.setText("Cuando el jefe de produccion le asigne una tarea "
                                 "aparecera en esta lista.")
            self._habilitar(False)
            return
        fila = 0
        if actual:
            fila = next((i for i, t in enumerate(self.tareas_datos)
                         if t["id_tarea"] == actual["id_tarea"]), 0)
        self.lista.setCurrentRow(fila)
        self._mostrar(fila)

    def _tarea(self):
        fila = self.lista.currentRow()
        return self.tareas_datos[fila] if 0 <= fila < len(self.tareas_datos) else None

    def _mostrar(self, _fila=None):
        tarea = self._tarea()
        if tarea is None:
            self._habilitar(False)
            return
        self.nombre.setText(tarea["nombre"])
        registradas = _decimal(tarea["horas_registradas"])
        estimadas = _decimal(tarea["horas_estimadas"])
        self.detalle.setText(
            f"{tarea['orden_trabajo_numero']} · {tarea['modelo_nombre']}<br>"
            f"Horas: <b>{_horas(registradas)}</b> de {_horas(estimadas)} estimadas"
        )
        self._habilitar(True)

    def _habilitar(self, activo: bool):
        for widget in (self.horas, self.b_horas, self.material, self.bodega,
                       self.cantidad, self.b_consumo, self.b_terminar):
            widget.setEnabled(activo)

    # -- Registros -----------------------------------------------------------
    def _operar(self, operacion, *args, exito: str):
        try:
            operacion(*args)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo registrar", error.mensaje)
            return
        QMessageBox.information(self, "Registrado", exito)
        self.refrescar()

    def _registrar_horas(self):
        tarea = self._tarea()
        self._operar(self.cliente.registrar_horas, tarea["id_tarea"], self.horas.value(),
                     exito=f"{self.horas.value():g} h registradas en «{tarea['nombre']}».")

    def _registrar_consumo(self):
        tarea = self._tarea()
        self._operar(self.cliente.registrar_consumo, tarea["id_tarea"],
                     self.material.currentData(), self.bodega.currentData(),
                     self.cantidad.value(),
                     exito=f"{self.cantidad.value():g} de {self.material.currentText()} "
                           "registrado.")

    def _terminar(self):
        tarea = self._tarea()
        if QMessageBox.question(self, "Terminar tarea",
                                f"¿Confirma que «{tarea['nombre']}» esta terminada?"
                                ) != QMessageBox.Yes:
            return
        self._operar(self.cliente.terminar_tarea, tarea["id_tarea"],
                     exito="Tarea terminada.")
