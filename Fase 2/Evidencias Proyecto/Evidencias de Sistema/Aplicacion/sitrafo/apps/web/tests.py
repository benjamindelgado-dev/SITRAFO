"""
Pruebas de la aplicacion web del cliente.

Verifican el autorregistro, el aislamiento entre clientes (RN-16), la
visibilidad del catalogo segun publicacion (RF-ADM-06) y el modo mantencion
administrado desde la aplicacion de escritorio (RF-ADM-01).
"""
import datetime
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalogo.models import (
    FamiliaProducto,
    ModeloProducto,
    ParametroTecnico,
    ValorParametro,
)
from apps.clientes.models import Cliente
from apps.comercial.models import Cotizacion, EstadoDocumento, SolicitudPresupuesto
from apps.configuracion.models import ParametroSistema


@pytest.fixture
def escenario(db, django_user_model, client):
    cliente = Cliente.objects.create(
        rut="76543210-3", razon_social="Electrica del Maipo SpA",
        tipo_persona="juridica",
    )
    otro = Cliente.objects.create(
        rut="77777777-7", razon_social="Otra Empresa Ltda", tipo_persona="juridica"
    )
    usuario = django_user_model.objects.create_user(
        "maipo", "c@c.cl", "ClaveSegura2026", cliente=cliente, es_interno=False
    )
    interno = django_user_model.objects.create_user(
        "ejecutivo", "e@e.cl", "ClaveSegura2026", es_interno=True
    )
    familia = FamiliaProducto.objects.create(nombre="Distribucion")
    publicado = ModeloProducto.objects.create(
        familia=familia, codigo="TD-100", nombre="Transformador 100 kVA",
        publicado=True,
    )
    oculto = ModeloProducto.objects.create(
        familia=familia, codigo="TD-999", nombre="Prototipo reservado",
        publicado=False,
    )
    parametro = ParametroTecnico.objects.create(
        codigo="potencia_kva", nombre="Potencia nominal", unidad="kVA",
        tipo_dato="lista", obligatorio=True,
    )
    ValorParametro.objects.create(parametro=parametro, valor="100", orden=1)

    EstadoDocumento.objects.create(
        tipo_documento="solicitud", codigo="recibida", nombre="Recibida"
    )
    estado_emitida = EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="emitida", nombre="Emitida"
    )
    EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="aceptada", nombre="Aceptada", es_final=True
    )
    EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="rechazada", nombre="Rechazada", es_final=True
    )
    EstadoDocumento.objects.create(
        tipo_documento="cotizacion", codigo="vencida", nombre="Vencida", es_final=True
    )

    client.force_login(usuario)
    return {
        "client": client, "cliente": cliente, "otro": otro, "usuario": usuario,
        "interno": interno, "publicado": publicado, "oculto": oculto,
        "parametro": parametro, "estado_emitida": estado_emitida,
    }


# ---------------------------------------------------------------------------
# Acceso y autorregistro
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_inicio_exige_sesion(client):
    respuesta = client.get(reverse("web:inicio"))
    assert respuesta.status_code == 302
    assert "/acceso/" in respuesta["Location"]


@pytest.mark.django_db
def test_autorregistro_crea_cliente_y_cuenta(client, django_user_model):
    """RF-CLI-06."""
    datos = {
        "rut": "76.543.210-3", "razon_social": "Electrica del Maipo SpA",
        "tipo_persona": "juridica", "giro": "Distribucion electrica",
        "username": "maipo", "email": "contacto@maipo.cl",
        "password1": "ClaveSegura2026", "password2": "ClaveSegura2026",
    }
    respuesta = client.post(reverse("web:registro"), datos)

    assert respuesta.status_code == 302
    assert Cliente.objects.filter(rut="76543210-3").exists()
    usuario = django_user_model.objects.get(username="maipo")
    assert usuario.es_interno is False
    assert usuario.cliente.razon_social == "Electrica del Maipo SpA"


@pytest.mark.django_db
def test_autorregistro_rechaza_rut_invalido(client):
    """RF-CLI-02."""
    datos = {
        "rut": "12345678-9", "razon_social": "Empresa X", "tipo_persona": "juridica",
        "username": "x", "email": "x@x.cl",
        "password1": "ClaveSegura2026", "password2": "ClaveSegura2026",
    }
    respuesta = client.post(reverse("web:registro"), datos)

    assert respuesta.status_code == 200
    assert not Cliente.objects.filter(rut="12345678-9").exists()


@pytest.mark.django_db
def test_autorregistro_rechaza_contrasenas_distintas(client):
    datos = {
        "rut": "76.543.210-3", "razon_social": "Empresa X", "tipo_persona": "juridica",
        "username": "x", "email": "x@x.cl",
        "password1": "ClaveSegura2026", "password2": "OtraClave2026",
    }
    client.post(reverse("web:registro"), datos)
    assert Cliente.objects.count() == 0


# ---------------------------------------------------------------------------
# Catalogo
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_catalogo_solo_muestra_lo_publicado(escenario):
    """RF-ADM-06: la visibilidad se administra desde escritorio."""
    contenido = escenario["client"].get(reverse("web:catalogo")).content.decode()

    assert "TD-100" in contenido
    assert "TD-999" not in contenido


@pytest.mark.django_db
def test_ficha_de_modelo_no_publicado_no_es_accesible(escenario):
    url = reverse("web:ficha_modelo", args=[escenario["oculto"].pk])
    assert escenario["client"].get(url).status_code == 404


# ---------------------------------------------------------------------------
# Solicitud de presupuesto
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_solicitud_captura_la_especificacion_tecnica(escenario):
    """CU-COM-01."""
    datos = {
        "modelo": escenario["publicado"].pk,
        "cantidad": 2,
        "fecha_deseada": "2026-12-01",
        f"param_{escenario['parametro'].id_parametro}": "100",
    }
    respuesta = escenario["client"].post(reverse("web:solicitar"), datos)

    assert respuesta.status_code == 302
    solicitud = SolicitudPresupuesto.objects.get()
    assert solicitud.cliente == escenario["cliente"]
    assert solicitud.especificaciones.count() == 1
    assert solicitud.especificaciones.first().valor == "100"
    assert solicitud.historial.count() == 1


@pytest.mark.django_db
def test_solicitud_se_asigna_al_cliente_de_la_cuenta(escenario):
    """RN-16: el cliente no se toma del formulario."""
    datos = {
        "modelo": escenario["publicado"].pk,
        "cantidad": 1,
        "cliente": escenario["otro"].pk,
        f"param_{escenario['parametro'].id_parametro}": "100",
    }
    escenario["client"].post(reverse("web:solicitar"), datos)

    assert SolicitudPresupuesto.objects.get().cliente == escenario["cliente"]


# ---------------------------------------------------------------------------
# Cotizaciones
# ---------------------------------------------------------------------------
def _crear_cotizacion(escenario, vence_el, numero="COT-2026-0001", cliente=None):
    estado_sol = EstadoDocumento.objects.get(
        tipo_documento="solicitud", codigo="recibida"
    )
    solicitud = SolicitudPresupuesto.objects.create(
        numero=f"SP-{numero}", cliente=cliente or escenario["cliente"],
        cantidad=1, estado=estado_sol,
    )
    return Cotizacion.objects.create(
        numero=numero, solicitud=solicitud,
        cliente=cliente or escenario["cliente"],
        estado=escenario["estado_emitida"], ejecutivo=escenario["interno"],
        valor_uf=Decimal("40125.50"), fecha_valor_uf=datetime.date(2026, 9, 23),
        vence_el=vence_el, total_uf=Decimal("99.25"),
    )


@pytest.mark.django_db
def test_cliente_no_ve_cotizaciones_de_otro(escenario):
    """RN-16."""
    futura = datetime.date.today() + datetime.timedelta(days=10)
    ajena = _crear_cotizacion(escenario, futura, cliente=escenario["otro"])

    listado = escenario["client"].get(reverse("web:mis_cotizaciones"))
    detalle = escenario["client"].get(
        reverse("web:detalle_cotizacion", args=[ajena.pk])
    )

    assert ajena.numero not in listado.content.decode()
    assert detalle.status_code == 404


@pytest.mark.django_db
def test_aceptar_cotizacion_vigente(escenario):
    """CU-COM-08."""
    futura = datetime.date.today() + datetime.timedelta(days=10)
    cotizacion = _crear_cotizacion(escenario, futura)

    escenario["client"].post(
        reverse("web:aceptar_cotizacion", args=[cotizacion.pk])
    )
    cotizacion.refresh_from_db()

    assert cotizacion.estado.codigo == "aceptada"
    assert cotizacion.historial.count() == 1


@pytest.mark.django_db
def test_aceptar_cotizacion_vencida_la_marca_vencida(escenario):
    """RN-04: la vigencia se verifica al confirmar, no solo al desplegar."""
    pasada = datetime.date.today() - datetime.timedelta(days=1)
    cotizacion = _crear_cotizacion(escenario, pasada)

    escenario["client"].post(
        reverse("web:aceptar_cotizacion", args=[cotizacion.pk])
    )
    cotizacion.refresh_from_db()

    assert cotizacion.estado.codigo == "vencida"


@pytest.mark.django_db
def test_rechazar_exige_motivo(escenario):
    futura = datetime.date.today() + datetime.timedelta(days=10)
    cotizacion = _crear_cotizacion(escenario, futura)

    escenario["client"].post(
        reverse("web:rechazar_cotizacion", args=[cotizacion.pk]), {"motivo": ""}
    )
    cotizacion.refresh_from_db()
    assert cotizacion.estado.codigo == "emitida"

    escenario["client"].post(
        reverse("web:rechazar_cotizacion", args=[cotizacion.pk]),
        {"motivo": "Precio fuera de presupuesto"},
    )
    cotizacion.refresh_from_db()
    assert cotizacion.estado.codigo == "rechazada"
    assert cotizacion.historial.first().observacion == "Precio fuera de presupuesto"


# ---------------------------------------------------------------------------
# Modo mantencion
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_modo_mantencion_suspende_la_web(escenario):
    """RF-ADM-01: el escritorio administra el comportamiento del sitio."""
    ParametroSistema.objects.create(
        clave="web.modo_mantencion", valor="true", tipo_dato="booleano",
        ambito="canal_web", usuario=escenario["interno"],
    )

    respuesta = escenario["client"].get(reverse("web:catalogo"))

    assert respuesta.status_code == 503
    assert b"mantencion" in respuesta.content.lower()


@pytest.mark.django_db
def test_modo_mantencion_no_afecta_al_usuario_interno(escenario):
    ParametroSistema.objects.create(
        clave="web.modo_mantencion", valor="true", tipo_dato="booleano",
        ambito="canal_web", usuario=escenario["interno"],
    )
    escenario["client"].force_login(escenario["interno"])

    assert escenario["client"].get(reverse("web:catalogo")).status_code == 200
