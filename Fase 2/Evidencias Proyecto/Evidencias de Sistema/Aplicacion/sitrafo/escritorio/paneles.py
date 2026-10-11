"""
Paneles de la aplicacion de escritorio.

Cada panel consume la API REST a traves de ClienteAPI. Ninguno construye
consultas ni accede a la base de datos.
"""
from cliente_api import ClienteAPI, ErrorAPI
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
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
    QVBoxLayout,
    QWidget,
)


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
        if error.codigo == 403:
            # Sin permiso no se deja a la vista informacion cargada antes
            for tabla in self.findChildren(QTableWidget):
                tabla.setRowCount(0)
            QMessageBox.warning(self, "Acceso denegado",
                                f"{error.mensaje}\n\nSu rol ya no autoriza esta seccion.")
            return
        QMessageBox.warning(self, "No se pudo completar la operacion", error.mensaje)

    def refrescar(self):
        """Las subclases recargan sus datos."""


class PanelInicio(PanelBase):
    """
    Bienvenida y bandeja de pendientes: lo que el rol del usuario debe atender
    ahora. La API calcula la lista desde el estado de los documentos, de modo
    que un pendiente desaparece en cuanto alguien lo atiende.
    """

    titulo = "Inicio"
    columnas = ["Pendiente", "Detalle", "Donde", "Desde"]

    def __init__(self, cliente: ClienteAPI, secciones: list[str], al_ir_a=None,
                 al_contar=None):
        self.secciones = secciones
        self.al_ir_a = al_ir_a or (lambda nombre, referencia: None)
        self.al_contar = al_contar or (lambda total: None)
        self.items = []
        super().__init__(cliente)

    def construir(self):
        identidad = self.cliente.identidad
        saludo = QLabel(
            f"Sesion iniciada como <b>{identidad.get('username', '')}</b> · "
            f"{', '.join(self.cliente.roles) or 'Sin rol'}"
        )
        self.contenedor.addWidget(saludo)

        grupo = QGroupBox("Mis pendientes")
        capa = QVBoxLayout(grupo)
        self.resumen = QLabel("Cargando...")
        self.resumen.setObjectName("cifra")
        capa.addWidget(self.resumen)
        nota = QLabel(
            "Lo que su rol debe atender ahora. Los marcados en naranja son "
            "prioritarios. Doble clic (o «Ir al panel») abre la seccion donde se "
            "atiende. La lista se actualiza sola cada dos minutos."
        )
        nota.setObjectName("subtitulo")
        nota.setWordWrap(True)
        capa.addWidget(nota)

        self.tabla = self.crear_tabla()
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.Stretch)
        cabecera.setSectionResizeMode(1, QHeaderView.Stretch)
        for columna in (2, 3):
            cabecera.setSectionResizeMode(columna, QHeaderView.ResizeToContents)
        self.tabla.doubleClicked.connect(self.ir_al_panel)
        capa.addWidget(self.tabla, 1)

        self.vacio = QLabel("No tiene pendientes. Todo al dia.")
        self.vacio.setAlignment(Qt.AlignCenter)
        self.vacio.setStyleSheet("color:#2f6b4f; font-size:15px; padding:18px;")
        self.vacio.hide()
        capa.addWidget(self.vacio, 1)

        acciones = QHBoxLayout()
        self.boton_ir = QPushButton("Ir al panel")
        self.boton_ir.clicked.connect(self.ir_al_panel)
        acciones.addWidget(self.boton_ir)
        actualizar = QPushButton("Actualizar")
        actualizar.setObjectName("secundario")
        actualizar.clicked.connect(self.refrescar)
        acciones.addWidget(actualizar)
        acciones.addStretch()
        capa.addLayout(acciones)
        self.contenedor.addWidget(grupo, 1)

        secciones = QLabel(
            "Secciones disponibles: " + (", ".join(self.secciones) or
                                         "ninguna en esta version del escritorio")
        )
        secciones.setObjectName("subtitulo")
        secciones.setWordWrap(True)
        self.contenedor.addWidget(secciones)

    @staticmethod
    def _desde(fecha: str | None) -> str:
        from datetime import datetime

        if not fecha:
            return "Ahora"
        try:
            momento = datetime.fromisoformat(fecha)
        except ValueError:
            return ""
        minutos = int((datetime.now(momento.tzinfo) - momento).total_seconds() // 60)
        if minutos < 60:
            return f"hace {max(minutos, 1)} min"
        if minutos < 60 * 24:
            return f"hace {minutos // 60} h"
        return f"hace {minutos // (60 * 24)} d"

    def refrescar(self, silencioso: bool = False):
        try:
            respuesta = self.cliente.pendientes()
        except ErrorAPI as error:
            self.resumen.setText("No se pudo cargar")
            if not silencioso:
                self.manejar_error(error)
            return
        self.items = respuesta.get("resultados", [])
        total = len(self.items)
        urgentes = sum(1 for i in self.items if i.get("urgente"))
        texto = f"{total} pendiente{'s' if total != 1 else ''}"
        if urgentes:
            texto += f" · {urgentes} prioritario{'s' if urgentes != 1 else ''}"
        self.resumen.setText(texto if total else "Sin pendientes")
        self.llenar(self.tabla, [
            [i["titulo"], i.get("detalle", ""), i["panel"], self._desde(i.get("fecha"))]
            for i in self.items
        ])
        for fila, item in enumerate(self.items):
            if item.get("urgente"):
                for columna in range(self.tabla.columnCount()):
                    celda = self.tabla.item(fila, columna)
                    celda.setBackground(QColor("#fdebd9"))
                    if columna == 0:
                        fuente = celda.font()
                        fuente.setBold(True)
                        celda.setFont(fuente)
        for fila in range(self.tabla.rowCount()):
            self.tabla.item(fila, 0).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tabla.item(fila, 1).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tabla.setVisible(bool(total))
        self.boton_ir.setVisible(bool(total))
        self.vacio.setVisible(not total)
        self.al_contar(total)

    def ir_al_panel(self, *_):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.items):
            QMessageBox.information(self, "Pendientes", "Seleccione un pendiente de la lista.")
            return
        item = self.items[fila]
        self.al_ir_a(item["panel"], item.get("referencia", ""))


class PanelCatalogo(PanelBase):
    """
    Publicacion de modelos en el catalogo web (RF-ADM-06).

    Es el caso mas directo de la regla segun la cual la aplicacion de
    escritorio administra la aplicacion web: al publicar un modelo aqui,
    aparece de inmediato en el catalogo que ve el cliente.
    """

    titulo = "Catalogo de productos"
    subtitulo = ("Cree y edite los modelos del catalogo y controle cuales ve el "
                 "cliente en la web. La publicacion se aplica de inmediato.")
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
        if self.cliente.puede("catalogo.actualizar"):
            self.tabla.doubleClicked.connect(self.editar)
        self.contenedor.addWidget(self.tabla)

        acciones = QHBoxLayout()
        nuevo = QPushButton("Nuevo modelo")
        nuevo.setObjectName("exito")
        nuevo.clicked.connect(self.nuevo)
        nuevo.setVisible(self.cliente.puede("catalogo.crear"))
        acciones.addWidget(nuevo)
        editar = QPushButton("Editar")
        editar.setObjectName("secundario")
        editar.clicked.connect(self.editar)
        editar.setVisible(self.cliente.puede("catalogo.actualizar"))
        acciones.addWidget(editar)
        receta = QPushButton("Materiales y tareas")
        receta.setObjectName("secundario")
        receta.clicked.connect(self.receta)
        receta.setVisible(self.cliente.puede("bom.leer"))
        acciones.addWidget(receta)
        self.boton = QPushButton("Publicar o retirar")
        self.boton.clicked.connect(self.alternar)
        self.boton.setVisible(self.cliente.puede("catalogo.actualizar"))
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

    def receta(self):
        """Lista de materiales y tareas estandar del modelo (RF-CAT-04, 05)."""
        from paneles_maestros import DialogoReceta

        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione un modelo", "Elija una fila de la tabla.")
            return
        try:
            DialogoReceta(self.cliente, self.datos[fila], self).exec()
        except ErrorAPI as error:
            self.manejar_error(error)

    def nuevo(self):
        self._abrir(None)

    def editar(self, *_):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione un modelo", "Elija una fila de la tabla.")
            return
        self._abrir(self.datos[fila]["id_modelo"])

    def _abrir(self, id_modelo):
        from paneles_catalogo import DialogoModelo

        try:
            dialogo = DialogoModelo(self.cliente, id_modelo, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec() and dialogo.resultado:
            self.refrescar()
            if id_modelo:
                QMessageBox.information(self, "Catalogo",
                                        f"Modelo {dialogo.resultado['codigo']} actualizado.")
                return
            # Un modelo nuevo necesita su receta para cotizarse con costo y fabricarse
            if self.cliente.puede("bom.actualizar"):
                from paneles_maestros import DialogoReceta

                QMessageBox.information(
                    self, "Modelo creado",
                    f"Modelo {dialogo.resultado['codigo']} creado. Ahora defina sus materiales "
                    "y tareas: sin tareas no se puede publicar ni fabricar.")
                try:
                    DialogoReceta(self.cliente, dialogo.resultado, self).exec()
                except ErrorAPI as error:
                    self.manejar_error(error)
            else:
                QMessageBox.information(
                    self, "Modelo creado",
                    f"Modelo {dialogo.resultado['codigo']} creado sin publicar.\n\n"
                    "Siguiente paso: el Jefe de produccion define sus materiales y tareas "
                    "(Catalogo > Materiales y tareas). Mientras no tenga tareas, el modelo no "
                    "se puede publicar ni fabricar.")

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
        asignar.setVisible(self.cliente.puede("solicitud.actualizar"))
        acciones.addWidget(asignar)
        cotizar = QPushButton("Elaborar cotizacion")
        cotizar.clicked.connect(self.cotizar)
        cotizar.setVisible(self.cliente.puede("cotizacion.crear"))
        acciones.addWidget(cotizar)
        anular = QPushButton("Desestimar")
        anular.setObjectName("peligro")
        anular.clicked.connect(self.anular)
        anular.setVisible(self.cliente.puede("solicitud.anular"))
        acciones.addWidget(anular)
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


    def anular(self):
        from paneles_comercial import pedir_motivo_y_anular

        fila = self.tabla.currentRow()
        if 0 <= fila < len(self.datos):
            s = self.datos[fila]
            if pedir_motivo_y_anular(self, self.cliente, "solicitudes", s["id_solicitud"],
                                     s["numero"]):
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
        self.puede_operar = self.cliente.puede("canal_web.actualizar")
        guardar.setVisible(self.puede_operar)
        self.mensaje.setReadOnly(not self.puede_operar)
        layout_texto.addWidget(guardar, alignment=Qt.AlignLeft)
        self.contenedor.addWidget(grupo_texto)

        grupo_comercial = QGroupBox("Parametros comerciales y productivos")
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Parametro", "Valor", "Descripcion"])
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.puede_parametrizar = self.cliente.puede("parametro.actualizar")
        if self.puede_parametrizar:
            self.tabla.doubleClicked.connect(self.editar_parametro)
        layout_comercial = QVBoxLayout(grupo_comercial)
        layout_comercial.addWidget(self.tabla)
        editar = QPushButton("Cambiar valor")
        editar.clicked.connect(self.editar_parametro)
        editar.setVisible(self.puede_parametrizar)
        nota = QLabel("Los cambios rigen desde la siguiente operacion: por ejemplo, un nuevo "
                      "porcentaje de anticipo se aplica a las ordenes de compra que se generen "
                      "despues, no a las existentes.")
        nota.setObjectName("subtitulo")
        nota.setWordWrap(True)
        layout_comercial.addWidget(nota)
        layout_comercial.addWidget(editar, alignment=Qt.AlignLeft)
        self.contenedor.addWidget(grupo_comercial, 1)
        self.otros = []

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
            caja.setEnabled(parametro is not None and self.puede_operar)
            caja.blockSignals(False)

        aviso = por_clave.get("web.mensaje_mantencion")
        self.mensaje.setText(aviso["valor"] if aviso else "")

        otros = [
            p for p in parametros
            if p["ambito"] in ("comercial", "produccion", "sistema")
        ]
        self.otros = otros
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

    def editar_parametro(self, *_):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.otros):
            QMessageBox.information(self, "Parametros", "Seleccione un parametro de la tabla.")
            return
        parametro = self.otros[fila]
        valor, aceptado = QInputDialog.getText(
            self, "Cambiar parametro",
            f"{parametro['clave']}\n{parametro.get('descripcion', '')}\n\nNuevo valor:",
            text=parametro["valor"],
        )
        if not aceptado or valor.strip() == parametro["valor"]:
            return
        try:
            self.cliente.actualizar_parametro(parametro["clave"], valor.strip())
        except ErrorAPI as error:
            return self.manejar_error(error)
        QMessageBox.information(
            self, "Parametro actualizado",
            f"{parametro['clave']}: {parametro['valor']} → {valor.strip()}.\n\n"
            "El cambio quedo registrado en la bitacora de auditoria.")
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
