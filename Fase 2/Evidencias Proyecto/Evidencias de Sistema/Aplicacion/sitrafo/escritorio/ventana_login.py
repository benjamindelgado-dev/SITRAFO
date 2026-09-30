"""Ventana de acceso a la aplicacion de escritorio."""
import configuracion_local
from cliente_api import ClienteAPI, ErrorAPI
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class VentanaLogin(QDialog):
    """Autentica contra la API REST y obtiene el token de sesion."""

    def __init__(self, cliente: ClienteAPI):
        super().__init__()
        self.cliente = cliente
        self.setWindowTitle("SITRAFO — Acceso")
        self.setFixedSize(420, 370)
        self._construir()

    def _construir(self):
        contenedor = QVBoxLayout(self)
        contenedor.setContentsMargins(36, 30, 36, 30)
        contenedor.setSpacing(6)

        marca = QLabel("SITRAFO")
        marca.setObjectName("marca")
        marca.setAlignment(Qt.AlignCenter)
        contenedor.addWidget(marca)

        subtitulo = QLabel("Administracion interna")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setAlignment(Qt.AlignCenter)
        contenedor.addWidget(subtitulo)
        contenedor.addSpacing(22)

        formulario = QFormLayout()
        formulario.setSpacing(10)
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText("nombre de acceso")
        self.clave = QLineEdit()
        self.clave.setEchoMode(QLineEdit.Password)
        self.clave.setPlaceholderText("contrasena")
        formulario.addRow("Usuario", self.usuario)
        formulario.addRow("Contrasena", self.clave)
        contenedor.addLayout(formulario)
        contenedor.addSpacing(14)

        self.boton = QPushButton("Ingresar")
        self.boton.clicked.connect(self.ingresar)
        contenedor.addWidget(self.boton)

        self.mensaje = QLabel("")
        self.mensaje.setAlignment(Qt.AlignCenter)
        self.mensaje.setWordWrap(True)
        self.mensaje.setStyleSheet("color: #b02a37;")
        contenedor.addWidget(self.mensaje)
        contenedor.addStretch()

        self.pie = QLabel("")
        self.pie.setObjectName("subtitulo")
        self.pie.setAlignment(Qt.AlignCenter)
        self.pie.setWordWrap(True)
        self.pie.setStyleSheet("color: #9aa5b1; font-size: 11px;")
        contenedor.addWidget(self.pie)
        cambiar = QPushButton("Cambiar servidor")
        cambiar.setObjectName("secundario")
        cambiar.clicked.connect(self.cambiar_servidor)
        contenedor.addWidget(cambiar, alignment=Qt.AlignCenter)
        self._mostrar_servidor()

        self.clave.returnPressed.connect(self.ingresar)
        ultimo = configuracion_local.leer().get("usuario")
        if ultimo:
            self.usuario.setText(ultimo)
            self.clave.setFocus()
        else:
            self.usuario.setFocus()

    def _mostrar_servidor(self):
        self.pie.setText(f"Servidor: {self.cliente.url_base}")

    def cambiar_servidor(self):
        texto, ok = QInputDialog.getText(
            self, "Servidor de SITRAFO",
            "Direccion del sistema (por ejemplo sitrafo.onrender.com o localhost:8000):",
            text=self.cliente.url_base.removesuffix("/api/v1"))
        if not ok:
            return
        servidor = configuracion_local.normalizar_servidor(texto)
        if servidor is None:
            QMessageBox.warning(self, "Direccion no valida",
                                "Escriba solo la direccion, sin espacios ni simbolos < >.")
            return
        self.cliente.cambiar_servidor(servidor)
        configuracion_local.guardar(servidor=servidor)
        self._mostrar_servidor()

    def _rechazar(self, motivo: str):
        self.cliente.cerrar_sesion()
        QMessageBox.warning(self, "Acceso denegado", motivo)
        self.boton.setEnabled(True)
        self.boton.setText("Ingresar")

    def ingresar(self):
        usuario = self.usuario.text().strip()
        clave = self.clave.text()

        if not usuario or not clave:
            self.mensaje.setText("Ingrese usuario y contrasena.")
            return

        self.boton.setEnabled(False)
        self.boton.setText("Conectando...")
        self.mensaje.setText("")

        try:
            self.cliente.autenticar(usuario, clave)
        except ErrorAPI as error:
            self.mensaje.setText(error.mensaje)
            self.boton.setEnabled(True)
            self.boton.setText("Ingresar")
            return

        # La aplicacion de escritorio es exclusiva de usuarios internos con
        # rol asignado: sin rol el acceso se deniega por defecto (RN-18)
        try:
            identidad = self.cliente.cargar_identidad()
        except ErrorAPI as error:
            return self._rechazar(error.mensaje)

        if not identidad.get("es_interno"):
            return self._rechazar(
                "Esta cuenta es de cliente. Las cuentas de cliente deben usar "
                "el portal web."
            )
        if not identidad.get("es_superusuario") and not identidad.get("permisos"):
            return self._rechazar(
                "Su usuario no tiene un rol asignado. Solicite al administrador "
                "que le asigne uno."
            )

        # Se recuerdan el servidor y el usuario (nunca la contrasena)
        configuracion_local.guardar(servidor=self.cliente.url_base, usuario=usuario)
        self.accept()
