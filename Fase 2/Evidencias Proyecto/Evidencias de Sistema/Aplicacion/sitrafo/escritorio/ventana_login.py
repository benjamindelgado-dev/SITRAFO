"""Ventana de acceso a la aplicacion de escritorio."""
from cliente_api import ClienteAPI, ErrorAPI
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
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
        self.setFixedSize(420, 340)
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

        pie = QLabel(f"Servidor: {self.cliente.url_base}")
        pie.setObjectName("subtitulo")
        pie.setAlignment(Qt.AlignCenter)
        pie.setStyleSheet("color: #9aa5b1; font-size: 11px;")
        contenedor.addWidget(pie)

        self.clave.returnPressed.connect(self.ingresar)
        self.usuario.setFocus()

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

        self.accept()
