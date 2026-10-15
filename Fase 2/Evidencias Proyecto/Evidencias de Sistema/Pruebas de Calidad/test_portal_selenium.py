# Pruebas de interfaz del portal web de SITRAFO (no crean datos)
import os

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = os.environ.get("SITRAFO_URL", "https://sitrafo.onrender.com").rstrip("/")
USUARIO = os.environ.get("SITRAFO_USUARIO", "")
CLAVE = os.environ.get("SITRAFO_CLAVE", "")
ESPERA = 30  # Render a veces tarda en despertar


@pytest.fixture
def nav():
    if not USUARIO or not CLAVE:
        pytest.fail("Falta definir SITRAFO_USUARIO y SITRAFO_CLAVE")
    opciones = webdriver.ChromeOptions()
    opciones.add_argument("--window-size=1400,900")
    driver = webdriver.Chrome(options=opciones)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def ingresar(nav, usuario, clave):
    nav.get(URL + "/acceso/")
    nav.find_element(By.NAME, "username").send_keys(usuario)
    nav.find_element(By.NAME, "password").send_keys(clave)
    nav.find_element(By.CSS_SELECTOR, "button[type=submit]").click()


def esperar_inicio(nav):
    WebDriverWait(nav, ESPERA).until(EC.title_contains("Inicio"))


def test_pagina_protegida_redirige_al_acceso(nav):
    nav.get(URL + "/catalogo/")
    WebDriverWait(nav, ESPERA).until(EC.url_contains("/acceso/"))
    assert "/acceso/" in nav.current_url


def test_clave_incorrecta_muestra_error(nav):
    # ojo: cuenta como intento fallido para el bloqueo de la cuenta
    ingresar(nav, USUARIO, "clave-incorrecta")
    aviso = WebDriverWait(nav, ESPERA).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".aviso--mal"))
    )
    assert aviso.is_displayed()
    assert "/acceso/" in nav.current_url


def test_ingreso_correcto_muestra_inicio(nav):
    ingresar(nav, USUARIO, CLAVE)
    esperar_inicio(nav)
    assert nav.current_url.rstrip("/") == URL


def test_catalogo_muestra_modelos_y_abre_ficha(nav):
    ingresar(nav, USUARIO, CLAVE)
    esperar_inicio(nav)
    nav.get(URL + "/catalogo/")
    fichas = nav.find_elements(By.XPATH, "//a[normalize-space()='Ficha']")
    assert len(fichas) > 0, "No hay modelos publicados en el catalogo"
    fichas[0].click()
    WebDriverWait(nav, ESPERA).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Descargar ficha tecnica')]"))
    )
    assert "/catalogo/" in nav.current_url


def test_cerrar_sesion(nav):
    ingresar(nav, USUARIO, CLAVE)
    esperar_inicio(nav)
    nav.find_element(By.XPATH, "//button[normalize-space()='Salir']").click()
    WebDriverWait(nav, ESPERA).until(EC.url_contains("/acceso/"))
    assert "/acceso/" in nav.current_url
