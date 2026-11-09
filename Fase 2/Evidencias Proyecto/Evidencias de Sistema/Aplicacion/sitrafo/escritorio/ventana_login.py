"""Ventana de acceso a la aplicacion de escritorio."""
import configuracion_local
from cliente_api import ClienteAPI, ErrorAPI
from estilos import recurso
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Tamano del panel con la vista explotada del transformador
ANCHO_IMAGEN, ALTO_VENTANA = 470, 540


class VentanaLogin(QDialog):
    """Autentica contra la API REST y obtiene el token de sesion."""

    def __init__(self, cliente: ClienteAPI):
        super().__init__()
        self.cliente = cliente
        self.setWindowTitle("SITRAFO — Acceso")
        self.setFixedSize(ANCHO_IMAGEN + 430, ALTO_VENTANA)
        self._construir()

    def _construir(self):
        contenedor = QHBoxLayout(self)
        contenedor.setContentsMargins(0, 0, 0, 0)
        contenedor.setSpacing(0)
        contenedor.addWidget(self._panel_imagen())
        contenedor.addWidget(self._panel_formulario(), 1)
        self._mostrar_servidor()

        self.clave.returnPressed.connect(self.ingresar)
        ultimo = configuracion_local.leer().get("usuario")
        if ultimo:
            self.usuario.setText(ultimo)
            self.clave.setFocus()
        else:
            self.usuario.setFocus()

    def _panel_imagen(self) -> QLabel:
        """Vista explotada del transformador, la misma imagen del portal web."""
        imagen = QLabel()
        imagen.setObjectName("imagenLogin")
        imagen.setFixedSize(ANCHO_IMAGEN, ALTO_VENTANA)
        dibujo = QPixmap(recurso("img/login_despiece.jpg"))
        if not dibujo.isNull():
            # Se escala a la densidad de la pantalla para que no se vea borroso
            densidad = QGuiApplication.primaryScreen().devicePixelRatio()
            dibujo = dibujo.scaled(int(ANCHO_IMAGEN * densidad), int(ALTO_VENTANA * densidad),
                                   Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            dibujo.setDevicePixelRatio(densidad)
            imagen.setPixmap(dibujo)

        capa = QVBoxLayout(imagen)
        capa.setContentsMargins(34, 30, 34, 30)
        capa.setSpacing(0)
        marca = QLabel("SITRAFO")
        marca.setObjectName("marcaLogin")
        capa.addWidget(marca)
        capa.addSpacing(10)
        filete = QFrame()
        filete.setObjectName("filete")
        filete.setFixedSize(46, 3)
        capa.addWidget(filete)
        capa.addSpacing(10)
        linea = QLabel("ADMINISTRACION INTERNA")
        linea.setObjectName("lineaLogin")
        capa.addWidget(linea)
        capa.addStretch()
        return imagen

    def _panel_formulario(self) -> QWidget:
        formulario = QWidget()
        formulario.setObjectName("formularioLogin")
        formulario.setAttribute(Qt.WA_StyledBackground, True)
        capa = QVBoxLayout(formulario)
        capa.setContentsMargins(44, 46, 44, 24)
        capa.setSpacing(6)

        titulo = QLabel("Iniciar sesion")
        titulo.setObjectName("tituloLogin")
        capa.addWidget(titulo)
        guia = QLabel("Ingrese con su usuario interno de SITRAFO.")
        guia.setObjectName("subtitulo")
        guia.setWordWrap(True)
        capa.addWidget(guia)
        capa.addSpacing(22)

        etiqueta = QLabel("Usuario")
        etiqueta.setObjectName("etiquetaLogin")
        capa.addWidget(etiqueta)
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText("nombre de acceso")
        capa.addWidget(self.usuario)
        capa.addSpacing(10)

        etiqueta = QLabel("Contrasena")
        etiqueta.setObjectName("etiquetaLogin")
        capa.addWidget(etiqueta)
        self.clave = QLineEdit()
        self.clave.setEchoMode(QLineEdit.Password)
        self.clave.setPlaceholderText("contrasena")
        capa.addWidget(self.clave)
        capa.addSpacing(18)

        self.boton = QPushButton("Ingresar")
        self.boton.setObjectName("botonLogin")
        self.boton.clicked.connect(self.ingresar)
        capa.addWidget(self.boton)

        self.mensaje = QLabel("")
        self.mensaje.setObjectName("mensajeLogin")
        self.mensaje.setAlignment(Qt.AlignCenter)
        self.mensaje.setWordWrap(True)
        capa.addWidget(self.mensaje)
        capa.addStretch()

        self.pie = QLabel("")
        self.pie.setObjectName("pieLogin")
        self.pie.setAlignment(Qt.AlignCenter)
        self.pie.setWordWrap(True)
        capa.addWidget(self.pie)
        cambiar = QPushButton("Cambiar servidor")
        cambiar.setObjectName("secundario")
        cambiar.clicked.connect(self.cambiar_servidor)
        capa.addWidget(cambiar, alignment=Qt.AlignCenter)
        return formulario

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
