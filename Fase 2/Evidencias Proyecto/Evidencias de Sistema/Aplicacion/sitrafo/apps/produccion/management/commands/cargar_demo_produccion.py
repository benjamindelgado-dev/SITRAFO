"""
Datos de demostracion del area productiva.

Complementa a cargar_demo con lo necesario para operar el taller:
materiales con precio y stock, lista de materiales, tareas estandar y
protocolo de ensayos de rutina de cada modelo, empleados con tarifa y la asociacion del usuario "operario" a un
empleado. Es idempotente: se puede ejecutar varias veces.

Uso:
    python manage.py cargar_demo_produccion
"""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.calidad.models import ProtocoloCalidad, PuntoControl
from apps.catalogo.models import BomModelo, ModeloProducto, TareaEstandarModelo
from apps.inventario.models import (
    Bodega,
    CategoriaMaterial,
    Material,
    MovimientoInventario,
    PrecioMaterial,
)
from apps.produccion.models import (
    Empleado,
    OrdenTrabajo,
    RegistroHoraHombre,
    TareaOT,
    TarifaHoraHombre,
)

DESDE = datetime.date(2026, 1, 1)

# codigo, nombre, categoria, unidad, costo UF, stock minimo, stock inicial
MATERIALES = [
    ("ACE-SI", "Acero al silicio grano orientado", "Nucleo", "kg", "0.0850", "500", "2500"),
    ("CU-ESM", "Alambre de cobre esmaltado", "Conductores", "kg", "0.3500", "200", "900"),
    ("ACT-DIE", "Aceite dielectrico mineral", "Aislantes", "L", "0.0800", "400", "1800"),
    ("AIS-BT", "Aislador pasatapas BT", "Accesorios", "u", "0.6000", "20", "80"),
    ("AIS-AT", "Aislador pasatapas AT", "Accesorios", "u", "1.1000", "15", "60"),
    ("TNQ-01", "Tanque de acero con radiadores", "Estructura", "u", "12.0000", "4", "10"),
]

# Cantidad por unidad de producto, para un transformador de 100 kVA; el
# resto de los modelos se escala por su potencia
BOM_BASE_100 = {"ACE-SI": 180, "CU-ESM": 60, "ACT-DIE": 150, "AIS-BT": 4, "AIS-AT": 3,
                "TNQ-01": 1}
ESCALA = {"TD-050": Decimal("0.6"), "TD-100": Decimal("1"), "TD-250": Decimal("2"),
          "TM-025": Decimal("0.35")}

# nombre, secuencia, horas por unidad. Son horas de demostracion, reducidas
# a proposito (maximo 2 por tarea) para poder recorrer el flujo completo en
# una sesion de pruebas; en operacion real se cargan las horas del taller.
TAREAS_DEMO = [
    ("Corte y armado de nucleo", 1, 2),
    ("Bobinado de baja tension", 2, 2),
    ("Bobinado de alta tension", 3, 2),
    ("Ensamble y llenado de aceite", 4, 2),
    ("Ensayos de rutina", 5, 1),
]
HORAS_MAXIMAS_DEMO = Decimal("2")

# Ensayos de rutina segun IEC 60076-1: nombre, unidad, nominal, minimo,
# maximo, obligatorio. Las perdidas en vacio dependen de la potencia.
ENSAYOS = [
    ("Resistencia de aislamiento AT-BT y a tierra", "MOhm", None, "1000", None, True),
    ("Relacion de transformacion (desviacion)", "%", "0", "-0.5", "0.5", True),
    ("Resistencia de devanados (desbalance entre fases)", "%", "0", None, "2", True),
    ("Tension aplicada durante 60 s", "kV", "34", "34", None, True),
    ("Corriente de vacio", "%", None, None, "2.5", True),
    ("Perdidas en vacio", "W", None, None, "{perdidas}", True),
    ("Rigidez dielectrica del aceite", "kV", None, "30", None, True),
    ("Nivel de ruido", "dB", None, None, "60", False),
]
PERDIDAS_VACIO_W = {"TD-050": 190, "TD-100": 320, "TD-250": 650, "TM-025": 110}

# rut, nombre, cargo, tarifa UF/hora, usuario del sistema
EMPLEADOS = [
    ("15432876-9", "Juan Soto", "Bobinador", "0.5000", "operario"),
    ("16789234-5", "Pedro Rojas", "Armador", "0.4500", None),
    ("17234568-9", "Maria Diaz", "Tecnica de ensayos", "0.5500", None),
]


class Command(BaseCommand):
    help = "Carga materiales, stock, tareas estandar, protocolos de calidad y empleados."

    @transaction.atomic
    def handle(self, *args, **options):
        Usuario = get_user_model()
        responsable = (Usuario.objects.filter(is_superuser=True).order_by("pk").first()
                       or Usuario.objects.filter(es_interno=True).order_by("pk").first())
        if responsable is None:
            self.stdout.write(self.style.ERROR(
                "No hay usuarios internos. Ejecute antes cargar_demo."))
            return

        bodega, _ = Bodega.objects.get_or_create(
            codigo="B1", defaults={"nombre": "Bodega central", "ubicacion": "Planta"}
        )

        materiales = {}
        for codigo, nombre, categoria, unidad, costo, minimo, inicial in MATERIALES:
            cat, _ = CategoriaMaterial.objects.get_or_create(nombre=categoria)
            material, _ = Material.objects.get_or_create(
                codigo=codigo,
                defaults={"categoria": cat, "nombre": nombre, "unidad_medida": unidad,
                          "stock_minimo": Decimal(minimo)},
            )
            if not material.precios.exists():
                PrecioMaterial.objects.create(material=material, costo_uf=Decimal(costo),
                                              vigente_desde=DESDE)
            if not material.movimientos.exists():
                MovimientoInventario.objects.create(
                    material=material, bodega=bodega, tipo=MovimientoInventario.Tipo.RECEPCION,
                    cantidad=Decimal(inicial), costo_unitario_uf=Decimal(costo),
                    usuario=responsable, observacion="Stock inicial de demostracion",
                )
            materiales[codigo] = material

        for modelo in ModeloProducto.objects.filter(codigo__in=ESCALA):
            factor = ESCALA[modelo.codigo]
            if not modelo.materiales.exists():
                for codigo, cantidad in BOM_BASE_100.items():
                    valor = Decimal(cantidad) * factor
                    if materiales[codigo].unidad_medida == "u":
                        valor = max(Decimal("1"), valor.to_integral_value())
                    BomModelo.objects.create(modelo=modelo, material=materiales[codigo],
                                             cantidad=valor)
            if not modelo.tareas_estandar.exists():
                for nombre, secuencia, horas in TAREAS_DEMO:
                    TareaEstandarModelo.objects.create(
                        modelo=modelo, nombre=nombre, secuencia=secuencia,
                        horas_estimadas=Decimal(horas),
                    )

        # Bases cargadas con versiones anteriores de este comando tenian horas
        # de taller reales (hasta 28 h por tarea): se acotan para las pruebas
        TareaEstandarModelo.objects.filter(
            modelo__codigo__in=ESCALA, horas_estimadas__gt=HORAS_MAXIMAS_DEMO
        ).update(horas_estimadas=HORAS_MAXIMAS_DEMO)
        acotadas = 0
        for tarea in TareaOT.objects.filter(
            orden_trabajo__estado__codigo__in=["planificada", "en_ejecucion"]
        ).select_related("orden_trabajo"):
            maximo = HORAS_MAXIMAS_DEMO * tarea.orden_trabajo.cantidad
            if tarea.horas_estimadas > maximo:
                tarea.horas_estimadas = maximo
                tarea.save(update_fields=["horas_estimadas"])
                acotadas += 1

        for modelo in ModeloProducto.objects.filter(codigo__in=ESCALA):
            if modelo.protocolos.exists():
                continue
            protocolo = ProtocoloCalidad.objects.create(
                modelo=modelo, nombre="Ensayos de rutina", norma_referencia="IEC 60076-1"
            )
            for secuencia, (nombre, unidad, nominal, minimo, maximo, obligatorio) in enumerate(
                ENSAYOS, start=1
            ):
                if maximo == "{perdidas}":
                    maximo = str(PERDIDAS_VACIO_W[modelo.codigo])
                PuntoControl.objects.create(
                    protocolo=protocolo, secuencia=secuencia, nombre=nombre,
                    tipo_ensayo="Rutina", unidad=unidad,
                    valor_esperado=Decimal(nominal) if nominal else None,
                    tolerancia_inf=Decimal(minimo) if minimo else None,
                    tolerancia_sup=Decimal(maximo) if maximo else None,
                    obligatorio=obligatorio,
                )

        empleados = []
        for rut, nombre, cargo, tarifa, username in EMPLEADOS:
            empleado, _ = Empleado.objects.get_or_create(
                rut=rut, defaults={"nombre": nombre, "cargo": cargo}
            )
            if not empleado.tarifas.exists():
                TarifaHoraHombre.objects.create(empleado=empleado, valor_hora_uf=Decimal(tarifa),
                                                vigente_desde=DESDE)
            if username and empleado.usuario_id is None:
                usuario = Usuario.objects.filter(username=username).first()
                if usuario and not hasattr(usuario, "empleado"):
                    empleado.usuario = usuario
                    empleado.save(update_fields=["usuario"])
            empleados.append(empleado)

        # Tareas sin responsable en ordenes ya existentes (la OT de cargar_demo)
        pendientes = TareaOT.objects.filter(
            empleado__isnull=True,
            orden_trabajo__estado__codigo__in=["planificada", "en_ejecucion"],
        ).order_by("orden_trabajo", "secuencia")
        for i, tarea in enumerate(pendientes):
            tarea.empleado = empleados[0] if "obinado" in tarea.nombre else empleados[i % 3]
            tarea.save(update_fields=["empleado"])

        # Las tareas terminadas de la demo no tenian horas: se registran en
        # jornadas pasadas de 8 horas, con la tarifa vigente del responsable
        fecha = timezone.localdate()
        historicas = TareaOT.objects.filter(
            estado=TareaOT.Estado.TERMINADA, registros_hora__isnull=True,
            empleado__isnull=False, orden_trabajo__estado__codigo="en_ejecucion",
        )
        for tarea in historicas:
            restantes = tarea.horas_estimadas
            while restantes > 0:
                fecha -= datetime.timedelta(days=1)
                horas = min(Decimal("8"), restantes)
                RegistroHoraHombre.objects.create(
                    tarea=tarea, empleado=tarea.empleado, fecha=fecha, horas=horas,
                    valor_hora_uf=tarea.empleado.tarifa_vigente_a(fecha).valor_hora_uf,
                    usuario_registro=responsable,
                )
                restantes -= horas

        # Recalcula costo y avance de todas las ordenes (el avance se mide por
        # tareas terminadas; las ordenes previas a ese cambio se actualizan aqui)
        for ot in OrdenTrabajo.objects.all():
            ot.recalcular_costo_real()
            ot.recalcular_avance()

        juan = empleados[0]
        self.stdout.write(self.style.SUCCESS(
            f"Materiales: {Material.objects.count()}. Empleados: {Empleado.objects.count()}. "
            f"Protocolos: {ProtocoloCalidad.objects.count()}. "
            f"Tareas acotadas a 2 h: {acotadas}. "
            f"Tareas asignadas: {len(pendientes)}."
        ))
        if juan.usuario_id:
            self.stdout.write(f"  El usuario '{juan.usuario.username}' registra como {juan.nombre}.")
        else:
            self.stdout.write(self.style.WARNING(
                "  No existe el usuario 'operario': ejecute cargar_roles --usuarios-demo "
                "y luego este comando otra vez."))
