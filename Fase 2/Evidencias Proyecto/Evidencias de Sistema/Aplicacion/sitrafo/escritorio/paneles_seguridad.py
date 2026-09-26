"""
Administracion de usuarios internos (CU-SEG-02, CU-SEG-03).

Exclusivo del Administrador segun la matriz de acceso. Permite crear
usuarios, asignarles roles, asociarlos a un empleado del taller, suspender
o reactivar la cuenta y restablecer su clave. Las reglas (al menos un rol,
no autoexcluirse, empleado unico) las aplica la API.
"""
from cliente_api import ClienteAPI, ErrorAPI
from paneles import PanelBase
from paneles_comercial import fecha
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


def mostrar_clave(padre, usuario: str, clave: str):
    """La clave temporal se muestra una sola vez; se ofrece copiarla."""
    caja = QMessageBox(padre)
    caja.setWindowTitle("Clave temporal")
    caja.setText(
        f"Clave temporal de <b>{usuario}</b>:<br><br>"
        f"<span style='font-size:18px; font-family:monospace'>{clave}</span><br><br>"
        "Entreguela al usuario por un medio seguro. No volvera a mostrarse."
    )
    copiar = caja.addButton("Copiar y cerrar", QMessageBox.AcceptRole)
    caja.addButton("Cerrar", QMessageBox.RejectRole)
    caja.exec()
    if caja.clickedButton() is copiar:
        QApplication.clipboard().setText(clave)


class DialogoUsuario(QDialog):
    def __init__(self, cliente: ClienteAPI, usuario: dict | None = None, parent=None):
        super().__init__(parent)
        self.cliente = cliente
        self.usuario = usuario
        self.resultado = None
        self.roles = cliente.roles_disponibles()
        self.empleados = cliente.empleados()
        self.setWindowTitle("Editar usuario" if usuario else "Nuevo usuario interno")
        self.setMinimumWidth(480)
        self._construir()

    def _construir(self):
        capa = QVBoxLayout(self)
        datos = QGroupBox("Cuenta")
        formulario = QFormLayout(datos)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Ej.: mdiaz")
        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@empresa.cl")
        formulario.addRow("Usuario:", self.username)
        formulario.addRow("Correo:", self.email)
        if self.usuario is None:
            self.clave = QLineEdit()
            self.clave.setEchoMode(QLineEdit.Password)
            self.clave.setPlaceholderText("Dejar vacio para generar una temporal")
            formulario.addRow("Clave:", self.clave)
        capa.addWidget(datos)

        grupo_roles = QGroupBox("Roles (al menos uno)")
        gr = QVBoxLayout(grupo_roles)
        self.casillas = []
        for rol in self.roles:
            casilla = QCheckBox(rol["nombre"])
            casilla.setToolTip(rol["descripcion"])
            nota = QLabel(rol["descripcion"])
            nota.setObjectName("nota")
            nota.setWordWrap(True)
            gr.addWidget(casilla)
            gr.addWidget(nota)
            self.casillas.append((rol, casilla))
        capa.addWidget(grupo_roles)

        grupo_empleado = QGroupBox("Empleado del taller")
        ge = QVBoxLayout(grupo_empleado)
        self.empleado = QComboBox()
        self.empleado.addItem("Ninguno (no registra horas en taller)", None)
        propio = (self.usuario or {}).get("empleado") or {}
        for e in self.empleados:
            ocupado = e.get("username") and e["id_empleado"] != propio.get("id_empleado")
            texto = f"{e['nombre']} ({e['cargo']})" + (f" — usuario {e['username']}"
                                                         if ocupado else "")
            self.empleado.addItem(texto, e["id_empleado"])
            if ocupado:
                self.empleado.model().item(self.empleado.count() - 1).setEnabled(False)
        nota = QLabel("Solo para operarios: vincula la cuenta con el empleado cuyas horas "
                      "y tarifa se registran.")
        nota.setObjectName("nota")
        nota.setWordWrap(True)
        ge.addWidget(self.empleado)
        ge.addWidget(nota)
        capa.addWidget(grupo_empleado)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Save).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.button(QDialogButtonBox.Cancel).setObjectName("secundario")
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)

        if self.usuario:
            u = self.usuario
            self.username.setText(u["username"])
            self.username.setEnabled(False)
            self.email.setText(u["email"])
            asignados = {r["id_rol"] for r in u["roles"]}
            for rol, casilla in self.casillas:
                casilla.setChecked(rol["id_rol"] in asignados)
            if propio:
                self.empleado.setCurrentIndex(self.empleado.findData(propio["id_empleado"]))

    def _guardar(self):
        roles = [rol["id_rol"] for rol, casilla in self.casillas if casilla.isChecked()]
        if not roles:
            QMessageBox.warning(self, "Falta el rol", "Marque al menos un rol.")
            return
        datos = {"email": self.email.text().strip(), "roles": roles,
                 "empleado": self.empleado.currentData()}
        try:
            if self.usuario:
                self.resultado = self.cliente.actualizar_usuario(
                    self.usuario["id_usuario"], datos)
            else:
                datos["username"] = self.username.text().strip()
                if self.clave.text():
                    datos["clave"] = self.clave.text()
                self.resultado = self.cliente.crear_usuario(datos)
        except ErrorAPI as error:
            QMessageBox.warning(self, "No se pudo guardar", error.mensaje)
            return
        self.accept()


class PanelUsuarios(PanelBase):
    titulo = "Usuarios y roles"
    subtitulo = ("Cree las cuentas del personal interno y asigne su rol. Cada rol "
                 "determina que paneles y acciones ve el usuario.")
    columnas = ["Usuario", "Correo", "Roles", "Empleado", "Estado", "Ultimo acceso"]

    def construir(self):
        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._seleccion)
        self.tabla.doubleClicked.connect(self._editar)
        self.contenedor.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        self.b_nuevo = QPushButton("Nuevo usuario")
        self.b_nuevo.setObjectName("exito")
        self.b_nuevo.clicked.connect(self._nuevo)
        self.b_editar = QPushButton("Editar roles y datos")
        self.b_editar.setObjectName("secundario")
        self.b_editar.clicked.connect(self._editar)
        self.b_estado = QPushButton("Suspender")
        self.b_estado.setObjectName("peligro")
        self.b_estado.clicked.connect(self._cambiar_estado)
        self.b_clave = QPushButton("Restablecer clave")
        self.b_clave.setObjectName("secundario")
        self.b_clave.clicked.connect(self._restablecer)
        for boton in (self.b_nuevo, self.b_editar, self.b_estado, self.b_clave):
            acciones.addWidget(boton)
        acciones.addStretch()
        recargar = QPushButton("Recargar")
        recargar.setObjectName("secundario")
        recargar.clicked.connect(self.refrescar)
        acciones.addWidget(recargar)
        self.contenedor.addLayout(acciones)

        self.b_nuevo.setVisible(self.cliente.puede("usuario.crear"))
        for boton in (self.b_editar, self.b_estado, self.b_clave):
            boton.setVisible(self.cliente.puede("usuario.actualizar"))
        self.datos = []
        self._seleccion()

    def refrescar(self):
        try:
            self.datos = self.cliente.usuarios()
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.llenar(self.tabla, [
            [u["username"] + (" (superusuario)" if u["es_superusuario"] else ""),
             u["email"], ", ".join(r["nombre"] for r in u["roles"]) or "sin rol",
             (u["empleado"] or {}).get("nombre", "—"), u["estado_nombre"],
             fecha(u["ultimo_acceso"]) if u["ultimo_acceso"] else "nunca"]
            for u in self.datos
        ])
        self._seleccion()

    def _actual(self):
        fila = self.tabla.currentRow()
        return self.datos[fila] if 0 <= fila < len(getattr(self, "datos", [])) else None

    def _seleccion(self):
        u = self._actual()
        for boton in (self.b_editar, self.b_estado, self.b_clave):
            boton.setEnabled(u is not None)
        if u:
            activo = u["estado"] == "activo"
            self.b_estado.setText("Suspender" if activo else "Reactivar")
            self.b_estado.setObjectName("peligro" if activo else "exito")
            self.b_estado.style().unpolish(self.b_estado)
            self.b_estado.style().polish(self.b_estado)

    def _abrir(self, usuario):
        try:
            dialogo = DialogoUsuario(self.cliente, usuario, self)
        except ErrorAPI as error:
            return self.manejar_error(error)
        if dialogo.exec() and dialogo.resultado:
            if dialogo.resultado.get("clave_temporal"):
                mostrar_clave(self, dialogo.resultado["username"],
                              dialogo.resultado["clave_temporal"])
            self.refrescar()

    def _nuevo(self):
        self._abrir(None)

    def _editar(self, *_):
        if self._actual():
            self._abrir(self._actual())

    def _cambiar_estado(self):
        u = self._actual()
        activo = u["estado"] == "activo"
        pregunta = (f"¿Suspender la cuenta de {u['username']}? No podra ingresar."
                    if activo else f"¿Reactivar la cuenta de {u['username']}?")
        if QMessageBox.question(self, "Confirmar", pregunta) != QMessageBox.Yes:
            return
        try:
            if activo:
                self.cliente.suspender_usuario(u["id_usuario"])
            else:
                self.cliente.reactivar_usuario(u["id_usuario"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.refrescar()

    def _restablecer(self):
        u = self._actual()
        if QMessageBox.question(
            self, "Restablecer clave",
            f"Se generara una clave temporal nueva para {u['username']}. ¿Continuar?",
        ) != QMessageBox.Yes:
            return
        try:
            respuesta = self.cliente.restablecer_clave(u["id_usuario"])
        except ErrorAPI as error:
            return self.manejar_error(error)
        mostrar_clave(self, u["username"], respuesta["clave_temporal"])


# ---------------------------------------------------------------------------
# Bitacora de auditoria (HU-12, RF-SEG-06)
# ---------------------------------------------------------------------------
class PanelAuditoria(PanelBase):
    titulo = "Bitacora de auditoria"
    subtitulo = ("Quien hizo que y cuando: cambios de precios y estados, usuarios, "
                 "anulaciones y accesos denegados. Es de solo lectura.")
    columnas = ["Fecha y hora", "Usuario", "Accion", "Entidad", "Registro", "Origen"]

    ACCIONES = [("Todas", ""), ("Creacion", "creacion"), ("Modificacion", "modificacion"),
                ("Anulacion", "anulacion"), ("Acceso denegado", "acceso_denegado")]

    def construir(self):
        filtros = QHBoxLayout()
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText("Usuario")
        self.accion = QComboBox()
        for nombre, codigo in self.ACCIONES:
            self.accion.addItem(nombre, codigo)
        self.entidad = QComboBox()
        self.entidad.addItem("Todas las entidades", "")
        self.desde = QDateEdit(QDate.currentDate().addDays(-30))
        self.desde.setCalendarPopup(True)
        self.desde.setDisplayFormat("dd-MM-yyyy")
        self.hasta = QDateEdit(QDate.currentDate())
        self.hasta.setCalendarPopup(True)
        self.hasta.setDisplayFormat("dd-MM-yyyy")
        buscar = QPushButton("Filtrar")
        buscar.clicked.connect(self.refrescar)
        for etiqueta, widget in (("", self.usuario), ("", self.accion), ("", self.entidad),
                                 ("Desde", self.desde), ("Hasta", self.hasta)):
            if etiqueta:
                filtros.addWidget(QLabel(etiqueta))
            filtros.addWidget(widget)
        filtros.addWidget(buscar)
        self.contenedor.addLayout(filtros)

        self.tabla = self.crear_tabla()
        self.tabla.itemSelectionChanged.connect(self._detalle)
        self.contenedor.addWidget(self.tabla, 1)
        self.detalle = QLabel("Seleccione un registro para ver el cambio.")
        self.detalle.setWordWrap(True)
        self.detalle.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.contenedor.addWidget(self.detalle)
        self.total = QLabel("")
        self.total.setObjectName("nota")
        self.contenedor.addWidget(self.total)
        self.datos = []
        self._entidades_cargadas = False

    def refrescar(self):
        try:
            if not self._entidades_cargadas:
                for entidad in self.cliente.entidades_auditadas():
                    self.entidad.addItem(entidad, entidad)
                self._entidades_cargadas = True
            respuesta = self.cliente.auditoria({
                "usuario": self.usuario.text().strip() or None,
                "accion": self.accion.currentData() or None,
                "entidad": self.entidad.currentData() or None,
                "desde": self.desde.date().toString("yyyy-MM-dd"),
                "hasta": self.hasta.date().toString("yyyy-MM-dd"),
                "page_size": 200,
            })
        except ErrorAPI as error:
            return self.manejar_error(error)
        self.datos = respuesta.get("results", respuesta)
        cantidad = respuesta.get("count", len(self.datos))
        self.total.setText(f"{cantidad} registro(s)"
                           + (" · se muestran los mas recientes" if cantidad > len(self.datos)
                              else ""))
        self.llenar(self.tabla, [
            [fecha(r["fecha_hora"]) + " " + r["fecha_hora"][11:19], r["usuario_nombre"],
             r["accion_nombre"], r["entidad"], r["id_registro"], r["origen_nombre"]]
            for r in self.datos
        ])
        self._detalle()

    @staticmethod
    def _valor(valor) -> str:
        if not valor:
            return "—"
        if isinstance(valor, dict):
            return "<br>".join(f"&nbsp;&nbsp;{k}: <b>{v}</b>" for k, v in valor.items())
        return str(valor)

    def _detalle(self):
        fila = self.tabla.currentRow()
        if not 0 <= fila < len(self.datos):
            self.detalle.setText("Seleccione un registro para ver el cambio.")
            return
        r = self.datos[fila]
        self.detalle.setText(
            f"<b>{r['accion_nombre']}</b> sobre {r['entidad']} #{r['id_registro']} por "
            f"{r['usuario_nombre']}<br><br>Antes:<br>{self._valor(r['valor_anterior'])}"
            f"<br>Despues:<br>{self._valor(r['valor_nuevo'])}"
        )
