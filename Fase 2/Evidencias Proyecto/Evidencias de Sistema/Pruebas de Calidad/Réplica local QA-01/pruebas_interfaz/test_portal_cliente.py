"""
Pruebas automatizadas de interfaz del portal del cliente de SITRAFO (Selenium).

Recorren el flujo de extremo a extremo con la cuenta de demostración
(cargar_demo): acceso, catálogo, solicitud de presupuesto, respuesta a la
cotización, orden de compra, documento de cobro y seguimiento.

Las pruebas se ejecutan en orden y comparten el navegador. Requieren una base
recién cargada con los comandos de demostración del README (pasos 6 a 11),
porque la prueba de aceptación consume la cotización emitida COT-2026-0001.

Ejecución:
    pip install selenium pytest
    pytest pruebas_interfaz -v
"""
import re

import requests
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from conftest import BASE


# ---------------------------------------------------------------- acceso
def test_01_pagina_protegida_redirige_al_acceso(portal):
    """Sin sesión, una página del cliente redirige al formulario de acceso (RF-SEG)."""
    portal.salir()
    portal.ir("/mis-pedidos/")
    portal.esperar_url("/acceso/")
    assert "next=/mis-pedidos/" in portal.d.current_url
    portal.captura("01_acceso_requerido")


def test_02_clave_incorrecta_muestra_error(portal):
    """Una clave incorrecta no da acceso y muestra un mensaje de error."""
    portal.entrar(clave="ClaveIncorrecta99")
    assert "/acceso/" in portal.d.current_url
    aviso = portal.d.find_element(By.CSS_SELECTOR, ".aviso--mal")
    assert aviso.text.strip()
    portal.captura("02_clave_incorrecta")


def test_03_ingreso_correcto_muestra_el_panel(portal):
    """Con credenciales válidas se llega al inicio con los datos de la empresa."""
    portal.entrar()
    portal.espera.until(lambda d: "/acceso/" not in d.current_url)
    texto = portal.texto()
    assert "Electrica del Maipo" in texto
    assert "Orden de compra" in texto and "Fabricacion" in texto
    portal.captura("03_inicio_cliente")


# ---------------------------------------------------------------- catálogo
def test_04_catalogo_lista_y_filtra_por_familia(portal):
    """El catálogo muestra los modelos y el filtro por familia acota el resultado."""
    portal.ir("/catalogo/")
    fichas = portal.d.find_elements(By.CSS_SELECTOR, "a[href^='/catalogo/'][href$='/']")
    total = len({f.get_attribute("href") for f in fichas})
    assert total >= 4
    familia = Select(portal.d.find_element(By.CSS_SELECTOR, "form select"))
    familia.select_by_visible_text("Distribucion monofasicos")
    portal.d.find_element(By.XPATH, "//button[normalize-space()='Filtrar']").click()
    portal.esperar_url("?")
    filtradas = portal.d.find_elements(By.CSS_SELECTOR, "a[href^='/catalogo/'][href$='/']")
    assert 0 < len({f.get_attribute("href") for f in filtradas}) < total
    portal.captura("04_catalogo_filtrado")


def test_05_ficha_tecnica_del_modelo(portal):
    """La ficha de un modelo muestra su especificación técnica y descarga en PDF."""
    portal.ir("/catalogo/1/")
    texto = portal.texto()
    assert "Potencia nominal" in texto
    portal.captura("05_ficha_modelo")
    respuesta = _descargar(portal, "/catalogo/1/ficha.pdf")
    assert respuesta.status_code == 200
    assert respuesta.headers["Content-Type"].startswith("application/pdf")


# ---------------------------------------------------------------- solicitud
def _numeros_solicitud(portal):
    portal.ir("/mis-solicitudes/")
    return set(re.findall(r"SP-\d{4}-\d{4}", portal.texto()))


def test_06_solicitud_incompleta_es_rechazada(portal):
    """Sin la especificación obligatoria, la solicitud no se crea y se indica el error."""
    antes = _numeros_solicitud(portal)
    portal.ir("/solicitar/")
    portal.d.find_element(By.XPATH, "//button[normalize-space()='Enviar la solicitud']").click()
    assert "/solicitar/" in portal.d.current_url
    errores = portal.d.find_elements(By.CSS_SELECTOR, ".text-danger")
    assert errores, "se esperaban mensajes de error por campo"
    portal.captura("06_solicitud_incompleta")
    assert _numeros_solicitud(portal) == antes


def _llenar_solicitud(portal, potencia):
    """Completa la solicitud para el modelo TD-100 con la potencia indicada."""
    d = portal.d
    portal.ir("/solicitar/?modelo=2")
    cantidad = d.find_element(By.NAME, "cantidad")
    cantidad.clear()
    cantidad.send_keys("3")
    for campo in d.find_elements(By.CSS_SELECTOR, "[name^='param_']"):
        etiqueta = d.find_element(By.CSS_SELECTOR, f"label[for='{campo.get_attribute('id')}']").text
        if campo.tag_name == "select":
            opciones = Select(campo)
            if etiqueta.startswith("Potencia"):
                opciones.select_by_visible_text(potencia)
            else:
                opciones.select_by_index(1)
        else:
            minimo = float(campo.get_attribute("min") or 1)
            maximo = float(campo.get_attribute("max") or minimo)
            campo.clear()
            campo.send_keys(str(int((minimo + maximo) // 2)))


def _enviar_solicitud(portal):
    d = portal.d
    d.find_element(By.XPATH, "//button[normalize-space()='Enviar la solicitud']").click()
    portal.espera.until(lambda drv: "/solicitar/" not in drv.current_url
                        or drv.find_elements(By.CSS_SELECTOR, ".text-danger, .aviso--mal"))
    return [e.text for e in d.find_elements(By.CSS_SELECTOR, ".text-danger, .aviso--mal")]


def test_07_potencia_distinta_al_modelo_es_rechazada(portal):
    """Si la potencia no coincide con el modelo elegido, la solicitud se rechaza con su causa."""
    antes = _numeros_solicitud(portal)
    _llenar_solicitud(portal, potencia="250")
    errores = _enviar_solicitud(portal)
    assert "/solicitar/" in portal.d.current_url
    assert any("TD-100" in e and "100 kVA" in e for e in errores), errores
    portal.captura("07_potencia_distinta_al_modelo")
    assert _numeros_solicitud(portal) == antes


def test_08_solicitud_valida_queda_recibida(portal):
    """Una solicitud con la especificación completa queda registrada como Recibida."""
    antes = _numeros_solicitud(portal)
    _llenar_solicitud(portal, potencia="100")
    portal.captura("08a_solicitud_completa")
    errores = _enviar_solicitud(portal)
    assert "/solicitar/" not in portal.d.current_url, f"el formulario reportó: {errores}"
    nuevas = _numeros_solicitud(portal) - antes
    assert len(nuevas) == 1
    assert "Recibida" in portal.texto()
    portal.captura("08b_solicitud_recibida")


# ---------------------------------------------------------------- cotización
def test_09_cotizacion_emitida_muestra_detalle_y_pdf(portal):
    """La cotización por responder muestra montos en UF y se descarga en PDF."""
    portal.ir("/mis-cotizaciones/")
    assert "Por responder" in portal.texto()
    portal.ir("/cotizacion/1/")
    texto = portal.texto()
    assert "COT-2026-0001" in texto and "UF" in texto
    assert portal.d.find_element(By.XPATH, "//button[contains(., 'Aceptar la cotizacion')]")
    portal.captura("09_cotizacion_emitida")
    respuesta = _descargar(portal, "/cotizacion/1/pdf/")
    assert respuesta.status_code == 200
    assert respuesta.headers["Content-Type"].startswith("application/pdf")


def test_10_aceptar_cotizacion_genera_orden_de_compra(portal):
    """Al aceptar la cotización se genera la orden de compra automáticamente (RN-06)."""
    portal.ir("/mis-pedidos/")
    ordenes_antes = set(re.findall(r"OC-\d{4}-\d{4}", portal.texto()))
    portal.ir("/cotizacion/1/")
    portal.d.find_element(By.XPATH, "//button[contains(., 'Aceptar la cotizacion')]").click()
    alerta = portal.espera.until(EC.alert_is_present())
    alerta.accept()
    portal.espera.until(lambda d: _sin_alerta(d) and "aceptad" in d.page_source.lower())
    portal.captura("10a_cotizacion_aceptada")
    portal.ir("/mis-pedidos/")
    texto = portal.texto()
    nuevas = set(re.findall(r"OC-\d{4}-\d{4}", texto)) - ordenes_antes
    assert len(nuevas) == 1, texto
    assert "desde COT-2026-0001" in texto
    portal.captura("10b_orden_de_compra_generada")


def test_11_documento_de_cobro_del_anticipo(portal):
    """La nueva orden tiene su documento de cobro del anticipo con monto en pesos."""
    portal.ir("/mis-pedidos/")
    cobros = [a.get_attribute("href") for a in
              portal.d.find_elements(By.CSS_SELECTOR, "a[href*='/cobro/']")]
    assert len(set(cobros)) >= 2, "se esperaba el cobro de la nueva orden"
    portal.d.get(sorted(set(cobros))[-1])
    texto = portal.texto()
    assert "Anticipo" in texto and "$" in texto
    assert portal.d.find_element(By.XPATH, "//button[contains(., 'Pagar con PayPal')]")
    portal.captura("11_documento_de_cobro")


def test_12_pago_sin_pasarela_disponible_no_falla(portal):
    """Si PayPal no responde, el sistema informa el problema y no muestra un error 500."""
    portal.d.find_element(By.XPATH, "//button[contains(., 'Pagar con PayPal')]").click()
    portal.espera.until(lambda d: "/cobro/" in d.current_url or "paypal" in d.current_url)
    if "paypal.com" in portal.d.current_url:
        portal.captura("12_redireccion_paypal")
        return  # ambiente con credenciales de PayPal: se llegó a la pasarela
    texto = portal.texto()
    assert "Server Error" not in texto and "500" not in portal.d.title
    assert portal.d.find_elements(By.CSS_SELECTOR, ".aviso--mal, .alert-danger, .aviso"), texto[:400]
    portal.captura("12_pago_sin_pasarela")


# ---------------------------------------------------------------- seguimiento
def test_13_seguimiento_de_fabricacion(portal):
    """El cliente sigue el avance de su orden de trabajo en el taller."""
    portal.ir("/seguimiento/1/")
    texto = portal.texto()
    assert "OT-2026-0001" in texto
    assert "%" in texto
    portal.captura("13_seguimiento_ot")


def test_14_documento_de_otro_cliente_no_es_accesible(portal):
    """Un identificador inexistente o ajeno responde 404, sin exponer datos."""
    respuesta = _descargar(portal, "/cotizacion/9999/")
    assert respuesta.status_code == 404


def test_15_vista_movil_con_menu_colapsado(portal):
    """En un teléfono (390 px) el menú se colapsa y el contenido no se desborda."""
    portal.d.set_window_size(390, 844)
    portal.ir("/mis-pedidos/")
    ancho = portal.d.execute_script("return document.documentElement.scrollWidth")
    assert ancho <= 400
    assert portal.d.find_element(By.CSS_SELECTOR, ".navbar-toggler").is_displayed()
    portal.captura("15_vista_movil")
    portal.d.set_window_size(1366, 900)


def test_16_cerrar_sesion(portal):
    """Al salir, la sesión termina y las páginas del cliente vuelven a pedir acceso."""
    portal.ir("/")
    portal.d.find_element(By.XPATH, "//button[normalize-space()='Salir']").click()
    portal.esperar_url("/acceso/")
    portal.ir("/mis-pedidos/")
    portal.esperar_url("/acceso/")
    portal.captura("16_sesion_cerrada")


# ---------------------------------------------------------------- utilidades
def _descargar(portal, ruta):
    """Descarga una ruta con la misma sesión del navegador."""
    sesion = requests.Session()
    for cookie in portal.d.get_cookies():
        sesion.cookies.set(cookie["name"], cookie["value"])
    return sesion.get(f"{BASE}{ruta}", verify=False, allow_redirects=False, timeout=30)


def _sin_alerta(driver):
    try:
        driver.switch_to.alert
        return False
    except NoAlertPresentException:
        return True
