"""
Pruebas del dominio de configuracion e integraciones.

Verifican la degradacion controlada exigida por RF-INT-03: el sistema debe
seguir operando cuando un servicio externo no responde. Las llamadas se
simulan con dobles de prueba, de modo que la suite no dependa de la
disponibilidad real de los servicios.
"""
import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectTimeout

from apps.configuracion.models import Feriado, LogIntegracion, ParametroSistema
from apps.configuracion.services.feriados import ClienteFeriados, plazo_en_dias_habiles
from apps.configuracion.services.indicadores import ClienteIndicadores, valor_uf
from apps.pagos.models import IndicadorEconomico


class RespuestaFalsa:
    """Doble de prueba de una respuesta HTTP."""

    def __init__(self, datos, status_code=200):
        self._datos = datos
        self.status_code = status_code

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._datos


# ---------------------------------------------------------------------------
# Indicadores economicos
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_sincroniza_indicadores_y_los_almacena():
    datos = {
        "uf": {"valor": 40125.5, "fecha": "2026-09-23T04:00:00.000Z"},
        "utm": {"valor": 68785.0, "fecha": "2026-09-01T04:00:00.000Z"},
        "dolar": {"valor": 942.15, "fecha": "2026-09-23T04:00:00.000Z"},
    }
    with patch("requests.get", return_value=RespuestaFalsa(datos)):
        resultado = ClienteIndicadores().sincronizar_dia(datetime.date(2026, 9, 23))

    assert resultado["exitoso"]
    assert IndicadorEconomico.objects.count() == 3
    uf = IndicadorEconomico.objects.get(codigo="UF")
    assert uf.valor == Decimal("40125.5")
    assert uf.fecha == datetime.date(2026, 9, 23)


@pytest.mark.django_db
def test_llamada_exitosa_queda_registrada_en_el_log():
    """RF-INT-01: toda llamada se registra."""
    datos = {"uf": {"valor": 40125.5, "fecha": "2026-09-23T04:00:00.000Z"}}
    with patch("requests.get", return_value=RespuestaFalsa(datos)):
        ClienteIndicadores().sincronizar_dia()

    log = LogIntegracion.objects.get()
    assert log.servicio == "mindicador"
    assert log.exitoso is True
    assert log.codigo_respuesta == 200


@pytest.mark.django_db
def test_servicio_caido_no_rompe_el_proceso():
    """RF-INT-03: el fallo se informa, no se propaga."""
    with patch("requests.get", side_effect=ConnectTimeout("sin conexion")):
        with patch("time.sleep"):  # evita la espera real entre reintentos
            resultado = ClienteIndicadores().sincronizar_dia()

    assert resultado["exitoso"] is False
    assert "ConnectTimeout" in resultado["error"]
    assert IndicadorEconomico.objects.count() == 0


@pytest.mark.django_db
def test_fallo_transitorio_se_reintenta():
    """RF-INT-02: reintentos con espera incremental."""
    with patch("requests.get", side_effect=ConnectTimeout("sin conexion")) as llamada:
        with patch("time.sleep"):
            ClienteIndicadores().sincronizar_dia()

    assert llamada.call_count == 3
    assert LogIntegracion.objects.filter(exitoso=False).count() == 3


@pytest.mark.django_db
def test_error_de_peticion_no_se_reintenta():
    """Un 4xx indica un problema en la peticion: reintentar no aporta."""
    with patch("requests.get", return_value=RespuestaFalsa({}, status_code=404)) as llamada:
        with patch("time.sleep"):
            ClienteIndicadores().sincronizar_dia()

    assert llamada.call_count == 1


@pytest.mark.django_db
def test_uf_cae_al_ultimo_valor_conocido():
    """RF-PAG-06: se opera con el ultimo valor y se advierte la fecha."""
    IndicadorEconomico.objects.create(
        codigo="UF", fecha=datetime.date(2026, 9, 20), valor=Decimal("40100")
    )

    with patch("requests.get", side_effect=ConnectTimeout("sin conexion")):
        with patch("time.sleep"):
            valor, fecha, es_del_dia = valor_uf(datetime.date(2026, 9, 23))

    assert valor == Decimal("40100")
    assert fecha == datetime.date(2026, 9, 20)
    assert es_del_dia is False


@pytest.mark.django_db
def test_uf_sin_historico_ni_servicio_devuelve_none():
    with patch("requests.get", side_effect=ConnectTimeout("sin conexion")):
        with patch("time.sleep"):
            valor, fecha, es_del_dia = valor_uf()

    assert valor is None and fecha is None and es_del_dia is False


# ---------------------------------------------------------------------------
# Feriados y dias habiles
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_sincroniza_feriados():
    """Formato de feriadito.cl: objeto con la clave feriados."""
    datos = {
        "anio": 2026,
        "cantidad": 2,
        "feriados": [
            {"nombre": "Independencia Nacional", "fecha": "2026-09-18", "tipo": "Civil"},
            {"nombre": "Dia de las Glorias del Ejercito", "fecha": "2026-09-19", "tipo": "Civil"},
        ],
    }
    with patch("requests.get", return_value=RespuestaFalsa(datos)):
        resultado = ClienteFeriados().sincronizar_anio(2026)

    assert resultado["exitoso"]
    assert resultado["creados"] == 2
    assert Feriado.objects.filter(fecha=datetime.date(2026, 9, 18)).exists()


@pytest.mark.django_db
def test_sincroniza_feriados_acepta_lista_directa():
    """Otros proveedores devuelven la lista sin envoltorio."""
    datos = [{"nombre": "Ano Nuevo", "fecha": "2026-01-01", "tipo": "Civil"}]
    with patch("requests.get", return_value=RespuestaFalsa(datos)):
        resultado = ClienteFeriados().sincronizar_anio(2026)

    assert resultado["creados"] == 1


@pytest.mark.django_db
def test_feriados_servicio_caido_conserva_los_almacenados():
    """RF-INT-03: el calculo de plazos sigue funcionando."""
    Feriado.objects.create(fecha=datetime.date(2026, 9, 18), nombre="Independencia")

    with patch("requests.get", side_effect=ConnectTimeout("sin conexion")):
        with patch("time.sleep"):
            resultado = ClienteFeriados().sincronizar_anio(2026)

    assert resultado["exitoso"] is False
    assert resultado["total"] == 1
    assert Feriado.es_habil(datetime.date(2026, 9, 18)) is False


@pytest.mark.django_db
def test_plazo_descuenta_feriados():
    """RN-08: el plazo se calcula en dias habiles."""
    Feriado.objects.create(fecha=datetime.date(2026, 9, 18), nombre="Independencia")
    Feriado.objects.create(fecha=datetime.date(2026, 9, 19), nombre="Glorias del Ejercito")

    fecha, con_feriados = plazo_en_dias_habiles(datetime.date(2026, 9, 16), 10)

    assert con_feriados is True
    assert fecha == datetime.date(2026, 10, 1)


@pytest.mark.django_db
def test_plazo_sin_feriados_almacenados_advierte():
    """Excepcion E8 de CU-COM-03: se calcula igual, pero se advierte."""
    fecha, con_feriados = plazo_en_dias_habiles(datetime.date(2026, 9, 16), 10)

    assert con_feriados is False
    assert fecha == datetime.date(2026, 9, 30)  # solo excluye sabados y domingos


@pytest.mark.django_db
def test_dia_feriado_no_es_habil():
    Feriado.objects.create(fecha=datetime.date(2026, 9, 18), nombre="Independencia")

    assert Feriado.es_habil(datetime.date(2026, 9, 18)) is False
    assert Feriado.es_habil(datetime.date(2026, 9, 17)) is True
    assert Feriado.es_habil(datetime.date(2026, 9, 20)) is False  # domingo


# ---------------------------------------------------------------------------
# Parametros del sistema
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_parametro_devuelve_valor_tipado(django_user_model):
    usuario = django_user_model.objects.create_user("adm", "a@a.cl", "Clave12345")
    ParametroSistema.objects.create(
        clave="web.modo_mantencion", valor="true", tipo_dato="booleano",
        ambito="canal_web", usuario=usuario,
    )
    ParametroSistema.objects.create(
        clave="comercial.vigencia_cotizacion_dias", valor="30", tipo_dato="numerico",
        ambito="comercial", usuario=usuario,
    )

    assert ParametroSistema.obtener("web.modo_mantencion") is True
    assert ParametroSistema.obtener("comercial.vigencia_cotizacion_dias") == Decimal("30")


@pytest.mark.django_db
def test_parametro_inexistente_usa_el_valor_por_defecto():
    assert ParametroSistema.obtener("clave.que.no.existe", "respaldo") == "respaldo"


@pytest.mark.django_db
def test_feriados_formato_nager_omite_regionales():
    """
    Proveedor actual: Nager.Date (lista directa, campos en ingles). Los
    feriados regionales no deben guardarse: correrian plazos de empresas
    de otras regiones.
    """
    datos = [
        {"date": "2026-09-18", "localName": "Fiestas Patrias", "global": True},
        {"date": "2026-06-07", "localName": "Asalto y Toma del Morro de Arica",
         "global": False, "counties": ["CL-AP"]},
    ]
    cliente = ClienteFeriados("https://date.nager.at/api/v3/PublicHolidays")
    with patch("requests.get", return_value=RespuestaFalsa(datos)) as llamada:
        resultado = cliente.sincronizar_anio(2026)

    assert resultado["exitoso"]
    assert llamada.call_args.args[0].endswith("/PublicHolidays/2026/CL")
    assert list(Feriado.objects.values_list("nombre", flat=True)) == ["Fiestas Patrias"]


# ---------------------------------------------------------------------------
# Correo transaccional (Brevo)
# ---------------------------------------------------------------------------
def _mensaje_prueba():
    from django.core.mail import EmailMultiAlternatives

    mensaje = EmailMultiAlternatives(
        subject="Cotizacion COT-2026-0001", body="Texto plano",
        from_email="SITRAFO <ventas@sitrafo.cl>", to=["Cliente <cliente@maipo.cl>"],
    )
    mensaje.attach_alternative("<p>HTML</p>", "text/html")
    return mensaje


@pytest.mark.django_db
def test_brevo_arma_el_mensaje_y_registra_el_envio():
    from apps.configuracion.services.correo import ClienteBrevo

    with patch("requests.post",
               return_value=RespuestaFalsa({"messageId": "<abc@smtp>"}, 201)) as llamada:
        resultado = ClienteBrevo(api_key="clave-prueba").enviar(_mensaje_prueba())

    assert resultado.exitoso
    url, kwargs = llamada.call_args.args[0], llamada.call_args.kwargs
    assert url.endswith("/v3/smtp/email")
    assert kwargs["headers"]["api-key"] == "clave-prueba"
    cuerpo = kwargs["json"]
    assert cuerpo["sender"] == {"name": "SITRAFO", "email": "ventas@sitrafo.cl"}
    assert cuerpo["to"] == [{"name": "Cliente", "email": "cliente@maipo.cl"}]
    assert cuerpo["htmlContent"] == "<p>HTML</p>"
    assert cuerpo["textContent"] == "Texto plano"

    log = LogIntegracion.objects.get(servicio="correo")
    assert log.exitoso and log.metodo == "POST"
    assert "clave-prueba" not in log.endpoint


@pytest.mark.django_db
def test_brevo_sin_clave_no_llama_al_servicio():
    from apps.configuracion.services.correo import ClienteBrevo

    with patch("requests.post") as llamada:
        resultado = ClienteBrevo(api_key="").enviar(_mensaje_prueba())
    assert resultado.exitoso is False
    llamada.assert_not_called()


@pytest.mark.django_db
def test_backend_brevo_caido_no_rompe_el_proceso(settings):
    """RF-INT-03: con fail_silently el fallo se registra y no se propaga."""
    from apps.configuracion.services.correo import BrevoEmailBackend

    settings.BREVO_API_KEY = "clave-prueba"
    with patch("requests.post", side_effect=ConnectTimeout("sin conexion")), \
         patch("time.sleep"):
        enviados = BrevoEmailBackend(fail_silently=True).send_messages([_mensaje_prueba()])

    assert enviados == 0
    assert LogIntegracion.objects.filter(servicio="correo", exitoso=False).count() == 2


@pytest.mark.django_db
def test_destinatarios_prefiere_contacto_principal_y_cae_a_cuentas(django_user_model):
    from apps.clientes.models import Cliente, ContactoCliente
    from apps.configuracion.services.notificaciones import destinatarios_de

    cliente = Cliente.objects.create(
        rut="76543210-3", razon_social="Maipo SpA", tipo_persona="juridica"
    )
    django_user_model.objects.create_user("maipo", "cuenta@maipo.cl", "x" * 12,
                                          cliente=cliente)
    assert destinatarios_de(cliente) == ["cuenta@maipo.cl"]

    ContactoCliente.objects.create(cliente=cliente, nombre="Ana", email="ana@maipo.cl")
    assert destinatarios_de(cliente) == ["ana@maipo.cl"]

    ContactoCliente.objects.create(cliente=cliente, nombre="Jefe", email="jefe@maipo.cl",
                                   principal=True)
    assert destinatarios_de(cliente) == ["jefe@maipo.cl"]


@pytest.mark.django_db
def test_redireccion_de_correos_en_desarrollo(settings):
    from django.core import mail

    from apps.configuracion.services.notificaciones import enviar

    settings.CORREO_REDIRIGIR_A = "benja@prueba.cl"
    ok = enviar("solicitud_recibida", "Asunto", ["cliente@maipo.cl"],
                {"solicitud": type("S", (), {"numero": "SP-1", "cantidad": 1,
                                             "modelo": None, "fecha_deseada": None})(),
                 "url": "http://x"})
    assert ok
    assert mail.outbox[0].to == ["benja@prueba.cl"]
    assert "cliente@maipo.cl" in mail.outbox[0].subject
