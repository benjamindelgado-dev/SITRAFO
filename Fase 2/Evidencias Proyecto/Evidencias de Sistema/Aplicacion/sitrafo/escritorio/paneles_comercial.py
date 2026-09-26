"""
Paneles del proceso comercial: elaboracion y emision de cotizaciones, y
gestion de ordenes de compra.

Permiten recorrer desde el escritorio el flujo que antes requeria el admin
de Django: solicitud -> cotizacion -> emision -> orden de compra. Toda
operacion pasa por la API REST (RNF-05) y las reglas de negocio las aplica el
backend: este modulo solo muestra el resultado o el motivo del rechazo.
"""
from decimal import Decimal, InvalidOperation

from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------------------
# Formato
# ---------------------------------------------------------------------------
def _decimal(valor) -> Decimal:
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def uf(valor, decimales: int = 2) -> str:
    if valor in (None, ""):
        return "-"
    texto = f"{_decimal(valor):,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".") + " UF"


def clp(valor) -> str:
    if valor in (None, ""):
        return "-"
    return "$" + f"{_decimal(valor):,.0f}".replace(",", ".")


def fecha(texto) -> str:
    """'2026-09-25' o '2026-09-25T10:00:00' -> '25-09-2026'."""
    if not texto:
        return "-"
    anio, mes, dia = str(texto)[:10].split("-")
    return f"{dia}-{mes}-{anio}"


# ---------------------------------------------------------------------------
# Dialogo: elaborar cotizacion desde una solicitud (CU-COM-03)
# ---------------------------------------------------------------------------
class DialogoCotizacion(QDialog):
    """
    Muestra el costeo que calcula el backend y permite ajustar precio,
    margen, descuento y plazo antes de crear la cotizacion en borrador.
    """

    def __init__(self, cliente: ClienteAPI, solicitud: dict, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.solicitud = solicitud
        self.resultado = None
        self.setWindowTitle(f"Elaborar cotizacion — {solicitud['numero']}")
        self.setMinimumWidth(520)

        self.costeo = cliente.costeo_solicitud(solicitud["id_solicitud"])
        self._construir()
        self._recalcular()

    def _construir(self):
        c = self.costeo
        disposicion = QVBoxLayout(self)

        encabezado = QLabel(
            f"<b>{c['cliente']}</b><br>{c['cantidad']} x {c['modelo']}"
        )
        encabezado.setWordWrap(True)
        disposicion.addWidget(encabezado)

        # -- Costeo calculado por el backend (solo lectura) ----------------
        grupo_costeo = QGroupBox("Costo unitario estimado")
        f1 = QFormLayout(grupo_costeo)
        f1.addRow("Materiales (lista de materiales):", QLabel(uf(c["costo_material_uf"], 4)))
        tarifa = c.get("tarifa_referencia_uf")
        detalle_hh = (f"{c['horas_estandar']} h x {uf(tarifa, 4)}" if tarifa
                      else "sin tarifa de referencia")
        f1.addRow("Horas hombre:", QLabel(f"{uf(c['costo_hh_uf'], 4)}  ({detalle_hh})"))
        f1.addRow("Costo estimado:", QLabel(f"<b>{uf(c['costo_estimado_uf'], 4)}</b>"))
        f1.addRow("Precio base del catalogo:", QLabel(uf(c.get("precio_base_uf"), 4)))
        origen = {
            "costeo": "El precio sugerido se calculo desde el costo mas el margen.",
            "precio_base": "El modelo aun no tiene costeo cargado: se sugiere el "
                           "precio base del catalogo.",
            "sin_precio": "El modelo no tiene costeo ni precio base: ingrese el precio.",
        }[c["origen_precio"]]
        nota = QLabel(origen)
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        f1.addRow(nota)
        disposicion.addWidget(grupo_costeo)

        # -- Condiciones editables ----------------------------------------
        grupo = QGroupBox("Condiciones de la cotizacion")
        f2 = QFormLayout(grupo)

        self.margen = QDoubleSpinBox()
        self.margen.setRange(0, 300)
        self.margen.setDecimals(2)
        self.margen.setSuffix(" %")
        self.margen.setValue(float(_decimal(c["margen_pct"])))
        self.margen.setEnabled(c["origen_precio"] == "costeo")
        self.margen.valueChanged.connect(self._margen_cambio)
        f2.addRow("Margen:", self.margen)

        self.precio = QDoubleSpinBox()
        self.precio.setRange(0, 1_000_000)
        self.precio.setDecimals(4)
        self.precio.setSuffix(" UF")
        self.precio.setValue(float(_decimal(c.get("precio_sugerido_uf") or 0)))
        self.precio.valueChanged.connect(self._recalcular)
        f2.addRow("Precio unitario:", self.precio)

        self.descuento = QDoubleSpinBox()
        self.descuento.setRange(0, 100)
        self.descuento.setDecimals(2)
        self.descuento.setSuffix(" %")
        self.descuento.valueChanged.connect(self._recalcular)
        f2.addRow("Descuento:", self.descuento)

        self.plazo = QSpinBox()
        self.plazo.setRange(1, 365)
        self.plazo.setValue(int(c.get("plazo_defecto_dias_habiles") or 30))
        self.plazo.setSuffix(" dias habiles")
        f2.addRow("Plazo de fabricacion:", self.plazo)
        disposicion.addWidget(grupo)

        # -- Resumen -------------------------------------------------------
        self.total = QLabel("")
        self.total.setObjectName("cifra")
        disposicion.addWidget(self.total)
        self.detalle_total = QLabel("")
        self.detalle_total.setObjectName("nota")
        self.detalle_total.setWordWrap(True)
        disposicion.addWidget(self.detalle_total)

        botones = QDialogButtonBox()
        crear = botones.addButton("Crear borrador", QDialogButtonBox.AcceptRole)
        crear.setObjectName("exito")
        cancelar = botones.addButton("Cancelar", QDialogButtonBox.RejectRole)
        cancelar.setObjectName("secundario")
        botones.accepted.connect(self._crear)
        botones.rejected.connect(self.reject)
        disposicion.addWidget(botones)

    def _margen_cambio(self):
        costo = _decimal(self.costeo["costo_estimado_uf"])
        if costo > 0:
            margen = Decimal(str(self.margen.value()))
            self.precio.setValue(float(costo * (1 + margen / 100)))
        self._recalcular()

    def _recalcular(self):
        cantidad = int(self.costeo["cantidad"])
        bruto = Decimal(str(self.precio.value())) * cantidad
        neto = bruto * (1 - Decimal(str(self.descuento.value())) / 100)
        valor_uf = _decimal(self.costeo.get("valor_uf"))
        self.total.setText(f"Total: {uf(neto)}  ·  {clp(neto * valor_uf)}")
        aviso_uf = "" if self.costeo.get("uf_del_dia") else " (ultimo valor conocido)"
        self.detalle_total.setText(
            f"UF del {fecha(self.costeo.get('fecha_valor_uf'))}: "
            f"{clp(valor_uf)}{aviso_uf}. Se vuelve a congelar al emitir."
        )

    def _crear(self):
        if self.precio.value() <= 0:
            QMessageBox.warning(self, "Falta el precio", "Ingrese el precio unitario.")
            return
        datos = {
            "precio_uf": f"{self.precio.value():.4f}",
            "descuento_pct": f"{self.descuento.value():.2f}",
            "plazo_dias_habiles": self.plazo.value(),
        }
        if self.margen.isEnabled():
            datos["margen_pct"] = f"{self.margen.value():.2f}"
        try:
            self.resultado = self.cliente.cotizar_solicitud(
                self.solicitud["id_solicitud"], datos
            )
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo crear la cotizacion", error.mensaje)
            return
        self.accept()


# ---------------------------------------------------------------------------
# Panel de cotizaciones (CU-COM-05 a CU-COM-07)
# ---------------------------------------------------------------------------
class PanelCotizaciones(PanelBase):
    titulo = "Cotizaciones"
    subtitulo = ("Revise los borradores, envielos a aprobacion si el descuento lo "
                 "exige, emitalos al cliente y genere la orden de compra cuando "
                 "el cliente acepte.")
    columnas = ["Numero", "Cliente", "Total", "Total CLP", "Vence", "Estado"]

    FILTROS = [
        ("Todas", None),
        ("Borradores", "borrador"),
        ("En aprobacion", "en_aprobacion"),
        ("Emitidas", "emitida"),
        ("Aceptadas", "aceptada"),
    ]

    def construir(self):
        barra = QHBoxLayout()
        barra.addWidget(QLabel("Mostrar:"))
        self.filtro = QComboBox()
        self.filtro.addItems([nombre for nombre, _ in self.FILTROS])
        self.filtro.currentIndexChanged.connect(self._mostrar)
        barra.addWidget(self.filtro)
        barra.addStretch()
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        barra.addWidget(recargar)
        self.contenedor.addLayout(barra)

        division = QSplitter(Qt.Vertical)
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        division.addWidget(self.tabla)

        detalle = QWidget()
        detalle_layout = QHBoxLayout(detalle)
        detalle_layout.setContentsMargins(0, 0, 0, 0)

        grupo_lineas = QGroupBox("Detalle")
        gl = QVBoxLayout(grupo_lineas)
        self.lineas = QTableWidget()
        self.lineas.setColumnCount(4)
        self.lineas.setHorizontalHeaderLabels(["Modelo", "Unidades", "Precio unit.", "Costo est."])
        self.lineas.verticalHeader().setVisible(False)
        self.lineas.setEditTriggers(QTableWidget.NoEditTriggers)
        cabecera = self.lineas.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(0, QHeaderView.Stretch)
        gl.addWidget(self.lineas)
        self.condiciones = QLabel("Seleccione una cotizacion.")
        self.condiciones.setWordWrap(True)
        gl.addWidget(self.condiciones)
        detalle_layout.addWidget(grupo_lineas, 3)

        grupo_historial = QGroupBox("Historial")
        gh = QVBoxLayout(grupo_historial)
        self.historial = QLabel("")
        self.historial.setWordWrap(True)
        self.historial.setAlignment(Qt.AlignTop)
        gh.addWidget(self.historial)
        detalle_layout.addWidget(grupo_historial, 2)

        division.addWidget(detalle)
        division.setSizes([300, 220])
        self.contenedor.addWidget(division, 1)

        acciones = QHBoxLayout()
        self.b_aprobacion = QPushButton("Enviar a aprobacion")
        self.b_aprobacion.clicked.connect(self._solicitar_aprobacion)
        self.b_emitir = QPushButton("Emitir al cliente")
        self.b_emitir.setObjectName("exito")
        self.b_emitir.clicked.connect(self._emitir)
        self.b_correo = QPushButton("Reenviar por correo")
        self.b_correo.setObjectName("secundario")
        self.b_correo.clicked.connect(self._reenviar)
        self.b_devolver = QPushButton("Devolver al autor")
        self.b_devolver.setObjectName("peligro")
        self.b_devolver.clicked.connect(self._devolver)
        self.b_oc = QPushButton("Generar orden de compra")
        self.b_oc.clicked.connect(self._generar_oc)
        for boton in (self.b_aprobacion, self.b_emitir, self.b_devolver,
                      self.b_correo, self.b_oc):
            acciones.addWidget(boton)

        # Con acceso de solo lectura (L en la matriz) no se muestran acciones
        puede = self.cliente.puede
        self.b_aprobacion.setVisible(puede("cotizacion.actualizar"))
        self.b_emitir.setVisible(puede("cotizacion.actualizar") or puede("cotizacion.aprobar"))
        self.b_devolver.setVisible(puede("cotizacion.aprobar"))
        self.b_correo.setVisible(puede("cotizacion.actualizar"))
        self.b_oc.setVisible(puede("orden_compra.crear"))
        acciones.addStretch()
        self.contenedor.addLayout(acciones)

        self.todas = []
        self.visibles = []
        self._habilitar(None)

    # -- Datos -------------------------------------------------------------
    def refrescar(self):
        try:
            respuesta = self.cliente.cotizaciones({"ordering": "-creado_en"})
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.todas = respuesta.get("results", respuesta)
        self._mostrar()

    @staticmethod
    def _codigo(cotizacion) -> str:
        return cotizacion.get("estado_codigo") or ""

    def _mostrar(self):
        _, codigo = self.FILTROS[self.filtro.currentIndex()]
        self.visibles = [c for c in self.todas if codigo is None or self._codigo(c) == codigo]
        self.llenar(self.tabla, [
            [c["numero"], c.get("cliente_nombre", ""), uf(c["total_uf"]),
             clp(c.get("total_clp")), fecha(c["vence_el"]), c.get("estado_nombre", "")]
            for c in self.visibles
        ])
        self._seleccion()

    def _actual(self):
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self.visibles):
            return self.visibles[fila]
        return None

    def _seleccion(self):
        c = self._actual()
        self._habilitar(c)
        if c is None:
            self.lineas.setRowCount(0)
            self.condiciones.setText("Seleccione una cotizacion.")
            self.historial.setText("")
            return

        self.lineas.setRowCount(len(c["lineas"]))
        for i, linea in enumerate(c["lineas"]):
            valores = [linea["modelo_nombre"], linea["cantidad"],
                       uf(linea["precio_uf"], 4), uf(linea["costo_estimado_uf"], 4)]
            for j, valor in enumerate(valores):
                self.lineas.setItem(i, j, self._item(valor))

        partes = [f"UF congelada: {clp(c['valor_uf'])} del {fecha(c['fecha_valor_uf'])}"]
        if _decimal(c.get("descuento_pct")) > 0:
            partes.append(f"Descuento: {c['descuento_pct']}%")
        if c.get("plazo_dias_habiles"):
            partes.append(f"Plazo: {c['plazo_dias_habiles']} dias habiles "
                          f"(entrega {fecha(c.get('fecha_entrega'))})")
        partes.append(f"Vence: {fecha(c['vence_el'])}")
        self.condiciones.setText("  ·  ".join(partes))

        self.historial.setText("\n".join(
            f"{fecha(h['fecha_hora'])}  {h['estado_nuevo']} ({h['usuario']})"
            + (f"\n     {h['observacion']}" if h.get("observacion") else "")
            for h in c.get("historial", [])
        ) or "Sin movimientos.")

    @staticmethod
    def _item(valor):
        from PySide6.QtWidgets import QTableWidgetItem

        return QTableWidgetItem(str(valor))

    def _habilitar(self, c):
        """Solo se ofrecen las acciones que el estado permite."""
        codigo = self._codigo(c) if c else ""
        propia = bool(c) and c.get("ejecutivo") == self.cliente.identidad.get("id_usuario")
        self.b_aprobacion.setEnabled(codigo == "borrador")
        # En aprobacion, emitir es aprobar: no la propia (RN-05)
        self.b_emitir.setEnabled(
            codigo == "borrador"
            or (codigo == "en_aprobacion" and self.cliente.puede("cotizacion.aprobar")
                and not propia)
        )
        self.b_emitir.setText("Aprobar y emitir" if codigo == "en_aprobacion"
                              else "Emitir al cliente")
        self.b_devolver.setEnabled(codigo == "en_aprobacion" and not propia)
        self.b_correo.setEnabled(codigo in ("emitida", "aceptada"))
        self.b_oc.setEnabled(codigo == "aceptada" and not (c or {}).get("orden_compra"))

    # -- Acciones ------------------------------------------------------------
    def _ejecutar(self, operacion, exito: str, confirmar: str | None = None):
        c = self._actual()
        if c is None:
            return
        if confirmar and QMessageBox.question(self, "Confirmar", confirmar) != QMessageBox.Yes:
            return
        try:
            resultado = operacion(c["id_cotizacion"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(self, "Listo", exito.format(c=c, r=resultado or {}))
        self.refrescar()

    def _solicitar_aprobacion(self):
        self._ejecutar(self.cliente.solicitar_aprobacion,
                       "La cotizacion {c[numero]} quedo en aprobacion.")

    def _emitir(self):
        self._ejecutar(
            self.cliente.emitir_cotizacion,
            "Cotizacion {c[numero]} emitida. {r[aviso_correo]}",
            "Se emitira la cotizacion al cliente con la UF de hoy y se le enviara "
            "por correo. ¿Continuar?",
        )

    def _devolver(self):
        from PySide6.QtWidgets import QInputDialog

        c = self._actual()
        if c is None:
            return
        motivo, ok = QInputDialog.getText(
            self, "Devolver cotizacion", "Motivo de la devolucion:"
        )
        if not ok:
            return
        try:
            self.cliente.devolver_cotizacion(c["id_cotizacion"], motivo.strip())
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(self, "Devuelta",
                                f"La cotizacion {c['numero']} volvio a borrador.")
        self.refrescar()

    def _reenviar(self):
        self._ejecutar(self.cliente.enviar_cotizacion,
                       "Cotizacion {c[numero]} reenviada por correo.")

    def _generar_oc(self):
        self._ejecutar(
            self.cliente.generar_orden_compra,
            "Orden de compra {r[numero]} generada. El documento de cobro del "
            "anticipo quedo disponible para el cliente.",
            "Se generara la orden de compra desde esta cotizacion. ¿Continuar?",
        )


# ---------------------------------------------------------------------------
# Panel de ordenes de compra (RN-06, RN-07, RN-15)
# ---------------------------------------------------------------------------
class PanelOrdenesCompra(PanelBase):
    titulo = "Ordenes de compra"
    subtitulo = ("Ordenes generadas desde cotizaciones aceptadas. El anticipo se cobra "
                 "al generarla y el saldo al terminar la fabricacion; la entrega se "
                 "registra con el saldo pagado.")
    columnas = ["Numero", "Cliente", "Cotizacion", "Total", "Anticipo", "Saldo", "Estado"]

    ESTADO_ANTICIPO = {"pendiente": "Pendiente", "pagado": "Pagado", "anulado": "Anulado"}

    def construir(self):
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        self.contenedor.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        self.b_confirmar = QPushButton("Confirmar la orden")
        self.b_confirmar.setObjectName("exito")
        self.b_confirmar.clicked.connect(self._confirmar)
        self.b_confirmar.setVisible(self.cliente.puede("orden_compra.actualizar"))
        acciones.addWidget(self.b_confirmar)
        self.b_ot = QPushButton("Generar ordenes de trabajo")
        self.b_ot.clicked.connect(self._generar_ot)
        self.b_ot.setVisible(self.cliente.puede("orden_trabajo.crear"))
        acciones.addWidget(self.b_ot)
        self.b_entrega = QPushButton("Registrar entrega")
        self.b_entrega.setObjectName("exito")
        self.b_entrega.clicked.connect(self._entregar)
        self.b_entrega.setVisible(self.cliente.puede("orden_compra.actualizar"))
        acciones.addWidget(self.b_entrega)
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)

        self.datos = []
        self.b_confirmar.setEnabled(False)
        self.b_ot.setEnabled(False)
        self.b_entrega.setEnabled(False)

    def refrescar(self):
        try:
            respuesta = self.cliente.ordenes_compra({"ordering": "-creado_en"})
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.datos = respuesta.get("results", respuesta)

        def cobro(o, tipo, sin):
            a = o.get(tipo)
            if not a:
                return sin
            return f"{self.ESTADO_ANTICIPO.get(a['estado'], a['estado'])} · {clp(a['monto_clp'])}"

        self.llenar(self.tabla, [
            [o["numero"], o.get("cliente_nombre", ""), o.get("cotizacion_numero", ""),
             uf(o["total_uf"]), cobro(o, "anticipo", "sin emitir"),
             cobro(o, "saldo", "al terminar la fabricacion"), o.get("estado_nombre", "")]
            for o in self.datos
        ])
        self._seleccion()

    def _seleccion(self):
        fila = self.tabla.currentRow()
        orden = self.datos[fila] if 0 <= fila < len(self.datos) else None
        self.b_confirmar.setEnabled(
            bool(orden) and orden.get("estado_codigo") == "pendiente"
        )
        self.b_ot.setEnabled(
            bool(orden) and orden.get("estado_codigo") == "confirmada"
            and not orden.get("ordenes_trabajo")
        )
        # La entrega exige la fabricacion terminada (hay saldo emitido) y pagada
        self.b_entrega.setEnabled(
            bool(orden) and orden.get("estado_codigo") == "en_produccion"
            and (orden.get("saldo") or {}).get("estado") == "pagado"
        )

    def _entregar(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.datos):
            return
        orden = self.datos[fila]
        if QMessageBox.question(self, "Registrar entrega",
                                f"¿Confirma la entrega de {orden['numero']} al cliente?"
                                ) != QMessageBox.Yes:
            return
        try:
            self.cliente.accion(f"ordenes-compra/{orden['id_orden_compra']}/registrar_entrega/")
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(self, "Pedido entregado",
                                f"{orden['numero']} quedo como entregada.")
        self.refrescar()

    def _generar_ot(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.datos):
            return
        orden = self.datos[fila]
        if QMessageBox.question(
            self, "Generar ordenes de trabajo",
            f"Se generaran las ordenes de trabajo de {orden['numero']} con las tareas "
            "estandar de cada modelo. ¿Continuar?",
        ) != QMessageBox.Yes:
            return
        try:
            creadas = self.cliente.generar_ordenes_trabajo(orden["id_orden_compra"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(
            self, "Ordenes de trabajo generadas",
            "Se generaron: " + ", ".join(o["numero"] for o in creadas)
            + ". Planifiquelas en el panel Ordenes de trabajo.",
        )
        self.refrescar()

    def _confirmar(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.datos):
            return
        orden = self.datos[fila]
        anticipo = orden.get("anticipo") or {}
        if anticipo.get("estado") != "pagado":
            respuesta = QMessageBox.question(
                self, "Anticipo sin pagar",
                f"El anticipo de {orden['numero']} aun no esta pagado. "
                "¿Confirmar la orden de todas formas?",
            )
            if respuesta != QMessageBox.Yes:
                return
        try:
            self.cliente.confirmar_orden_compra(orden["id_orden_compra"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(self, "Orden confirmada",
                                f"La orden {orden['numero']} quedo confirmada.")
        self.refrescar()
