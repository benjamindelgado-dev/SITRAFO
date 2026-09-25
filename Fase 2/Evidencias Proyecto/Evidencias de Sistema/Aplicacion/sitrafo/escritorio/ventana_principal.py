"""Ventana principal de la aplicacion de escritorio."""
from cliente_api import ClienteAPI
from paneles import (
    PanelCanalWeb,
    PanelCatalogo,
    PanelClientes,
    PanelInicio,
    PanelIntegraciones,
    PanelSolicitudes,
)
from paneles_comercial import PanelCotizaciones, PanelOrdenesCompra
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


class VentanaPrincipal(QMainWindow):
    def __init__(self, cliente: ClienteAPI):
        super().__init__()
        self.cliente = cliente
        self.setWindowTitle("SITRAFO — Administracion interna")
        self.resize(1180, 740)
        self._construir()

    def _construir(self):
        central = QWidget()
        disposicion = QHBoxLayout(central)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)

        # -- Menu lateral ---------------------------------------------------
        lateral = QWidget()
        lateral.setFixedWidth(230)
        lateral.setStyleSheet("background-color: #1f3864;")
        lateral_layout = QVBoxLayout(lateral)
        lateral_layout.setContentsMargins(0, 0, 0, 0)
        lateral_layout.setSpacing(0)

        marca = QLabel("SITRAFO")
        marca.setAlignment(Qt.AlignCenter)
        marca.setStyleSheet(
            "color: white; font-size: 21px; font-weight: bold; padding: 22px 0;"
        )
        lateral_layout.addWidget(marca)

        self.menu = QListWidget()
        self.menu.setObjectName("menu")
        self.menu.setIconSize(QSize(18, 18))
        lateral_layout.addWidget(self.menu)

        usuario = QLabel(
            f"Sesion: {self.cliente.usuario}\n{', '.join(self.cliente.roles)}"
        )
        usuario.setAlignment(Qt.AlignCenter)
        usuario.setStyleSheet("color: #cfe0f5; padding: 14px; font-size: 12px;")
        usuario.setWordWrap(True)
        lateral_layout.addWidget(usuario)

        disposicion.addWidget(lateral)

        # -- Contenido ------------------------------------------------------
        self.contenido = QStackedWidget()
        disposicion.addWidget(self.contenido, 1)

        # Cada panel se muestra solo si el rol tiene al menos lectura sobre
        # su modulo (matriz de acceso, ERS-01 seccion 8.2)
        disponibles = [
            ("Catalogo", "catalogo.leer", PanelCatalogo),
            ("Clientes", "cliente.leer", PanelClientes),
            ("Solicitudes", "solicitud.leer", PanelSolicitudes),
            ("Cotizaciones", "cotizacion.leer", PanelCotizaciones),
            ("Ordenes de compra", "orden_compra.leer", PanelOrdenesCompra),
            ("Canal web", "canal_web.leer", PanelCanalWeb),
            ("Integraciones", "parametro.leer", PanelIntegraciones),
        ]
        permitidos = [(n, clase) for n, permiso, clase in disponibles
                      if self.cliente.puede(permiso)]
        self.paneles = [("Inicio", PanelInicio(self.cliente, [n for n, _ in permitidos]))]
        self.paneles += [(nombre, clase(self.cliente)) for nombre, clase in permitidos]
        for nombre, panel in self.paneles:
            self.menu.addItem(nombre)
            self.contenido.addWidget(panel)

        self.menu.currentRowChanged.connect(self.cambiar_panel)
        self.setCentralWidget(central)

        barra = QStatusBar()
        barra.showMessage(f"Conectado a {self.cliente.url_base}")
        self.setStatusBar(barra)

        self.menu.setCurrentRow(0)

    def cambiar_panel(self, indice: int):
        if indice < 0:
            return
        self.contenido.setCurrentIndex(indice)
        nombre, panel = self.paneles[indice]
        self.statusBar().showMessage(f"{nombre} — cargando...")
        panel.refrescar()
        self.statusBar().showMessage(
            f"{nombre} — conectado a {self.cliente.url_base}"
        )
