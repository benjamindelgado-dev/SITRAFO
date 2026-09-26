"""
Paneles del control de calidad (HU-09).

- PanelControlCalidad: el inspector ejecuta los ensayos de las ordenes que
  produccion envio a calidad. Ingresa el valor medido; el sistema decide si
  es conforme segun el rango del protocolo y, si no, abre la no conformidad.
- PanelNoConformidades: seguimiento y cierre con accion correctiva.
- PanelProtocolos: definicion de los ensayos de cada modelo, versionados.

Produccion, comercial y administracion los ven segun la matriz, en lectura.
"""
from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import _decimal, fecha
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
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
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

SEVERIDADES = [("mayor", "Mayor"), ("menor", "Menor"), ("critica", "Critica")]
VERDE, ROJO, GRIS = QColor("#e6f4ea"), QColor("#fdecea"), QColor("#f1f3f5")


def _num(valor) -> str:
    if valor in (None, ""):
        return ""
    texto = f"{_decimal(valor):f}"
    return texto.rstrip("0").rstrip(".") if "." in texto else texto


def rango(punto: dict) -> str:
    inf, sup, u = _num(punto["tolerancia_inf"]), _num(punto["tolerancia_sup"]), punto["unidad"]
    if inf and sup:
        return f"{inf} a {sup} {u}"
    return f"≥ {inf} {u}" if inf else f"≤ {sup} {u}"


def _tabla(columnas: list[str], estirar: int = 0) -> QTableWidget:
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(QTableWidget.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    tabla.setSelectionMode(QTableWidget.SingleSelection)
    cabecera = tabla.horizontalHeader()
    cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
    cabecera.setSectionResizeMode(estirar, QHeaderView.Stretch)
    return tabla


# ---------------------------------------------------------------------------
# Ejecucion de ensayos (CU-CAL-03, CU-CAL-04)
# ---------------------------------------------------------------------------
class PanelControlCalidad(PanelBase):
    titulo = "Control de calidad"
    subtitulo = ("Ordenes enviadas a calidad. Registre el valor medido de cada ensayo: "
                 "el sistema evalua la conformidad contra el rango del protocolo.")
    columnas = ["Orden", "Cliente", "Modelo", "Control", "Estado del control"]

    def construir(self):
        division = QSplitter(Qt.Vertical)
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion_ot)
        division.addWidget(self.tabla)

        detalle = QWidget()
        capa = QVBoxLayout(detalle)
        capa.setContentsMargins(0, 0, 0, 0)
        barra = QHBoxLayout()
        self.titulo_control = QLabel("Seleccione una orden.")
        self.titulo_control.setObjectName("subtitulo")
        barra.addWidget(self.titulo_control, 1)
        self.b_iniciar = QPushButton("Iniciar control con protocolo")
        self.b_iniciar.clicked.connect(self._iniciar)
        barra.addWidget(self.b_iniciar)
        capa.addLayout(barra)

        self.puntos = _tabla(["#", "Ensayo", "Rango aceptable", "Ultima medicion",
                              "Resultado", "Obligatorio"], estirar=1)
        self.puntos.itemSelectionChanged.connect(self._habilitar_medicion)
        capa.addWidget(self.puntos, 1)

        medicion = QGroupBox("Registrar medicion del ensayo seleccionado")
        fm = QHBoxLayout(medicion)
        self.valor = QDoubleSpinBox()
        self.valor.setRange(-1_000_000, 1_000_000)
        self.valor.setDecimals(4)
        self.severidad = QComboBox()
        for codigo, nombre in SEVERIDADES:
            self.severidad.addItem(f"Si no cumple: {nombre}", codigo)
        self.observacion = QLineEdit()
        self.observacion.setPlaceholderText("Observacion (opcional)")
        self.b_medir = QPushButton("Registrar")
        self.b_medir.setObjectName("exito")
        self.b_medir.clicked.connect(self._medir)
        fm.addWidget(QLabel("Valor:"))
        fm.addWidget(self.valor)
        fm.addWidget(self.severidad)
        fm.addWidget(self.observacion, 1)
        fm.addWidget(self.b_medir)
        capa.addWidget(medicion)
        self.cuadro_medicion = medicion
        division.addWidget(detalle)
        division.setSizes([200, 360])
        self.contenedor.addWidget(division, 1)

        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        pie = QHBoxLayout()
        pie.addStretch()
        pie.addWidget(recargar)
        self.contenedor.addLayout(pie)

        self.ejecuta = self.cliente.puede("ensayo.crear")
        self.b_iniciar.setVisible(self.ejecuta)
        medicion.setVisible(self.ejecuta)
        self.ordenes, self.controles, self.control = [], {}, None
        self._seleccion_ot()

    # -- Datos -------------------------------------------------------------
    def refrescar(self):
        actual = self._ot()
        try:
            respuesta = self.cliente.ordenes_trabajo()
            todas = respuesta.get("results", respuesta)
            controles = self.cliente.controles_calidad()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.ordenes = [o for o in todas if o["estado_codigo"] == "en_calidad"]
        self.controles = {}
        for c in controles:
            self.controles.setdefault(c["orden_trabajo"], []).append(c)
        self.llenar(self.tabla, [
            [o["numero"], o["cliente_nombre"], o["modelo_nombre"],
             ", ".join(c["protocolo_nombre"] for c in self.controles.get(
                 o["id_orden_trabajo"], [])) or "sin iniciar",
             ", ".join(c["estado_nombre"] for c in self.controles.get(
                 o["id_orden_trabajo"], [])) or "—"]
            for o in self.ordenes
        ])
        if actual:
            fila = next((i for i, o in enumerate(self.ordenes)
                         if o["id_orden_trabajo"] == actual["id_orden_trabajo"]), -1)
            if fila >= 0:
                self.tabla.selectRow(fila)
        self._seleccion_ot()

    def _ot(self):
        fila = self.tabla.currentRow() if hasattr(self, "tabla") else -1
        ordenes = getattr(self, "ordenes", [])
        return ordenes[fila] if 0 <= fila < len(ordenes) else None

    def _seleccion_ot(self):
        ot = self._ot()
        controles = self.controles.get(ot["id_orden_trabajo"], []) if ot else []
        self.control = controles[0] if controles else None
        self.b_iniciar.setEnabled(ot is not None and self.control is None)
        if ot is None:
            self.titulo_control.setText("Seleccione una orden en control de calidad.")
        elif self.control is None:
            self.titulo_control.setText(f"{ot['numero']}: aun no se inicia el control.")
        else:
            c = self.control
            self.titulo_control.setText(
                f"{ot['numero']} · {c['protocolo_nombre']} · inspector "
                f"{c['inspector_nombre']} · <b>{c['estado_nombre']}</b>")
        self._mostrar_puntos()

    def _mostrar_puntos(self):
        puntos = self.control["puntos"] if self.control else []
        self.puntos.setRowCount(len(puntos))
        for i, p in enumerate(puntos):
            if p["conforme"] is None:
                resultado, color = "Pendiente", GRIS
            elif p["conforme"]:
                resultado, color = "Conforme", VERDE
            else:
                nc = p["no_conformidad"] or {}
                resultado = "NO conforme · NC " + ("abierta" if nc.get("estado") == "abierta"
                                                   else "cerrada")
                color = ROJO if nc.get("estado") == "abierta" else GRIS
            medicion = (f"{_num(p['valor_medido'])} {p['unidad']}"
                        + (f" ({p['mediciones']} mediciones)" if p["mediciones"] > 1 else "")
                        if p["valor_medido"] is not None else "—")
            valores = [p["secuencia"], p["nombre"], rango(p), medicion, resultado,
                       "Si" if p["obligatorio"] else "No"]
            for j, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))
                if j == 4:
                    item.setBackground(color)
                self.puntos.setItem(i, j, item)
        self._habilitar_medicion()

    def _punto(self):
        fila = self.puntos.currentRow()
        puntos = self.control["puntos"] if self.control else []
        return puntos[fila] if 0 <= fila < len(puntos) else None

    def _habilitar_medicion(self):
        punto = self._punto()
        nc_abierta = bool(punto and punto["no_conformidad"]
                          and punto["no_conformidad"]["estado"] == "abierta")
        self.cuadro_medicion.setEnabled(punto is not None and not nc_abierta)
        if punto is not None and punto["valor_esperado"] is not None:
            self.valor.setValue(float(_decimal(punto["valor_esperado"])))

    # -- Acciones ------------------------------------------------------------
    def _iniciar(self):
        ot = self._ot()
        try:
            protocolos = self.cliente.protocolos({"activo": True, "modelo": ot["modelo"]})
        except ErrorAPI as error:
            return self.manejar_error(error)
        if not protocolos:
            QMessageBox.warning(self, "Sin protocolo",
                                f"No hay un protocolo vigente para {ot['modelo_nombre']}. "
                                "Definalo en el panel Protocolos de calidad.")
            return
        opciones = [f"{p['nombre']} v{p['version']} ({len(p['puntos'])} ensayos)"
                    for p in protocolos]
        elegido, ok = QInputDialog.getItem(self, "Iniciar control",
                                           f"Protocolo para {ot['numero']}:",
                                           opciones, 0, False)
        if not ok:
            return
        try:
            self.cliente.iniciar_control(ot["id_orden_trabajo"],
                                         protocolos[opciones.index(elegido)]["id_protocolo"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.refrescar()

    def _medir(self):
        punto = self._punto()
        fila = self.puntos.currentRow()
        try:
            control = self.cliente.registrar_resultado(self.control["id_control"], {
                "punto": punto["id_punto"], "valor": f"{self.valor.value():.4f}",
                "observacion": self.observacion.text(),
                "severidad": self.severidad.currentData(),
            })
        except ErrorAPI as error:
            return self.manejar_error(error)
        nuevo = control["puntos"][fila]
        if nuevo["conforme"] is False:
            QMessageBox.warning(
                self, "Resultado no conforme",
                f"«{punto['nombre']}» midio {_num(nuevo['valor_medido'])} {punto['unidad']}, "
                f"fuera del rango {rango(punto)}.\n\nSe abrio una no conformidad. Registre "
                "la accion correctiva en el panel No conformidades y repita el ensayo.",
            )
        self.observacion.clear()
        self.refrescar()
        self.puntos.selectRow(min(fila + 1, self.puntos.rowCount() - 1))


# ---------------------------------------------------------------------------
# No conformidades (CU-CAL-05)
# ---------------------------------------------------------------------------
class PanelNoConformidades(PanelBase):
    titulo = "No conformidades"
    subtitulo = ("Desviaciones detectadas en los ensayos. Mientras una este abierta, "
                 "la orden de trabajo no puede cerrarse (RN-12).")
    columnas = ["Orden", "Ensayo", "Medido", "Severidad", "Estado", "Abierta",
                "Accion correctiva"]

    def construir(self):
        barra = QHBoxLayout()
        barra.addWidget(QLabel("Mostrar:"))
        self.filtro = QComboBox()
        self.filtro.addItem("Abiertas", "abierta")
        self.filtro.addItem("Cerradas", "cerrada")
        self.filtro.addItem("Todas", None)
        self.filtro.currentIndexChanged.connect(self.refrescar)
        barra.addWidget(self.filtro)
        barra.addStretch()
        self.contenedor.addLayout(barra)

        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        self.contenedor.addWidget(self.tabla, 1)
        self.detalle = QLabel("")
        self.detalle.setWordWrap(True)
        self.contenedor.addWidget(self.detalle)

        acciones = QHBoxLayout()
        self.b_cerrar = QPushButton("Cerrar con accion correctiva")
        self.b_cerrar.setObjectName("exito")
        self.b_cerrar.clicked.connect(self._cerrar)
        self.b_cerrar.setVisible(self.cliente.puede("no_conformidad.actualizar"))
        acciones.addWidget(self.b_cerrar)
        acciones.addStretch()
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        self.contenedor.addLayout(acciones)
        self.datos = []
        self._seleccion()

    def refrescar(self):
        estado = self.filtro.currentData()
        try:
            self.datos = self.cliente.no_conformidades({"estado": estado} if estado else None)
        except ErrorAPI as error:
            return self.manejar_error(error)
        nombres = dict(SEVERIDADES)
        self.llenar(self.tabla, [
            [n["orden_trabajo"], n["punto"], _num(n["valor_medido"]),
             nombres.get(n["severidad"], n["severidad"]), n["estado"].capitalize(),
             fecha(n["abierta_en"]), (n["accion_correctiva"] or "—")[:50]]
            for n in self.datos
        ])
        self._seleccion()

    def _actual(self):
        fila = self.tabla.currentRow()
        return self.datos[fila] if 0 <= fila < len(getattr(self, "datos", [])) else None

    def _seleccion(self):
        n = self._actual()
        self.b_cerrar.setEnabled(bool(n) and n["estado"] == "abierta")
        if n is None:
            self.detalle.setText("")
            return
        texto = f"<b>{n['descripcion']}</b><br>Abierta por {n['responsable_nombre']}"
        if n["estado"] == "cerrada":
            texto += (f"<br>Cerrada por {n['cerrada_por']} el {fecha(n['cerrada_en'])}: "
                      f"{n['accion_correctiva']}")
        self.detalle.setText(texto)

    def _cerrar(self):
        n = self._actual()
        accion, ok = QInputDialog.getMultiLineText(
            self, "Cerrar no conformidad",
            f"{n['descripcion']}\n\nDescriba la accion correctiva aplicada:")
        if not ok:
            return
        try:
            self.cliente.cerrar_no_conformidad(n["id_no_conformidad"], accion)
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(self, "No conformidad cerrada",
                                "Repita el ensayo en el panel Control de calidad para "
                                "dejar constancia del nuevo resultado.")
        self.refrescar()


# ---------------------------------------------------------------------------
# Protocolos (CU-CAL-01, CU-CAL-02)
# ---------------------------------------------------------------------------
class DialogoProtocolo(QDialog):
    COLUMNAS = ["Ensayo", "Tipo", "Unidad", "Nominal", "Minimo", "Maximo", "Obligatorio"]

    def __init__(self, cliente: ClienteAPI, protocolo: dict | None = None, parent=None):
        super().__init__(parent)
        self.cliente, self.protocolo, self.resultado = cliente, protocolo, None
        self.setWindowTitle("Editar protocolo" if protocolo else "Nuevo protocolo de calidad")
        self.setMinimumSize(820, 520)
        capa = QVBoxLayout(self)

        formulario = QFormLayout()
        self.modelo = QComboBox()
        modelos = cliente.modelos({"page_size": 200})
        for m in modelos.get("results", modelos):
            self.modelo.addItem(f"{m['codigo']} — {m['nombre']}", m["id_modelo"])
        self.nombre = QLineEdit("Ensayos de rutina")
        self.norma = QLineEdit()
        self.norma.setPlaceholderText("Ej.: IEC 60076-1")
        formulario.addRow("Modelo:", self.modelo)
        formulario.addRow("Nombre:", self.nombre)
        formulario.addRow("Norma de referencia:", self.norma)
        capa.addLayout(formulario)

        if protocolo and protocolo["aplicado"]:
            aviso = QLabel("Este protocolo ya se aplico en controles: al guardar se creara la "
                           f"version {protocolo['version'] + 1} y la actual quedara retirada.")
            aviso.setObjectName("nota")
            aviso.setWordWrap(True)
            capa.addWidget(aviso)

        self.tabla = QTableWidget(0, len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        capa.addWidget(self.tabla, 1)
        nota = QLabel("Defina el rango con Minimo y/o Maximo; el nominal es referencial. "
                      "Los ensayos obligatorios condicionan el cierre de la orden.")
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        capa.addWidget(nota)

        filas = QHBoxLayout()
        agregar = QPushButton("Agregar ensayo")
        agregar.setObjectName("secundario")
        agregar.clicked.connect(lambda: self._agregar_fila())
        quitar = QPushButton("Quitar ensayo")
        quitar.setObjectName("secundario")
        quitar.clicked.connect(lambda: self.tabla.removeRow(self.tabla.currentRow()))
        filas.addWidget(agregar)
        filas.addWidget(quitar)
        filas.addStretch()
        capa.addLayout(filas)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)

        if protocolo:
            self.modelo.setCurrentIndex(self.modelo.findData(protocolo["modelo"]))
            self.modelo.setEnabled(False)
            self.nombre.setText(protocolo["nombre"])
            self.norma.setText(protocolo["norma_referencia"])
            for p in protocolo["puntos"]:
                self._agregar_fila(p)
        else:
            self._agregar_fila()

    def _agregar_fila(self, punto: dict | None = None):
        punto = punto or {}
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        valores = [punto.get("nombre", ""), punto.get("tipo_ensayo", "Rutina"),
                   punto.get("unidad", ""), _num(punto.get("valor_esperado")),
                   _num(punto.get("tolerancia_inf")), _num(punto.get("tolerancia_sup"))]
        for j, valor in enumerate(valores):
            self.tabla.setItem(fila, j, QTableWidgetItem(valor))
        casilla = QCheckBox()
        casilla.setChecked(punto.get("obligatorio", True))
        self.tabla.setCellWidget(fila, 6, casilla)

    def _texto(self, fila, columna) -> str:
        item = self.tabla.item(fila, columna)
        return item.text().strip() if item else ""

    def _guardar(self):
        puntos = []
        for fila in range(self.tabla.rowCount()):
            nombre = self._texto(fila, 0)
            if not nombre:
                continue

            def numero(columna, fila=fila):
                texto = self._texto(fila, columna).replace(",", ".")
                return texto or None

            puntos.append({
                "nombre": nombre, "tipo_ensayo": self._texto(fila, 1) or "Rutina",
                "unidad": self._texto(fila, 2), "valor_esperado": numero(3),
                "tolerancia_inf": numero(4), "tolerancia_sup": numero(5),
                "obligatorio": self.tabla.cellWidget(fila, 6).isChecked(),
            })
        datos = {"modelo": self.modelo.currentData(), "nombre": self.nombre.text().strip(),
                 "norma_referencia": self.norma.text().strip(), "puntos": puntos}
        try:
            if self.protocolo:
                self.resultado = self.cliente.actualizar_protocolo(
                    self.protocolo["id_protocolo"], datos)
            else:
                self.resultado = self.cliente.crear_protocolo(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class PanelProtocolos(PanelBase):
    titulo = "Protocolos de calidad"
    subtitulo = ("Ensayos que debe aprobar cada modelo antes de cerrar su orden de "
                 "trabajo. Un protocolo ya aplicado se modifica creando una version nueva.")
    columnas = ["Modelo", "Protocolo", "Version", "Norma", "Ensayos", "Estado"]

    def construir(self):
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        self.contenedor.addWidget(self.tabla, 1)
        self.detalle = _tabla(["#", "Ensayo", "Rango aceptable", "Obligatorio"], estirar=1)
        self.detalle.setMaximumHeight(220)
        self.contenedor.addWidget(self.detalle)

        acciones = QHBoxLayout()
        self.b_nuevo = QPushButton("Nuevo protocolo")
        self.b_nuevo.setObjectName("exito")
        self.b_nuevo.clicked.connect(lambda: self._abrir(None))
        self.b_editar = QPushButton("Editar / nueva version")
        self.b_editar.setObjectName("secundario")
        self.b_editar.clicked.connect(lambda: self._abrir(self._actual()))
        acciones.addWidget(self.b_nuevo)
        acciones.addWidget(self.b_editar)
        acciones.addStretch()
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        self.contenedor.addLayout(acciones)
        self.b_nuevo.setVisible(self.cliente.puede("protocolo_calidad.crear"))
        self.b_editar.setVisible(self.cliente.puede("protocolo_calidad.actualizar"))
        self.datos = []
        self._seleccion()

    def refrescar(self):
        try:
            self.datos = self.cliente.protocolos()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.llenar(self.tabla, [
            [p["modelo_codigo"], p["nombre"], p["version"], p["norma_referencia"] or "—",
             len(p["puntos"]), "Vigente" if p["activo"] else "Retirado"]
            for p in self.datos
        ])
        self._seleccion()

    def _actual(self):
        fila = self.tabla.currentRow()
        return self.datos[fila] if 0 <= fila < len(getattr(self, "datos", [])) else None

    def _seleccion(self):
        p = self._actual()
        self.b_editar.setEnabled(bool(p) and p["activo"])
        puntos = p["puntos"] if p else []
        self.detalle.setRowCount(len(puntos))
        for i, punto in enumerate(puntos):
            for j, valor in enumerate([punto["secuencia"], punto["nombre"], rango(punto),
                                       "Si" if punto["obligatorio"] else "No"]):
                self.detalle.setItem(i, j, QTableWidgetItem(str(valor)))

    def _abrir(self, protocolo):
        try:
            dialogo = DialogoProtocolo(self.cliente, protocolo, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec() and dialogo.resultado:
            r = dialogo.resultado
            QMessageBox.information(self, "Protocolo guardado",
                                    f"{r['nombre']} v{r['version']} para {r['modelo_codigo']}.")
            self.refrescar()
