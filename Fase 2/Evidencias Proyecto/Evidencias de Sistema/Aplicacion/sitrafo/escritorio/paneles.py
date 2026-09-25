"""
Paneles de la aplicacion de escritorio.

Cada panel consume la API REST a traves de ClienteAPI. Ninguno construye
consultas ni accede a la base de datos.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cliente_api import ClienteAPI, ErrorAPI


class PanelBase(QWidget):
    """Base con cabecera, tabla y manejo uniforme de errores."""

    titulo = ""
    subtitulo = ""
    columnas: list[str] = []

    def __init__(self, cliente: ClienteAPI):
        super().__init__()
        self.cliente = cliente
        self.contenedor = QVBoxLayout(self)
        self.contenedor.setContentsMargins(24, 20, 24, 20)
        self.contenedor.setSpacing(12)
        self._cabecera()
        self.construir()

    def _cabecera(self):
        titulo = QLabel(self.titulo)
        titulo.setObjectName("titulo")
        self.contenedor.addWidget(titulo)
        if self.subtitulo:
            sub = QLabel(self.subtitulo)
            sub.setObjectName("subtitulo")
            sub.setWordWrap(True)
            self.contenedor.addWidget(sub)

    def construir(self):
        """Las subclases arman su contenido."""

    def crear_tabla(self) -> QTableWidget:
        tabla = QTableWidget()
        tabla.setColumnCount(len(self.columnas))
        tabla.setHorizontalHeaderLabels(self.columnas)
        tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return tabla

    def llenar(self, tabla: QTableWidget, filas: list[list[str]]):
        tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                item = QTableWidgetItem(str(valor))
                if j > 0:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                tabla.setItem(i, j, item)

    def manejar_error(self, error: ErrorAPI):
        QMessageBox.warning(self, "No se pudo completar la operacion", error.mensaje)

    def refrescar(self):
        """Las subclases recargan sus datos."""


class PanelCatalogo(PanelBase):
    """
    Publicacion de modelos en el catalogo web (RF-ADM-06).

    Es el caso mas directo de la regla segun la cual la aplicacion de
    escritorio administra la aplicacion web: al publicar un modelo aqui,
    aparece de inmediato en el catalogo que ve el cliente.
    """

    titulo = "Catalogo de productos"
    subtitulo = ("Controle que modelos son visibles para el cliente en la "
                 "aplicacion web. El cambio se aplica de inmediato.")
    columnas = ["Codigo", "Nombre", "Familia", "Precio UF", "En la web"]

    def construir(self):
        barra = QHBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar por codigo o nombre")
        self.busqueda.returnPressed.connect(self.refrescar)
        barra.addWidget(self.busqueda)

        buscar = QPushButton("Buscar")
        buscar.setObjectName("secundario")
        buscar.clicked.connect(self.refrescar)
        barra.addWidget(buscar)
        self.contenedor.addLayout(barra)

        self.tabla = self.crear_tabla()
        self.tabla.doubleClicked.connect(self.alternar)
        self.contenedor.addWidget(self.tabla)

        acciones = QHBoxLayout()
        self.boton = QPushButton("Publicar o retirar el modelo seleccionado")
        self.boton.clicked.connect(self.alternar)
        acciones.addWidget(self.boton)

        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)

        self.datos = []

    def refrescar(self):
        params = {}
        if self.busqueda.text().strip():
            params["search"] = self.busqueda.text().strip()
        try:
            respuesta = self.cliente.modelos(params)
        except ErrorAPI as error:
            return self.manejar_error(error)

        self.datos = respuesta.get("results", respuesta)
        self.llenar(self.tabla, [
            [
                m["codigo"],
                m["nombre"],
                m.get("familia_nombre", ""),
                m.get("precio_vigente") or "sin precio",
                "Publicado" if m["publicado"] else "Retirado",
            ]
            for m in self.datos
        ])

    def alternar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(
                self, "Seleccione un modelo",
                "Elija una fila de la tabla para cambiar su publicacion.",
            )
            return

        modelo = self.datos[fila]
        try:
            resultado = self.cliente.alternar_publicacion(modelo["id_modelo"])
        except ErrorAPI as error:
            return self.manejar_error(error)

        estado = "publicado en" if resultado["publicado"] else "retirado de"
        QMessageBox.information(
            self, "Catalogo actualizado",
            f"{resultado['nombre']} fue {estado} el catalogo web.\n\n"
            "El cambio quedo registrado en la bitacora de auditoria.",
        )
        self.refrescar()


class PanelClientes(PanelBase):
    titulo = "Clientes"
    subtitulo = "Clientes registrados en el sistema."
    columnas = ["RUT", "Razon social", "Tipo", "Estado", "Contactos", "Direcciones"]

    def construir(self):
        barra = QHBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar por RUT o razon social")
        self.busqueda.returnPressed.connect(self.refrescar)
        barra.addWidget(self.busqueda)
        buscar = QPushButton("Buscar")
        buscar.setObjectName("secundario")
        buscar.clicked.connect(self.refrescar)
        barra.addWidget(buscar)
        self.contenedor.addLayout(barra)

        self.tabla = self.crear_tabla()
        self.contenedor.addWidget(self.tabla)

    def refrescar(self):
        params = {}
        if self.busqueda.text().strip():
            params["search"] = self.busqueda.text().strip()
        try:
            respuesta = self.cliente.clientes(params)
        except ErrorAPI as error:
            return self.manejar_error(error)

        registros = respuesta.get("results", respuesta)
        self.llenar(self.tabla, [
            [
                c["rut"], c["razon_social"], c["tipo_persona"], c["estado"],
                len(c.get("contactos", [])), len(c.get("direcciones", [])),
            ]
            for c in registros
        ])


class PanelSolicitudes(PanelBase):
    """Bandeja de solicitudes de presupuesto (CU-COM-02)."""

    titulo = "Solicitudes de presupuesto"
    subtitulo = "Solicitudes recibidas desde la aplicacion web del cliente."
    columnas = ["Numero", "Cliente", "Modelo", "Unidades", "Estado", "Recibida"]

    def construir(self):
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self.mostrar_especificacion)
        self.contenedor.addWidget(self.tabla)

        self.detalle = QGroupBox("Especificacion tecnica solicitada")
        detalle_layout = QVBoxLayout(self.detalle)
        self.texto_detalle = QLabel("Seleccione una solicitud.")
        self.texto_detalle.setWordWrap(True)
        detalle_layout.addWidget(self.texto_detalle)
        self.contenedor.addWidget(self.detalle)

        acciones = QHBoxLayout()
        asignar = QPushButton("Asignarme la solicitud")
        asignar.setObjectName("secundario")
        asignar.clicked.connect(self.asignar)
        acciones.addWidget(asignar)
        cotizar = QPushButton("Elaborar cotizacion")
        cotizar.clicked.connect(self.cotizar)
        acciones.addWidget(cotizar)
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)

        self.datos = []

    def refrescar(self):
        try:
            respuesta = self.cliente.solicitudes()
        except ErrorAPI as error:
            return self.manejar_error(error)

        self.datos = respuesta.get("results", respuesta)
        self.llenar(self.tabla, [
            [
                s["numero"], s.get("cliente_nombre", ""),
                s.get("modelo_nombre") or "sin modelo", s["cantidad"],
                s.get("estado_nombre", "") + (
                    f" ({s['ejecutivo_nombre']})" if s.get("ejecutivo_nombre") else ""
                ),
                s["creado_en"][:10],
            ]
            for s in self.datos
        ])

    def mostrar_especificacion(self):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.datos):
            return
        solicitud = self.datos[fila]
        especificaciones = solicitud.get("especificaciones", [])
        if not especificaciones:
            self.texto_detalle.setText("La solicitud no registra especificacion tecnica.")
            return
        lineas = [
            f"  •  {e['parametro_nombre']}: {e['valor']} {e.get('unidad', '')}".rstrip()
            for e in especificaciones
        ]
        self.texto_detalle.setText("\n".join(lineas))

    def asignar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione una solicitud", "Elija una fila.")
            return
        try:
            resultado = self.cliente.asignar_solicitud(self.datos[fila]["id_solicitud"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(
            self, "Solicitud asignada",
            f"La solicitud {resultado['numero']} quedo a su nombre.",
        )
        self.refrescar()


    def cotizar(self):
        """Abre el formulario de cotizacion con el costeo del backend (CU-COM-03)."""
        from paneles_comercial import DialogoCotizacion

        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.datos):
            QMessageBox.information(self, "Seleccione una solicitud", "Elija una fila.")
            return
        solicitud = self.datos[fila]
        try:
            dialogo = DialogoCotizacion(self.cliente, solicitud, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec() and dialogo.resultado:
            QMessageBox.information(
                self, "Cotizacion creada",
                f"Se creo el borrador {dialogo.resultado['numero']}. Reviselo y "
                "emitalo desde el panel Cotizaciones.",
            )
            self.refrescar()


class PanelCanalWeb(PanelBase):
    """
    Administracion del canal web (RF-ADM-01 a RF-ADM-05).

    Este panel es la demostracion concreta de que la aplicacion de escritorio
    administra la aplicacion web: los interruptores cambian el comportamiento
    del sitio en tiempo de ejecucion, y cada cambio queda auditado.
    """

    titulo = "Administracion del canal web"
    subtitulo = ("Controle el comportamiento de la aplicacion web. Cada cambio "
                 "queda registrado en la bitacora de auditoria con responsable "
                 "y fecha.")

    def construir(self):
        self.interruptores = {}

        grupo = QGroupBox("Estado del sitio")
        formulario = QFormLayout(grupo)
        formulario.setSpacing(10)

        for clave, etiqueta in [
            ("web.modo_mantencion", "Modo mantencion (suspende el sitio)"),
            ("web.pago_en_linea_habilitado", "Pago en linea habilitado"),
            ("web.autorregistro_habilitado", "Registro de nuevos clientes"),
        ]:
            caja = QCheckBox(etiqueta)
            caja.clicked.connect(lambda _, c=clave: self.alternar(c))
            self.interruptores[clave] = caja
            formulario.addRow(caja)

        self.contenedor.addWidget(grupo)

        grupo_texto = QGroupBox("Aviso de mantencion")
        layout_texto = QVBoxLayout(grupo_texto)
        self.mensaje = QLineEdit()
        self.mensaje.setPlaceholderText("Texto que vera el cliente durante la mantencion")
        layout_texto.addWidget(self.mensaje)
        guardar = QPushButton("Guardar aviso")
        guardar.clicked.connect(self.guardar_mensaje)
        layout_texto.addWidget(guardar, alignment=Qt.AlignLeft)
        self.contenedor.addWidget(grupo_texto)

        grupo_comercial = QGroupBox("Parametros comerciales y productivos")
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Parametro", "Valor", "Descripcion"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout_comercial = QVBoxLayout(grupo_comercial)
        layout_comercial.addWidget(self.tabla)
        self.contenedor.addWidget(grupo_comercial)

        self.estado = QLabel("")
        self.estado.setObjectName("subtitulo")
        self.contenedor.addWidget(self.estado)

    def refrescar(self):
        try:
            parametros = self.cliente.parametros()
        except ErrorAPI as error:
            return self.manejar_error(error)

        por_clave = {p["clave"]: p for p in parametros}

        for clave, caja in self.interruptores.items():
            parametro = por_clave.get(clave)
            caja.blockSignals(True)
            caja.setChecked(bool(parametro and parametro["valor_tipado"]))
            caja.setEnabled(parametro is not None)
            caja.blockSignals(False)

        aviso = por_clave.get("web.mensaje_mantencion")
        self.mensaje.setText(aviso["valor"] if aviso else "")

        otros = [
            p for p in parametros
            if p["ambito"] in ("comercial", "produccion", "sistema")
        ]
        self.tabla.setRowCount(len(otros))
        for i, p in enumerate(otros):
            self.tabla.setItem(i, 0, QTableWidgetItem(p["clave"]))
            self.tabla.setItem(i, 1, QTableWidgetItem(p["valor"]))
            self.tabla.setItem(i, 2, QTableWidgetItem(p.get("descripcion", "")))

        if self.interruptores["web.modo_mantencion"].isChecked():
            self.estado.setText("El sitio se encuentra SUSPENDIDO para los clientes.")
            self.estado.setStyleSheet("color: #b02a37; font-weight: bold;")
        else:
            self.estado.setText("El sitio se encuentra operativo.")
            self.estado.setStyleSheet("color: #1a7f37;")

    def alternar(self, clave: str):
        try:
            resultado = self.cliente.alternar_parametro(clave)
        except ErrorAPI as error:
            self.manejar_error(error)
            return self.refrescar()

        if clave == "web.modo_mantencion" and resultado["valor_tipado"]:
            QMessageBox.warning(
                self, "Sitio suspendido",
                "La aplicacion web quedo en modo mantencion.\n\n"
                "Los clientes veran el aviso configurado y no podran operar "
                "hasta que se desactive.",
            )
        self.refrescar()

    def guardar_mensaje(self):
        try:
            self.cliente.actualizar_parametro(
                "web.mensaje_mantencion", self.mensaje.text().strip()
            )
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(self, "Aviso guardado", "El texto fue actualizado.")


class PanelIntegraciones(PanelBase):
    """Log de llamadas a servicios externos (RF-INT-01)."""

    titulo = "Integraciones con servicios externos"
    subtitulo = ("Registro de todas las llamadas a servicios externos, con su "
                 "resultado y latencia.")
    columnas = ["Fecha", "Servicio", "Recurso", "Codigo", "Latencia", "Resultado"]

    def construir(self):
        barra = QHBoxLayout()
        self.filtro = QComboBox()
        self.filtro.addItems(["Todas", "Solo fallidas", "Solo exitosas"])
        self.filtro.currentIndexChanged.connect(self.refrescar)
        barra.addWidget(QLabel("Mostrar:"))
        barra.addWidget(self.filtro)
        barra.addStretch()
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        barra.addWidget(recargar)
        self.contenedor.addLayout(barra)

        self.tabla = self.crear_tabla()
        self.contenedor.addWidget(self.tabla)

        self.resumen = QLabel("")
        self.resumen.setObjectName("subtitulo")
        self.contenedor.addWidget(self.resumen)

    def refrescar(self):
        params = {}
        if self.filtro.currentIndex() == 1:
            params["exitoso"] = "false"
        elif self.filtro.currentIndex() == 2:
            params["exitoso"] = "true"

        try:
            respuesta = self.cliente.log_integraciones(params)
        except ErrorAPI as error:
            return self.manejar_error(error)

        registros = respuesta.get("results", respuesta)
        self.llenar(self.tabla, [
            [
                r["fecha_hora"][:19].replace("T", " "),
                r["servicio"],
                r["endpoint"][-45:],
                r["codigo_respuesta"] or "sin respuesta",
                f"{r['latencia_ms']} ms",
                "OK" if r["exitoso"] else "ERROR",
            ]
            for r in registros
        ])

        total = respuesta.get("count", len(registros))
        fallidas = sum(1 for r in registros if not r["exitoso"])
        self.resumen.setText(
            f"{total} llamada(s) registrada(s). {fallidas} con error en esta pagina."
        )
