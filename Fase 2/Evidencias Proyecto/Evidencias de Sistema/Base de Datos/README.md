# Base de datos — SITRAFO

Base de datos **relacional PostgreSQL 16**, normalizada en **tercera forma normal (3FN)**, con **54 tablas** del modelo de negocio (requisito minimo: 30).

| Archivo | Contenido |
|---|---|
| `esquema_sitrafo.sql` | Script DDL: tablas, claves primarias y foraneas, indices y restricciones. |
| `datos_demo.sql` | Datos de demostracion (catalogo, clientes, documentos, produccion, calidad, inventario). |
| `diccionario_datos.md` | Cada tabla con sus columnas, tipos, claves, restricciones y descripcion. |
| `README.md` | Este documento: normalizacion, diagramas entidad-relacion y restauracion. |

## Composicion

| Modulo | Tablas |
|---|---|
| Seguridad y auditoria | 6 |
| Clientes | 5 |
| Catalogo y recetas | 8 |
| Proceso comercial | 10 |
| Produccion | 7 |
| Control de calidad | 5 |
| Inventario | 6 |
| Cobros, pagos e indicadores | 3 |
| Configuracion e integraciones | 4 |
| **Total modelo de negocio** | **54** |

El esquema incluye ademas 9 tablas tecnicas del framework (sesiones, tipos de contenido, migraciones, permisos internos de Django y revocacion de tokens JWT), que no forman parte del modelo de negocio y no se contabilizan.

## Normalizacion

- **1FN:** todos los atributos son atomicos; los valores multiples (parametros tecnicos de un modelo, lineas de una cotizacion, tareas de una orden) estan en tablas propias.
- **2FN:** cada tabla tiene clave primaria simple (`id_...`); ningun atributo depende de una parte de una clave compuesta. Las relaciones muchos a muchos se resuelven con tablas intermedias con clave propia y restriccion unica: `usuario_rol`, `rol_permiso`, `modelo_parametro`, `bom_modelo`.
- **3FN:** no hay dependencias transitivas. Los datos de referencia viven en su tabla y se referencian por clave foranea: `region`/`comuna`, `familia_producto`, `estado_documento`, `categoria_material`, `parametro_tecnico`/`valor_parametro`.
- **Historial separado:** cada documento del flujo tiene su tabla de historial de estados (`solicitud_historial`, `cotizacion_historial`, `orden_compra_historial`, `orden_trabajo_historial`).
- **Valores versionados por vigencia:** precios de modelos (`precio_base_modelo`), precios de materiales (`precio_material`) y tarifas de hora hombre (`tarifa_hora_hombre`) con vigencia desde y hasta: los documentos historicos conservan el valor que regia.
- **Sin datos derivados almacenados en duplicado:** el stock se calcula desde `movimiento_inventario`; la UF y el monto en pesos se congelan en cada documento (RN-03) por requerimiento de negocio, no por duplicacion.
- **Integridad declarada en la base:** claves foraneas en todas las relaciones (el borrado de registros referenciados lo impide ademas la aplicacion, para no perder historia), restricciones `UNIQUE` (RUT, numeros de documento, codigos) y `CHECK` (por ejemplo, horas y cantidades positivas).

## Diagramas entidad-relacion por modulo

GitHub dibuja estos diagramas automaticamente. Se muestran hasta siete columnas por tabla; el detalle completo esta en `diccionario_datos.md`. Las tablas sin columnas pertenecen a otro modulo y aparecen solo para mostrar la relacion.

### Seguridad y auditoria

Relacionado con: `cliente`.

```mermaid
erDiagram
    rol ||--o{ rol_permiso : "id_rol"
    permiso ||--o{ rol_permiso : "id_permiso"
    cliente ||--o{ usuario : "id_cliente"
    usuario ||--o{ usuario_rol : "id_usuario"
    rol ||--o{ usuario_rol : "id_rol"
    usuario ||--o{ auditoria : "id_usuario"
    rol {
        boolean activo
        integer id_rol PK
        varchar nombre
        varchar descripcion
    }
    permiso {
        integer id_permiso PK
        varchar codigo
        varchar modulo
        varchar operacion
    }
    rol_permiso {
        bigint id PK
        integer id_rol FK
        integer id_permiso FK
        timestamp_with_time_zone otorgado_en
    }
    usuario {
        varchar password
        timestamp_with_time_zone last_login
        integer id_usuario PK
        varchar username
        varchar email
        integer id_cliente FK
        boolean es_interno
    }
    usuario_rol {
        bigint id PK
        integer id_usuario FK
        integer id_rol FK
        timestamp_with_time_zone asignado_en
    }
    auditoria {
        bigint id_auditoria PK
        integer id_usuario FK
        varchar entidad
        varchar id_registro
        varchar accion
        jsonb valor_anterior
        jsonb valor_nuevo
    }
```

### Clientes

```mermaid
erDiagram
    region ||--o{ comuna : "id_region"
    cliente ||--o{ contacto_cliente : "id_cliente"
    cliente ||--o{ direccion_cliente : "id_cliente"
    comuna ||--o{ direccion_cliente : "id_comuna"
    region {
        integer id_region PK
        varchar nombre
        varchar codigo
    }
    comuna {
        integer id_comuna PK
        integer id_region FK
        varchar nombre
    }
    cliente {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_cliente PK
        varchar rut
        varchar razon_social
        varchar nombre_fantasia
        varchar tipo_persona
    }
    contacto_cliente {
        integer id_contacto PK
        integer id_cliente FK
        varchar nombre
        varchar cargo
        varchar email
        varchar telefono
        boolean principal
    }
    direccion_cliente {
        integer id_direccion PK
        integer id_cliente FK
        integer id_comuna FK
        varchar tipo
        varchar calle
        varchar numero
        numeric latitud
    }
```

### Catalogo y recetas

Relacionado con: `empleado`, `material`, `usuario`.

```mermaid
erDiagram
    parametro_tecnico ||--o{ valor_parametro : "id_parametro"
    familia_producto ||--o{ modelo_producto : "id_familia"
    modelo_producto ||--o{ modelo_parametro : "id_modelo"
    parametro_tecnico ||--o{ modelo_parametro : "id_parametro"
    modelo_producto ||--o{ precio_base_modelo : "id_modelo"
    usuario ||--o{ precio_base_modelo : "id_usuario"
    modelo_producto ||--o{ bom_modelo : "id_modelo"
    material ||--o{ bom_modelo : "id_material"
    modelo_producto ||--o{ tarea_estandar_modelo : "id_modelo"
    empleado ||--o{ tarea_estandar_modelo : "id_empleado_sugerido"
    familia_producto {
        boolean activo
        integer id_familia PK
        varchar nombre
        varchar descripcion
    }
    parametro_tecnico {
        integer id_parametro PK
        varchar codigo
        varchar nombre
        varchar unidad
        varchar tipo_dato
        boolean obligatorio
    }
    valor_parametro {
        boolean activo
        integer id_valor PK
        integer id_parametro FK
        varchar valor
        smallint orden
    }
    modelo_producto {
        boolean activo
        integer id_modelo PK
        integer id_familia FK
        varchar codigo
        varchar nombre
        text descripcion
        boolean publicado
    }
    modelo_parametro {
        bigint id PK
        integer id_modelo FK
        integer id_parametro FK
        varchar valor_defecto
        boolean obligatorio
    }
    precio_base_modelo {
        date vigente_desde
        date vigente_hasta
        integer id_precio PK
        integer id_modelo FK
        numeric monto_uf
        integer id_usuario FK
    }
    bom_modelo {
        integer id_bom PK
        integer id_modelo FK
        integer id_material FK
        numeric cantidad
        varchar observacion
    }
    tarea_estandar_modelo {
        integer id_tarea_estandar PK
        integer id_modelo FK
        varchar nombre
        smallint secuencia
        numeric horas_estimadas
        integer id_empleado_sugerido FK
    }
```

### Proceso comercial

Relacionado con: `cliente`, `direccion_cliente`, `modelo_producto`, `parametro_tecnico`, `usuario`.

```mermaid
erDiagram
    cliente ||--o{ solicitud_presupuesto : "id_cliente"
    modelo_producto ||--o{ solicitud_presupuesto : "id_modelo"
    direccion_cliente ||--o{ solicitud_presupuesto : "id_direccion"
    estado_documento ||--o{ solicitud_presupuesto : "id_estado"
    usuario ||--o{ solicitud_presupuesto : "id_ejecutivo"
    solicitud_presupuesto ||--o{ solicitud_especificacion : "id_solicitud"
    parametro_tecnico ||--o{ solicitud_especificacion : "id_parametro"
    estado_documento ||--o{ solicitud_historial : "estado_anterior_id"
    estado_documento ||--o{ solicitud_historial : "estado_nuevo_id"
    usuario ||--o{ solicitud_historial : "usuario_id"
    solicitud_presupuesto ||--o{ solicitud_historial : "id_solicitud"
    solicitud_presupuesto ||--o{ cotizacion : "id_solicitud"
    cliente ||--o{ cotizacion : "id_cliente"
    estado_documento ||--o{ cotizacion : "id_estado"
    usuario ||--o{ cotizacion : "id_ejecutivo"
    cotizacion ||--o{ cotizacion_linea : "id_cotizacion"
    modelo_producto ||--o{ cotizacion_linea : "id_modelo"
    estado_documento ||--o{ cotizacion_historial : "estado_anterior_id"
    estado_documento ||--o{ cotizacion_historial : "estado_nuevo_id"
    usuario ||--o{ cotizacion_historial : "usuario_id"
    cotizacion ||--o{ cotizacion_historial : "id_cotizacion"
    cotizacion ||--o{ orden_compra : "id_cotizacion"
    cliente ||--o{ orden_compra : "id_cliente"
    estado_documento ||--o{ orden_compra : "id_estado"
    orden_compra ||--o{ orden_compra_linea : "id_orden_compra"
    cotizacion_linea ||--o{ orden_compra_linea : "id_cotizacion_linea"
    estado_documento ||--o{ orden_compra_historial : "estado_anterior_id"
    estado_documento ||--o{ orden_compra_historial : "estado_nuevo_id"
    usuario ||--o{ orden_compra_historial : "usuario_id"
    orden_compra ||--o{ orden_compra_historial : "id_orden_compra"
    estado_documento {
        integer id_estado PK
        varchar tipo_documento
        varchar codigo
        varchar nombre
        boolean es_final
    }
    solicitud_presupuesto {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_solicitud PK
        varchar numero
        integer id_cliente FK
        integer id_modelo FK
        integer id_direccion FK
    }
    solicitud_especificacion {
        bigint id PK
        integer id_solicitud FK
        integer id_parametro FK
        varchar valor
    }
    solicitud_historial {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer estado_anterior_id FK
        integer estado_nuevo_id FK
        integer usuario_id FK
        timestamp_with_time_zone fecha_hora
        varchar observacion
    }
    cotizacion {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_cotizacion PK
        varchar numero
        smallint version
        integer id_solicitud FK
        integer id_cliente FK
    }
    cotizacion_linea {
        integer id_linea PK
        integer id_cotizacion FK
        integer id_modelo FK
        integer cantidad
        numeric costo_material_uf
        numeric costo_hh_uf
        numeric margen_pct
    }
    cotizacion_historial {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer estado_anterior_id FK
        integer estado_nuevo_id FK
        integer usuario_id FK
        timestamp_with_time_zone fecha_hora
        varchar observacion
    }
    orden_compra {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_orden_compra PK
        varchar numero
        integer id_cotizacion FK
        integer id_cliente FK
        integer id_estado FK
    }
    orden_compra_linea {
        integer id_linea_oc PK
        integer id_orden_compra FK
        integer id_cotizacion_linea FK
        integer cantidad
        numeric precio_uf
    }
    orden_compra_historial {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer estado_anterior_id FK
        integer estado_nuevo_id FK
        integer usuario_id FK
        timestamp_with_time_zone fecha_hora
        varchar observacion
    }
```

### Produccion

Relacionado con: `bodega`, `estado_documento`, `material`, `modelo_producto`, `orden_compra`, `usuario`.

```mermaid
erDiagram
    usuario ||--o| empleado : "id_usuario"
    empleado ||--o{ tarifa_hora_hombre : "id_empleado"
    orden_compra ||--o{ orden_trabajo : "id_orden_compra"
    modelo_producto ||--o{ orden_trabajo : "id_modelo"
    estado_documento ||--o{ orden_trabajo : "id_estado"
    estado_documento ||--o{ orden_trabajo_historial : "estado_anterior_id"
    estado_documento ||--o{ orden_trabajo_historial : "estado_nuevo_id"
    usuario ||--o{ orden_trabajo_historial : "usuario_id"
    orden_trabajo ||--o{ orden_trabajo_historial : "id_orden_trabajo"
    orden_trabajo ||--o{ tarea_ot : "id_orden_trabajo"
    empleado ||--o{ tarea_ot : "id_empleado"
    tarea_ot ||--o{ consumo_material : "id_tarea"
    material ||--o{ consumo_material : "id_material"
    bodega ||--o{ consumo_material : "id_bodega"
    empleado ||--o{ consumo_material : "id_empleado"
    tarea_ot ||--o{ registro_hora_hombre : "id_tarea"
    empleado ||--o{ registro_hora_hombre : "id_empleado"
    usuario ||--o{ registro_hora_hombre : "id_usuario_registro"
    empleado {
        boolean activo
        integer id_empleado PK
        varchar rut
        varchar nombre
        varchar cargo
        integer id_usuario FK
    }
    tarifa_hora_hombre {
        integer id_tarifa PK
        integer id_empleado FK
        numeric valor_hora_uf
        date vigente_desde
        date vigente_hasta
    }
    orden_trabajo {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_orden_trabajo PK
        varchar numero
        integer id_orden_compra FK
        integer id_modelo FK
        integer cantidad
    }
    orden_trabajo_historial {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer estado_anterior_id FK
        integer estado_nuevo_id FK
        integer usuario_id FK
        timestamp_with_time_zone fecha_hora
        varchar observacion
    }
    tarea_ot {
        integer id_tarea PK
        integer id_orden_trabajo FK
        varchar nombre
        smallint secuencia
        numeric horas_estimadas
        varchar estado
        integer id_empleado FK
    }
    consumo_material {
        integer id_consumo PK
        integer id_tarea FK
        integer id_material FK
        integer id_bodega FK
        numeric cantidad
        numeric costo_unitario_uf
        boolean planificado
    }
    registro_hora_hombre {
        integer id_registro PK
        integer id_tarea FK
        integer id_empleado FK
        date fecha
        numeric horas
        numeric valor_hora_uf
        boolean anulado
    }
```

### Control de calidad

Relacionado con: `modelo_producto`, `orden_trabajo`, `usuario`.

```mermaid
erDiagram
    modelo_producto ||--o{ protocolo_calidad : "id_modelo"
    protocolo_calidad ||--o{ punto_control : "id_protocolo"
    orden_trabajo ||--o{ control_calidad : "id_orden_trabajo"
    protocolo_calidad ||--o{ control_calidad : "id_protocolo"
    usuario ||--o{ control_calidad : "id_inspector"
    control_calidad ||--o{ resultado_control : "id_control"
    punto_control ||--o{ resultado_control : "id_punto"
    resultado_control ||--o| no_conformidad : "id_resultado"
    usuario ||--o{ no_conformidad : "id_responsable"
    usuario ||--o{ no_conformidad : "id_usuario_cierre"
    protocolo_calidad {
        boolean activo
        integer id_protocolo PK
        integer id_modelo FK
        varchar nombre
        smallint version
        varchar norma_referencia
    }
    punto_control {
        integer id_punto PK
        integer id_protocolo FK
        varchar nombre
        varchar tipo_ensayo
        varchar unidad
        numeric valor_esperado
        numeric tolerancia_inf
    }
    control_calidad {
        integer id_control PK
        integer id_orden_trabajo FK
        integer id_protocolo FK
        integer id_inspector FK
        timestamp_with_time_zone fecha_hora
        varchar estado
        varchar observacion
    }
    resultado_control {
        integer id_resultado PK
        integer id_control FK
        integer id_punto FK
        numeric valor_medido
        boolean conforme
        varchar observacion
        timestamp_with_time_zone registrado_en
    }
    no_conformidad {
        integer id_no_conformidad PK
        integer id_resultado FK
        varchar descripcion
        varchar severidad
        integer id_responsable FK
        text accion_correctiva
        varchar estado
    }
```

### Inventario

Relacionado con: `consumo_material`, `usuario`.

```mermaid
erDiagram
    categoria_material ||--o{ material : "id_categoria"
    material ||--o{ precio_material : "id_material"
    proveedor ||--o{ precio_material : "id_proveedor"
    material ||--o{ movimiento_inventario : "id_material"
    bodega ||--o{ movimiento_inventario : "id_bodega"
    proveedor ||--o{ movimiento_inventario : "id_proveedor"
    consumo_material ||--o| movimiento_inventario : "id_consumo"
    usuario ||--o{ movimiento_inventario : "id_usuario"
    categoria_material {
        boolean activo
        integer id_categoria PK
        varchar nombre
    }
    material {
        boolean activo
        integer id_material PK
        integer id_categoria FK
        varchar codigo
        varchar nombre
        varchar unidad_medida
        numeric stock_minimo
    }
    proveedor {
        boolean activo
        integer id_proveedor PK
        varchar rut
        varchar razon_social
        varchar email
        varchar telefono
    }
    bodega {
        boolean activo
        integer id_bodega PK
        varchar codigo
        varchar nombre
        varchar ubicacion
    }
    precio_material {
        date vigente_desde
        date vigente_hasta
        integer id_precio_material PK
        integer id_material FK
        integer id_proveedor FK
        numeric costo_uf
    }
    movimiento_inventario {
        bigint id_movimiento PK
        integer id_material FK
        integer id_bodega FK
        varchar tipo
        numeric cantidad
        numeric costo_unitario_uf
        integer id_proveedor FK
    }
```

### Cobros, pagos e indicadores

Relacionado con: `orden_compra`.

```mermaid
erDiagram
    orden_compra ||--o{ documento_cobro : "id_orden_compra"
    documento_cobro ||--o{ transaccion_pago : "id_documento_cobro"
    indicador_economico {
        integer id_indicador PK
        varchar codigo
        date fecha
        numeric valor
        timestamp_with_time_zone obtenido_en
    }
    documento_cobro {
        integer id_documento_cobro PK
        varchar numero
        integer id_orden_compra FK
        varchar tipo
        numeric monto_uf
        numeric valor_uf
        numeric monto_clp
    }
    transaccion_pago {
        integer id_transaccion PK
        integer id_documento_cobro FK
        varchar id_externo
        varchar pasarela
        numeric monto
        varchar moneda
        varchar estado
    }
```

### Configuracion e integraciones

Relacionado con: `usuario`.

```mermaid
erDiagram
    usuario ||--o{ parametro_sistema : "id_usuario"
    usuario ||--o{ aviso_sitio : "id_usuario"
    parametro_sistema {
        integer id_parametro_sistema PK
        varchar clave
        varchar valor
        varchar tipo_dato
        varchar ambito
        varchar descripcion
        integer id_usuario FK
    }
    aviso_sitio {
        integer id_aviso PK
        varchar titulo
        text cuerpo
        varchar tipo
        timestamp_with_time_zone vigente_desde
        timestamp_with_time_zone vigente_hasta
        boolean activo
    }
    feriado {
        integer id_feriado PK
        date fecha
        varchar nombre
        varchar tipo
        timestamp_with_time_zone obtenido_en
    }
    log_integracion {
        bigint id_log PK
        varchar servicio
        varchar endpoint
        varchar metodo
        smallint codigo_respuesta
        integer latencia_ms
        boolean exitoso
    }
```

## Restaurar la base

Con PostgreSQL 16 y una base vacia:

```bash
psql -U <usuario> -d <base> -f esquema_sitrafo.sql
psql -U <usuario> -d <base> -f datos_demo.sql
```

Con el proyecto en Docker, la forma recomendada es crear el esquema con las migraciones del sistema, que generan exactamente este mismo DDL:

```bash
docker compose exec web python manage.py migrate
```

Los datos de demostracion no contienen informacion real: las cuentas personales tienen la clave deshabilitada, y se omitieron sesiones, tokens e historial del administrador.
