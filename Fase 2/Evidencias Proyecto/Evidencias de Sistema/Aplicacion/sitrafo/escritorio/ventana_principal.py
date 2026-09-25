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
from paneles_produccion import PanelOrdenesTrabajo, VistaTaller
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


class VentanaPrincipal(QMainWindow):
    # Se emite al pulsar "Cerrar sesion"; main.py vuelve a mostrar el ingreso
    sesion_cerrada = Signal()

    def __init__(self, cliente: ClienteAPI):
        super().__init__()
        self.cliente = cliente
        self.setWindowTitle("SITRAFO — Administracion interna")
        self.resize(1180, 740)
        self._construir()

    @property
    def es_vista_taller(self) -> bool:
        """
        El operario usa una vista diferenciada, sin menu (ERS-01, seccion 8.2):
        registra en taller pero no planifica.
        """
        return (self.cliente.puede("taller.crear")
                and not self.cliente.puede("orden_trabajo.actualizar"))

    def _construir(self):
        if self.es_vista_taller:
            return self._construir_taller()
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

        salir = QPushButton("Cerrar sesion")
        salir.setStyleSheet(
            "QPushButton { background: transparent; color: #cfe0f5; border: 1px solid #4a6ea9;"
            " margin: 0 18px 18px 18px; padding: 8px; }"
            "QPushButton:hover { background: #2f5597; color: white; }"
        )
        salir.clicked.connect(self.cerrar_sesion)
        lateral_layout.addWidget(salir)

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
            ("Ordenes de trabajo", "orden_trabajo.leer", PanelOrdenesTrabajo),
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

    def _construir_taller(self):
        self.setWindowTitle("SITRAFO — Taller")
        central = QWidget()
        capa = QVBoxLayout(central)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(0)

        barra = QWidget()
        barra.setStyleSheet("background:#1f3864;")
        capa_barra = QHBoxLayout(barra)
        capa_barra.setContentsMargins(14, 8, 14, 8)
        titulo = QLabel(
            f"SITRAFO · Taller    |    {self.cliente.usuario}"
            f" ({', '.join(self.cliente.roles)})"
        )
        titulo.setStyleSheet("color:white; font-size:18px; font-weight:bold;")
        capa_barra.addWidget(titulo, 1)
        salir = QPushButton("Cerrar sesion")
        salir.setStyleSheet(
            "QPushButton { background: transparent; color: white; border: 1px solid #cfe0f5;"
            " font-size: 16px; padding: 10px 18px; }"
            "QPushButton:hover { background: #2f5597; }"
        )
        salir.clicked.connect(self.cerrar_sesion)
        capa_barra.addWidget(salir)
        capa.addWidget(barra)

        self.taller = VistaTaller(self.cliente)
        capa.addWidget(self.taller, 1)
        self.paneles = [("Taller", self.taller)]
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(f"Conectado a {self.cliente.url_base}")
        self.taller.refrescar()

    def cerrar_sesion(self):
        if QMessageBox.question(self, "Cerrar sesion",
                                "¿Desea cerrar la sesion?") != QMessageBox.Yes:
            return
        # El token JWT se descarta en el cliente; al expirar ya no sirve
        self.cliente.cerrar_sesion()
        self._cerrando_sesion = True
        self.hide()
        self.sesion_cerrada.emit()
        self.close()

    def closeEvent(self, evento):
        """Cerrar la ventana con la X termina la aplicacion; cerrar sesion no."""
        if not getattr(self, "_cerrando_sesion", False):
            QApplication.quit()
        super().closeEvent(evento)

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
