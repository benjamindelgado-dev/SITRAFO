"""
Gestion de clientes desde el escritorio (RF-CLI-01, 03, 04, 07, RF-ADM-03).

El ejecutivo comercial crea y edita clientes, sus contactos y direcciones,
revisa el historial completo de documentos y administra las cuentas web.
El RUT se valida en el backend (digito verificador y duplicados).
"""
from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import clp, fecha, uf
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def _lista(respuesta):
    return respuesta.get("results", respuesta) if isinstance(respuesta, dict) else respuesta


def _tabla(columnas, filas) -> QTableWidget:
    tabla = QTableWidget(len(filas), len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(QTableWidget.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            tabla.setItem(i, j, QTableWidgetItem(str(valor)))
    return tabla


def _formulario(dialogo, titulo, campos, aceptar="Guardar"):
    """Dialogo simple: campos = [(etiqueta, widget)]."""
    dialogo.setWindowTitle(titulo)
    dialogo.setMinimumWidth(440)
    capa = QFormLayout(dialogo)
    for etiqueta, widget in campos:
        capa.addRow(etiqueta, widget)
    botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    botones.button(QDialogButtonBox.Ok).setText(aceptar)
    botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
    botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
    botones.rejected.connect(dialogo.reject)
    capa.addRow(botones)
    return botones


class DialogoCliente(QDialog):
    def __init__(self, cliente_api: ClienteAPI, cliente: dict | None = None, parent=None):
        super().__init__(parent)
        self.api, self.cliente = cliente_api, cliente
        self.rut = QLineEdit()
        self.rut.setPlaceholderText("76.543.210-3")
        self.razon = QLineEdit()
        self.fantasia = QLineEdit()
        self.tipo = QComboBox()
        self.tipo.addItem("Persona juridica", "juridica")
        self.tipo.addItem("Persona natural", "natural")
        self.giro = QLineEdit()
        self.activo = QCheckBox("Activo")
        self.activo.setChecked(True)
        botones = _formulario(self, "Editar cliente" if cliente else "Nuevo cliente", [
            ("RUT:", self.rut), ("Razon social:", self.razon),
            ("Nombre de fantasia:", self.fantasia), ("Tipo:", self.tipo),
            ("Giro:", self.giro), ("", self.activo)])
        botones.accepted.connect(self._guardar)
        if cliente:
            self.rut.setText(cliente["rut"])
            self.rut.setEnabled(False)
            self.razon.setText(cliente["razon_social"])
            self.fantasia.setText(cliente.get("nombre_fantasia") or "")
            self.tipo.setCurrentIndex(self.tipo.findData(cliente["tipo_persona"]))
            self.giro.setText(cliente.get("giro") or "")
            self.activo.setChecked(cliente["estado"] == "activo")

    def _guardar(self):
        datos = {"razon_social": self.razon.text().strip(),
                 "nombre_fantasia": self.fantasia.text().strip(),
                 "tipo_persona": self.tipo.currentData(), "giro": self.giro.text().strip(),
                 "estado": "activo" if self.activo.isChecked() else "inactivo"}
        try:
            if self.cliente:
                self.api.actualizar_cliente(self.cliente["id_cliente"], datos)
            else:
                self.api.crear_cliente({**datos, "rut": self.rut.text().strip()})
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class DialogoContacto(QDialog):
    def __init__(self, api: ClienteAPI, id_cliente: int, parent=None, contacto=None):
        super().__init__(parent)
        self.api, self.id_cliente, self.contacto = api, id_cliente, contacto
        self.nombre, self.cargo = QLineEdit(), QLineEdit()
        self.email, self.telefono = QLineEdit(), QLineEdit()
        self.principal = QCheckBox("Contacto principal (recibe los correos del sistema)")
        if contacto:
            self.nombre.setText(contacto["nombre"])
            self.cargo.setText(contacto.get("cargo", ""))
            self.email.setText(contacto.get("email", ""))
            self.telefono.setText(contacto.get("telefono", ""))
            self.principal.setChecked(bool(contacto.get("principal")))
        _formulario(self, "Editar contacto" if contacto else "Nuevo contacto", [
            ("Nombre:", self.nombre), ("Cargo:", self.cargo), ("Correo:", self.email),
            ("Telefono:", self.telefono), ("", self.principal)]).accepted.connect(self._guardar)

    def _guardar(self):
        datos = {"cliente": self.id_cliente, "nombre": self.nombre.text().strip(),
                 "cargo": self.cargo.text().strip(), "email": self.email.text().strip(),
                 "telefono": self.telefono.text().strip(),
                 "principal": self.principal.isChecked()}
        try:
            if self.contacto:
                self.api.actualizar_contacto(self.contacto["id_contacto"], datos)
            else:
                self.api.crear_contacto(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class DialogoDireccion(QDialog):
    def __init__(self, api: ClienteAPI, id_cliente: int, parent=None, direccion=None):
        super().__init__(parent)
        self.api, self.id_cliente, self.direccion = api, id_cliente, direccion
        self.tipo = QComboBox()
        for codigo, nombre in (("despacho", "Despacho"), ("instalacion", "Instalacion"),
                               ("facturacion", "Facturacion")):
            self.tipo.addItem(nombre, codigo)
        self.comuna = QComboBox()
        self.comuna.setEditable(True)
        for c in _lista(api.comunas()):
            self.comuna.addItem(f"{c['nombre']} ({c['region_nombre']})", c["id_comuna"])
        self.calle, self.numero = QLineEdit(), QLineEdit()
        if direccion:
            self.tipo.setCurrentIndex(max(0, self.tipo.findData(direccion["tipo"])))
            self.comuna.setCurrentIndex(max(0, self.comuna.findData(direccion["comuna"])))
            self.calle.setText(direccion.get("calle", ""))
            self.numero.setText(direccion.get("numero", ""))
        _formulario(self, "Editar direccion" if direccion else "Nueva direccion", [
            ("Tipo:", self.tipo), ("Comuna:", self.comuna), ("Calle:", self.calle),
            ("Numero:", self.numero)]).accepted.connect(self._guardar)

    def _guardar(self):
        datos = {"cliente": self.id_cliente, "tipo": self.tipo.currentData(),
                 "comuna": self.comuna.currentData(),
                 "calle": self.calle.text().strip(), "numero": self.numero.text().strip()}
        try:
            if self.direccion:
                self.api.actualizar_direccion(self.direccion["id_direccion"], datos)
            else:
                self.api.crear_direccion(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class DialogoFichaCliente(QDialog):
    """Contactos, direcciones, historial de documentos y cuentas web."""

    def __init__(self, api: ClienteAPI, cliente: dict, parent=None):
        super().__init__(parent)
        self.api, self.cliente = api, cliente
        self.setWindowTitle(f"{cliente['razon_social']} — RUT {cliente['rut']}")
        self.resize(900, 560)
        capa = QVBoxLayout(self)
        self.pestanas = QTabWidget()
        capa.addWidget(self.pestanas, 1)
        cerrar = QPushButton("Cerrar")
        cerrar.setObjectName("secundario")
        cerrar.clicked.connect(self.accept)
        pie = QHBoxLayout()
        pie.addStretch()
        pie.addWidget(cerrar)
        capa.addLayout(pie)
        self._cargar()

    def _cargar(self):
        self.pestanas.clear()
        cliente = self.api.obtener(f"clientes/{self.cliente['id_cliente']}/")
        docs = self.api.documentos_cliente(self.cliente["id_cliente"])
        puede_editar = self.api.puede("cliente.actualizar")

        # Contactos y direcciones (RF-CLI-03, RF-CLI-04)
        puede_eliminar = self.api.puede("cliente.anular")
        self.registros = {}
        for titulo, registros, filas, columnas, dialogo in (
            ("Contactos", cliente["contactos"],
             [[c["nombre"], c["cargo"], c["email"], c["telefono"],
               "Si" if c["principal"] else ""] for c in cliente["contactos"]],
             ["Nombre", "Cargo", "Correo", "Telefono", "Principal"], DialogoContacto),
            ("Direcciones", cliente["direcciones"],
             [[d["tipo"].capitalize(), d["direccion_completa"],
               "Si" if d.get("validada") else "No"] for d in cliente["direcciones"]],
             ["Tipo", "Direccion", "Geocodificada"], DialogoDireccion),
        ):
            contenedor = QVBoxLayout()
            widget = _tabla(columnas, filas)
            self.registros[titulo] = (widget, registros, dialogo)
            if puede_editar:
                widget.doubleClicked.connect(lambda _=None, t=titulo: self._editar(t))
            fila = QHBoxLayout()
            singular = {"Contactos": "contacto", "Direcciones": "direccion"}[titulo]
            for texto, accion, visible, estilo in (
                (f"Agregar {singular}", lambda _=False, d=dialogo: self._agregar(d),
                 puede_editar, ""),
                ("Editar", lambda _=False, t=titulo: self._editar(t), puede_editar, "secundario"),
                ("Eliminar", lambda _=False, t=titulo: self._eliminar(t), puede_eliminar,
                 "peligro"),
            ):
                boton = QPushButton(texto)
                if estilo:
                    boton.setObjectName(estilo)
                boton.setVisible(visible)
                boton.clicked.connect(accion)
                fila.addWidget(boton)
            fila.addStretch()
            envoltura = QWidget()
            envoltura.setLayout(contenedor)
            contenedor.addWidget(widget)
            contenedor.addLayout(fila)
            self.pestanas.addTab(envoltura, f"{titulo} ({len(filas)})")

        # Historial (RF-CLI-07)
        historial = QTabWidget()
        historial.addTab(_tabla(["Numero", "Fecha", "Unidades", "Estado"], [
            [s["numero"], fecha(s["creado_en"]), s["cantidad"], s["estado"]]
            for s in docs["solicitudes"]]), f"Solicitudes ({len(docs['solicitudes'])})")
        historial.addTab(_tabla(["Numero", "Fecha", "Total", "Vence", "Estado"], [
            [c["numero"], fecha(c["creado_en"]), uf(c["total_uf"]), fecha(c["vence_el"]),
             c["estado"]] for c in docs["cotizaciones"]]),
            f"Cotizaciones ({len(docs['cotizaciones'])})")
        historial.addTab(_tabla(["Numero", "Fecha", "Total", "Estado"], [
            [o["numero"], fecha(o["creado_en"]), uf(o["total_uf"]), o["estado"]]
            for o in docs["ordenes_compra"]]), f"Ordenes ({len(docs['ordenes_compra'])})")
        historial.addTab(_tabla(["Numero", "Tipo", "Monto", "Estado", "Fecha"], [
            [d["numero"], d["tipo"], clp(d["monto_clp"]), d["estado"], fecha(d["creado_en"])]
            for d in docs["cobros"]]), f"Cobros ({len(docs['cobros'])})")
        self.pestanas.addTab(historial, "Historial de documentos")

        # Cuentas web (RF-ADM-03)
        if self.api.puede("cuenta_web.leer"):
            cuentas = self.api.cuentas_cliente(self.cliente["id_cliente"])
            contenedor = QVBoxLayout()
            self.tabla_cuentas = _tabla(["Usuario", "Correo", "Estado", "Ultimo acceso"], [
                [c["username"], c["email"], c["estado_nombre"],
                 fecha(c["ultimo_acceso"]) if c["ultimo_acceso"] else "nunca"] for c in cuentas])
            self.cuentas = cuentas
            contenedor.addWidget(self.tabla_cuentas)
            fila = QHBoxLayout()
            for texto, suspender in (("Suspender cuenta", True), ("Reactivar cuenta", False)):
                boton = QPushButton(texto)
                boton.setObjectName("peligro" if suspender else "exito")
                boton.setVisible(self.api.puede("cuenta_web.actualizar"))
                boton.clicked.connect(lambda _=False, s=suspender: self._estado_cuenta(s))
                fila.addWidget(boton)
            fila.addStretch()
            contenedor.addLayout(fila)
            nota = QLabel("Una cuenta suspendida no puede ingresar a la web y pierde su "
                          "sesion abierta de inmediato.")
            nota.setObjectName("nota")
            contenedor.addWidget(nota)
            envoltura = QWidget()
            envoltura.setLayout(contenedor)
            self.pestanas.addTab(envoltura, f"Cuentas web ({len(cuentas)})")

    def _agregar(self, clase):
        if clase(self.api, self.cliente["id_cliente"], self).exec():
            self._recargar(0 if clase is DialogoContacto else 1)

    def _seleccion(self, titulo):
        tabla, registros, dialogo = self.registros[titulo]
        fila = tabla.currentRow()
        if not 0 <= fila < len(registros):
            QMessageBox.information(self, titulo, f"Seleccione un registro de {titulo.lower()}.")
            return None, dialogo
        return registros[fila], dialogo

    def _recargar(self, pestana):
        self._cargar()
        self.pestanas.setCurrentIndex(pestana)

    def _editar(self, titulo):
        registro, dialogo = self._seleccion(titulo)
        if registro is None:
            return
        clave = "contacto" if dialogo is DialogoContacto else "direccion"
        if dialogo(self.api, self.cliente["id_cliente"], self, **{clave: registro}).exec():
            self._recargar(0 if titulo == "Contactos" else 1)

    def _eliminar(self, titulo):
        registro, dialogo = self._seleccion(titulo)
        if registro is None:
            return
        es_contacto = dialogo is DialogoContacto
        descripcion = registro["nombre"] if es_contacto else registro["direccion_completa"]
        if QMessageBox.question(self, f"Eliminar {'contacto' if es_contacto else 'direccion'}",
                                f"¿Eliminar «{descripcion}»?") != QMessageBox.Yes:
            return
        try:
            if es_contacto:
                self.api.eliminar_contacto(registro["id_contacto"])
            else:
                self.api.eliminar_direccion(registro["id_direccion"])
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo eliminar", error.mensaje)
            return
        self._recargar(0 if es_contacto else 1)

    def _estado_cuenta(self, suspender: bool):
        fila = self.tabla_cuentas.currentRow()
        if not 0 <= fila < len(self.cuentas):
            QMessageBox.information(self, "Cuentas web", "Seleccione una cuenta.")
            return
        try:
            self.api.estado_cuenta_cliente(self.cliente["id_cliente"],
                                           self.cuentas[fila]["id_usuario"], suspender)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo cambiar", error.mensaje)
            return
        self._cargar()
        self.pestanas.setCurrentIndex(self.pestanas.count() - 1)


class PanelClientes(PanelBase):
    titulo = "Clientes"
    subtitulo = ("Gestione clientes, contactos y direcciones; revise su historial de "
                 "documentos y administre sus cuentas web.")
    columnas = ["RUT", "Razon social", "Tipo", "Estado", "Contactos", "Direcciones"]

    def construir(self):
        barra = QHBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Buscar por RUT o razon social")
        self.busqueda.returnPressed.connect(self.refrescar)
        barra.addWidget(self.busqueda, 1)
        buscar = QPushButton("Buscar")
        buscar.setObjectName("secundario")
        buscar.clicked.connect(self.refrescar)
        barra.addWidget(buscar)
        self.contenedor.addLayout(barra)

        self.tabla = self.crear_tabla()
        self.tabla.doubleClicked.connect(self._ficha)
        self.contenedor.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        nuevo = QPushButton("Nuevo cliente")
        nuevo.setObjectName("exito")
        nuevo.clicked.connect(lambda: self._editar(None))
        nuevo.setVisible(self.cliente.puede("cliente.crear"))
        editar = QPushButton("Editar")
        editar.setObjectName("secundario")
        editar.clicked.connect(self._editar_actual)
        editar.setVisible(self.cliente.puede("cliente.actualizar"))
        ficha = QPushButton("Ficha e historial")
        ficha.clicked.connect(self._ficha)
        for boton in (nuevo, editar, ficha):
            acciones.addWidget(boton)
        acciones.addStretch()
        self.contenedor.addLayout(acciones)
        self.datos = []

    def refrescar(self):
        params = {"search": self.busqueda.text().strip()} if self.busqueda.text().strip() else None
        try:
            self.datos = _lista(self.cliente.clientes(params))
        except ErrorAPI as error:
            return self.manejar_error(error)
        tipos = {"juridica": "Juridica", "natural": "Natural"}
        self.llenar(self.tabla, [
            [c["rut"], c["razon_social"], tipos.get(c["tipo_persona"], c["tipo_persona"]),
             c["estado"].capitalize(), len(c.get("contactos", [])),
             len(c.get("direcciones", []))] for c in self.datos])

    def _actual(self):
        fila = self.tabla.currentRow()
        return self.datos[fila] if 0 <= fila < len(self.datos) else None

    def _editar_actual(self):
        if self._actual() is None:
            QMessageBox.information(self, "Clientes", "Seleccione un cliente.")
            return
        self._editar(self._actual())

    def _editar(self, cliente):
        if DialogoCliente(self.cliente, cliente, self).exec():
            self.refrescar()

    def _ficha(self, *_):
        actual = self._actual()
        if actual is None:
            QMessageBox.information(self, "Clientes", "Seleccione un cliente.")
            return
        try:
            DialogoFichaCliente(self.cliente, actual, self).exec()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.refrescar()
