"""
Matriz de acceso por rol (RF-SEG-02, RN-18).

Transcribe la seccion 8.2 del documento ERS-01. Cada fila de la matriz es un
modulo; cada rol tiene sobre el modulo acceso de operacion (O), de solo
lectura (L) o ninguno (se omite).

- O otorga leer, crear, actualizar y anular sobre el modulo.
- L otorga solo leer.
- Algunos modulos tienen operaciones especiales (por ejemplo
  cotizacion.aprobar), que se otorgan solo a los roles indicados.

La matriz se carga con `python manage.py cargar_roles` y luego es
configurable desde la administracion: el codigo no lee esta constante para
autorizar, lee la tabla rol_permiso.
"""

ADMIN = "Administrador"
COMERCIAL = "Ejecutivo comercial"
PRODUCCION = "Jefe de produccion"
OPERARIO = "Operario de taller"
CALIDAD = "Inspector de calidad"
BODEGA = "Encargado de bodega"

ROLES = {
    ADMIN: "Usuarios, roles, auditoria, parametros, catalogo, precios, "
           "empleados y canal web.",
    COMERCIAL: "Clientes, solicitudes, cotizaciones y ordenes de compra.",
    PRODUCCION: "Listas de materiales, ordenes de trabajo y registro en taller.",
    OPERARIO: "Registro de horas hombre y consumo de materiales en taller.",
    CALIDAD: "Protocolos, ensayos y no conformidades.",
    BODEGA: "Materiales, proveedores, bodegas, movimientos y kardex.",
}

O, L = "O", "L"  # noqa: E741 (operacion y lectura, como en la ERS)

# modulo: (descripcion, {rol: acceso}, {operacion_especial: [roles]})
MATRIZ = {
    "usuario": ("Usuarios y roles", {ADMIN: O}, {}),
    "rol": ("Matriz de permisos", {ADMIN: O}, {}),
    "auditoria": ("Bitacora de auditoria", {ADMIN: L}, {}),
    "parametro": ("Parametros del sistema e integraciones", {ADMIN: O}, {}),
    "cliente": ("Clientes, contactos y direcciones",
                {ADMIN: L, COMERCIAL: O, PRODUCCION: L}, {}),
    "catalogo": ("Catalogo: familias, modelos y parametros tecnicos",
                 {ADMIN: O, COMERCIAL: L, PRODUCCION: L, CALIDAD: L}, {}),
    "bom": ("Lista de materiales y tareas estandar",
            {ADMIN: L, COMERCIAL: L, PRODUCCION: O, BODEGA: L}, {}),
    "precio": ("Precios base y vigencias", {ADMIN: O, COMERCIAL: L}, {}),
    "solicitud": ("Bandeja de solicitudes de presupuesto",
                  {ADMIN: L, COMERCIAL: O, PRODUCCION: L}, {}),
    "cotizacion": ("Editor y aprobacion de cotizaciones",
                   {COMERCIAL: O, PRODUCCION: L}, {"aprobar": [COMERCIAL]}),
    "orden_compra": ("Ordenes de compra",
                     {ADMIN: L, COMERCIAL: O, PRODUCCION: L}, {}),
    "orden_trabajo": ("Ordenes de trabajo y planificacion",
                      {ADMIN: L, COMERCIAL: L, PRODUCCION: O, OPERARIO: L,
                       CALIDAD: L, BODEGA: L}, {}),
    "taller": ("Registro de horas y consumos", {PRODUCCION: O, OPERARIO: O}, {}),
    "protocolo_calidad": ("Protocolos de calidad",
                          {ADMIN: L, PRODUCCION: L, CALIDAD: O}, {}),
    "ensayo": ("Ejecucion de ensayos", {PRODUCCION: L, CALIDAD: O}, {}),
    "no_conformidad": ("No conformidades",
                       {ADMIN: L, COMERCIAL: L, PRODUCCION: L, CALIDAD: O}, {}),
    "material": ("Materiales y proveedores",
                 {ADMIN: L, PRODUCCION: L, BODEGA: O}, {}),
    "bodega": ("Bodegas y movimientos", {PRODUCCION: L, BODEGA: O}, {}),
    "kardex": ("Kardex y alertas de stock", {ADMIN: L, PRODUCCION: L, BODEGA: O}, {}),
    "empleado": ("Empleados, cargos y tarifas", {ADMIN: O, PRODUCCION: L}, {}),
    "canal_web": ("Administracion del canal web", {ADMIN: O, COMERCIAL: L}, {}),
    "cuenta_web": ("Cuentas de cliente web", {ADMIN: O, COMERCIAL: O}, {}),
    "reporte": ("Reportes",
                {ADMIN: O, COMERCIAL: O, PRODUCCION: O, CALIDAD: L, BODEGA: L}, {}),
}

OPERACIONES = ["leer", "crear", "actualizar", "anular"]


def permisos_de_rol(rol: str) -> set[str]:
    """Codigos de permiso que la matriz otorga a un rol."""
    codigos = set()
    for modulo, (_, accesos, especiales) in MATRIZ.items():
        acceso = accesos.get(rol)
        if acceso == O:
            codigos.update(f"{modulo}.{op}" for op in OPERACIONES)
        elif acceso == L:
            codigos.add(f"{modulo}.leer")
        for operacion, roles in especiales.items():
            if rol in roles:
                codigos.add(f"{modulo}.{operacion}")
    return codigos


def todos_los_permisos() -> list[tuple[str, str, str]]:
    """(codigo, modulo, operacion) de todos los permisos de la matriz."""
    resultado = []
    for modulo, (_, _, especiales) in MATRIZ.items():
        for op in OPERACIONES:
            resultado.append((f"{modulo}.{op}", modulo, op))
        for especial in especiales:
            # Las operaciones especiales se clasifican como actualizacion
            resultado.append((f"{modulo}.{especial}", modulo, "actualizar"))
    return resultado
