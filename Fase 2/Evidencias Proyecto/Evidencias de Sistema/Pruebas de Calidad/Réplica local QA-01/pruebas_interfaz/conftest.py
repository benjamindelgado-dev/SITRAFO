"""
Configuración de las pruebas de interfaz de SITRAFO con Selenium.

Variables de entorno:
    SITRAFO_URL        URL del sistema (por defecto http://localhost:8000)
    SITRAFO_CLIENTE    usuario del portal (por defecto el de cargar_demo: maipo)
    SITRAFO_CLAVE      clave del usuario del portal
    CHROME_BINARY      ruta a Chrome/Chromium (opcional)
    CHROMEDRIVER       ruta a chromedriver (opcional; si no, Selenium Manager lo resuelve)
    SITRAFO_CAPTURAS   carpeta donde guardar las capturas (por defecto ./capturas)
    HEADLESS           "0" para ver el navegador (por defecto sin ventana)
"""
import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE = os.environ.get("SITRAFO_URL", "http://localhost:8000").rstrip("/")
CLIENTE = os.environ.get("SITRAFO_CLIENTE", "maipo")
CLAVE = os.environ.get("SITRAFO_CLAVE", "ClaveSegura2026")
CAPTURAS = Path(os.environ.get("SITRAFO_CAPTURAS", "capturas"))
CAPTURAS.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def navegador():
    opciones = webdriver.ChromeOptions()
    if os.environ.get("HEADLESS", "1") != "0":
        opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,900")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--lang=es-CL")
    opciones.add_experimental_option("prefs", {"intl.accept_languages": "es-CL,es"})
    # El ambiente local de prueba usa un certificado autofirmado
    opciones.add_argument("--ignore-certificate-errors")
    if os.environ.get("CHROME_BINARY"):
        opciones.binary_location = os.environ["CHROME_BINARY"]
    servicio = Service(os.environ["CHROMEDRIVER"]) if os.environ.get("CHROMEDRIVER") else Service()
    driver = webdriver.Chrome(options=opciones, service=servicio)
    driver.implicitly_wait(2)
    yield driver
    driver.quit()


class Portal:
    """Acciones comunes sobre el portal del cliente."""

    def __init__(self, driver):
        self.d = driver
        self.espera = WebDriverWait(driver, 20)

    def ir(self, ruta):
        self.d.get(f"{BASE}{ruta}")

    def texto(self):
        return self.d.find_element(By.TAG_NAME, "body").text

    def captura(self, nombre):
        self.d.save_screenshot(str(CAPTURAS / f"{nombre}.png"))

    def salir(self):
        self.d.delete_all_cookies()

    def entrar(self, usuario=CLIENTE, clave=CLAVE):
        self.salir()
        self.ir("/acceso/")
        self.d.find_element(By.NAME, "username").send_keys(usuario)
        self.d.find_element(By.NAME, "password").send_keys(clave)
        self.d.find_element(By.CSS_SELECTOR, "form button[type=submit]").click()

    def esperar_url(self, fragmento):
        self.espera.until(EC.url_contains(fragmento))


@pytest.fixture
def portal(navegador):
    return Portal(navegador)
