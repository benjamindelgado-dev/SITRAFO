"""
Carga un caso de demostracion completo.

Siembra un cliente con su cuenta web, cuatro modelos de transformador con su
especificacion tecnica y sus precios, y la cadena documental recorrida de
punta a punta: solicitud, cotizacion emitida, cotizacion aceptada, orden de
compra y orden de trabajo en fabricacion.

Sirve para revisar el sistema y para preparar la demostracion sin cargar los
datos a mano.

Uso:
    python manage.py cargar_demo
    python manage.py cargar_demo --forzar
"""
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogo.models import (
    FamiliaProducto,
    ModeloParametro,
    ModeloProducto,
    ParametroTecnico,
    PrecioBaseModelo,
    ValorParametro,
)
from apps.clientes.models import Cliente, Comuna, DireccionCliente, Region
from apps.comercial.models import (
    Cotizacion,
    CotizacionHistorial,
    CotizacionLinea,
    EstadoDocumento,
    OrdenCompra,
    OrdenCompraLinea,
    SolicitudEspecificacion,
    SolicitudHistorial,
    SolicitudPresupuesto,
)
from apps.pagos.services.cobros import ErrorCobro, emitir_anticipo
from apps.produccion.models import OrdenTrabajo, OrdenTrabajoHistorial, TareaOT
from apps.seguridad.models import Usuario

RUT_DEMO = "76543210-3"

PARAMETROS = [
    ("potencia_kva", "Potencia nominal", "kVA", "lista",
     ["50", "100", "150", "250", "500"]),
    ("tension_prim", "Tension primaria", "kV", "numerico", []),
    ("tension_sec", "Tension secundaria", "V", "numerico", []),
    ("grupo_conexion", "Grupo de conexion", "", "lista", ["Dyn11", "Dyn5", "Yzn11"]),
    ("refrigeracion", "Refrigeracion", "", "lista", ["ONAN", "ONAF"]),
]

MODELOS = [
    ("TD-050", "Transformador de distribucion 50 kVA", "trifasicos",
     ("50", "15", "400", "Dyn11", "ONAN"), "118.5000"),
    ("TD-100", "Transformador de distribucion 100 kVA", "trifasicos",
     ("100", "15", "400", "Dyn11", "ONAN"), "185.0000"),
    ("TD-250", "Transformador de distribucion 250 kVA", "trifasicos",
     ("250", "23", "400", "Dyn11", "ONAN"), "342.8000"),
    ("TM-025", "Transformador monofasico 25 kVA", "monofasicos",
     ("50", "15", "400", "Yzn11", "ONAN"), None),
]

TAREAS = [
    ("Corte y armado de nucleo", 8, TareaOT.Estado.TERMINADA),
    ("Bobinado de baja tension", 16, TareaOT.Estado.TERMINADA),
    ("Bobinado de alta tension", 18, TareaOT.Estado.EN_EJECUCION),
    ("Ensamble y llenado de aceite", 12, TareaOT.Estado.PENDIENTE),
    ("Ensayos de rutina", 6, TareaOT.Estado.PENDIENTE),
]

DESCRIPCION = (
    "Transformador sumergido en aceite mineral, apto para montaje exterior "
    "en poste o plataforma. Fabricado segun la especificacion tecnica "
    "indicada en la solicitud."
)


class Command(BaseCommand):
    help = "Carga un caso de demostracion completo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Carga los datos aunque el caso ya exista.",
        )

    def handle(self, *args, **options):
        if not EstadoDocumento.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    "No hay estados cargados. Ejecute antes: "
                    "python manage.py cargar_estados"
                )
            )
            return

        if Cliente.objects.filter(rut=RUT_DEMO).exists() and not options["forzar"]:
            self.stdout.write(
                self.style.WARNING(
                    "El caso de demostracion ya esta cargado. "
                    "Use --forzar para volver a sembrarlo."
                )
            )
            return

        try:
            self._sembrar()
        except Exception as error:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"No se pudo sembrar: {error}"))
            return

        self.stdout.write(self.style.SUCCESS("Caso de demostracion cargado."))
        self.stdout.write("")
        self.stdout.write("  Portal del cliente — http://localhost:8000")
        self.stdout.write("    usuario  maipo")
        self.stdout.write("    clave    ClaveSegura2026")
        self.stdout.write("")
        self.stdout.write("  Escritorio y administracion")
        self.stdout.write("    usuario  ejecutivo")
        self.stdout.write("    clave    Clave123456")

    # ------------------------------------------------------------------
    @transaction.atomic
    def _sembrar(self):
        estado = lambda tipo, codigo: EstadoDocumento.objects.get(  # noqa: E731
            tipo_documento=tipo, codigo=codigo
        )

        ejecutivo, creado = Usuario.objects.get_or_create(
            username="ejecutivo",
            defaults={"email": "ejecutivo@sitrafo.cl", "es_interno": True,
                      "is_staff": True, "is_superuser": True},
        )
        if creado:
            ejecutivo.set_password("Clave123456")
            ejecutivo.save()

        region, _ = Region.objects.get_or_create(
            nombre="Metropolitana de Santiago", defaults={"codigo": "RM"}
        )
        comuna, _ = Comuna.objects.get_or_create(region=region, nombre="Puente Alto")

        cliente, _ = Cliente.objects.get_or_create(
            rut=RUT_DEMO,
            defaults={
                "razon_social": "Electrica del Maipo SpA",
                "tipo_persona": Cliente.TipoPersona.JURIDICA,
                "giro": "Distribucion electrica",
            },
        )
        DireccionCliente.objects.get_or_create(
            cliente=cliente, comuna=comuna, tipo=DireccionCliente.Tipo.INSTALACION,
            calle="Av. Concha y Toro", numero="2450",
        )

        cuenta, creada = Usuario.objects.get_or_create(
            username="maipo",
            defaults={"email": "contacto@maipo.cl", "cliente": cliente,
                      "es_interno": False},
        )
        if creada:
            cuenta.set_password("ClaveSegura2026")
            cuenta.save()

        # -- Catalogo --------------------------------------------------
        familias = {
            "trifasicos": FamiliaProducto.objects.get_or_create(
                nombre="Distribucion trifasicos"
            )[0],
            "monofasicos": FamiliaProducto.objects.get_or_create(
                nombre="Distribucion monofasicos"
            )[0],
        }

        parametros = {}
        for codigo, nombre, unidad, tipo, valores in PARAMETROS:
            parametro, _ = ParametroTecnico.objects.get_or_create(
                codigo=codigo,
                defaults={"nombre": nombre, "unidad": unidad, "tipo_dato": tipo},
            )
            parametros[codigo] = parametro
            for orden, valor in enumerate(valores):
                ValorParametro.objects.get_or_create(
                    parametro=parametro, valor=valor, defaults={"orden": orden}
                )

        modelos = {}
        for codigo, nombre, familia, valores, precio in MODELOS:
            modelo, _ = ModeloProducto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "familia": familias[familia],
                    "nombre": nombre,
                    "descripcion": DESCRIPCION,
                    "publicado": True,
                },
            )
            for (clave, *_), valor in zip(PARAMETROS, valores):
                ModeloParametro.objects.get_or_create(
                    modelo=modelo, parametro=parametros[clave],
                    defaults={"valor_defecto": valor},
                )
            if precio:
                PrecioBaseModelo.objects.get_or_create(
                    modelo=modelo, vigente_desde=datetime.date(2026, 1, 1),
                    defaults={"monto_uf": Decimal(precio), "usuario": ejecutivo},
                )
            modelos[codigo] = modelo

        # -- Solicitudes -----------------------------------------------
        solicitud = SolicitudPresupuesto.objects.create(
            numero=SolicitudPresupuesto.generar_numero(), cliente=cliente,
            modelo=modelos["TD-100"],
            cantidad=2, fecha_deseada=datetime.date(2026, 12, 1),
            estado=estado("solicitud", "cotizada"),
        )
        for clave, valor in [("potencia_kva", "100"), ("tension_prim", "23"),
                             ("tension_sec", "400"), ("grupo_conexion", "Dyn11"),
                             ("refrigeracion", "ONAN")]:
            SolicitudEspecificacion.objects.create(
                solicitud=solicitud, parametro=parametros[clave], valor=valor
            )
        SolicitudHistorial.objects.create(
            solicitud=solicitud, estado_nuevo=estado("solicitud", "recibida"),
            usuario=cuenta, observacion="Solicitud recibida desde la aplicacion web.",
        )

        segunda = SolicitudPresupuesto.objects.create(
            numero=SolicitudPresupuesto.generar_numero(), cliente=cliente,
            modelo=modelos["TD-250"],
            cantidad=1, estado=estado("solicitud", "recibida"),
        )
        for clave, valor in [("potencia_kva", "250"), ("tension_prim", "23")]:
            SolicitudEspecificacion.objects.create(
                solicitud=segunda, parametro=parametros[clave], valor=valor
            )

        # -- Cotizacion pendiente de respuesta -------------------------
        emitida = Cotizacion.objects.create(
            numero=Cotizacion.generar_numero(), solicitud=solicitud, cliente=cliente,
            estado=estado("cotizacion", "emitida"), ejecutivo=ejecutivo,
            valor_uf=Decimal("40125.50"), fecha_valor_uf=datetime.date(2026, 9, 20),
            vence_el=datetime.date(2026, 10, 20), plazo_dias_habiles=25,
            fecha_entrega=datetime.date(2026, 10, 28), total_uf=Decimal("412.6000"),
        )
        CotizacionLinea.objects.create(
            cotizacion=emitida, modelo=modelos["TD-100"], cantidad=2,
            costo_material_uf=Decimal("108.4000"), costo_hh_uf=Decimal("56.7000"),
            margen_pct=Decimal("25"), precio_uf=Decimal("206.3000"),
        )
        CotizacionHistorial.objects.create(
            cotizacion=emitida, estado_nuevo=estado("cotizacion", "borrador"),
            usuario=ejecutivo, observacion="Cotizacion elaborada.",
        )
        CotizacionHistorial.objects.create(
            cotizacion=emitida, estado_anterior=estado("cotizacion", "borrador"),
            estado_nuevo=estado("cotizacion", "emitida"), usuario=ejecutivo,
            observacion="Emitida al cliente.",
        )

        # -- Cotizacion aceptada, con pedido en fabricacion ------------
        aceptada = Cotizacion.objects.create(
            numero=Cotizacion.generar_numero(), solicitud=solicitud, cliente=cliente,
            estado=estado("cotizacion", "aceptada"), ejecutivo=ejecutivo,
            valor_uf=Decimal("39980.00"), fecha_valor_uf=datetime.date(2026, 8, 5),
            vence_el=datetime.date(2026, 9, 4), total_uf=Decimal("118.5000"),
        )
        linea = CotizacionLinea.objects.create(
            cotizacion=aceptada, modelo=modelos["TD-050"], cantidad=1,
            precio_uf=Decimal("118.5000"),
        )
        CotizacionHistorial.objects.create(
            cotizacion=aceptada, estado_nuevo=estado("cotizacion", "aceptada"),
            usuario=cuenta, observacion="Aceptada por el cliente.",
        )

        orden = OrdenCompra.objects.create(
            numero=OrdenCompra.generar_numero(), cotizacion=aceptada, cliente=cliente,
            estado=estado("orden_compra", "en_produccion"),
            total_uf=Decimal("118.5000"), anticipo_pct=Decimal("50"),
        )
        OrdenCompraLinea.objects.create(
            orden_compra=orden, cotizacion_linea=linea, cantidad=1,
            precio_uf=Decimal("118.5000"),
        )

        ot = OrdenTrabajo.objects.create(
            numero=OrdenTrabajo.generar_numero(), orden_compra=orden, modelo=modelos["TD-050"],
            cantidad=1, estado=estado("orden_trabajo", "en_ejecucion"),
            costo_estimado_uf=Decimal("94.8000"), avance_pct=Decimal("62.50"),
            fecha_inicio=datetime.date(2026, 9, 8),
        )
        for secuencia, (nombre, horas, estado_tarea) in enumerate(TAREAS, 1):
            TareaOT.objects.create(
                orden_trabajo=ot, nombre=nombre, secuencia=secuencia,
                horas_estimadas=Decimal(horas), estado=estado_tarea,
            )
        OrdenTrabajoHistorial.objects.create(
            orden_trabajo=ot, estado_nuevo=estado("orden_trabajo", "planificada"),
            usuario=ejecutivo,
            observacion=f"Generada desde la orden de compra {orden.numero}.",
        )
        OrdenTrabajoHistorial.objects.create(
            orden_trabajo=ot, estado_anterior=estado("orden_trabajo", "planificada"),
            estado_nuevo=estado("orden_trabajo", "en_ejecucion"), usuario=ejecutivo,
            observacion="Inicio de fabricacion en taller.",
        )

        # -- Anticipo pendiente de pago (para demostrar el pago en linea)
        try:
            emitir_anticipo(orden)
        except ErrorCobro as error:
            self.stdout.write(self.style.WARNING(
                f"Anticipo no emitido ({error}). Ejecute luego: python manage.py emitir_cobros"
            ))
