# Base de datos — SITRAFO

Base de datos **relacional PostgreSQL 16**, normalizada en **tercera forma normal (3FN)**, con **54 tablas** del modelo de negocio (requisito minimo: 30). Corresponde al **MER-01 v2.1** y al codigo actual del repositorio (todas las migraciones aplicadas).

| Archivo | Contenido |
|---|---|
| `esquema_sitrafo.sql` | Script DDL: tablas, claves primarias y foraneas, indices y restricciones. |
| `datos_demo.sql` | Datos de demostracion: catalogo, cliente, dos pedidos completos (ver abajo), inventario, calidad, cobros, indicadores y feriados. |
| `diccionario_datos.md` | Cada tabla con sus columnas, tipos, claves, restricciones y descripcion. |
| `README.md` | Este documento: composicion, normalizacion, diagramas entidad-relacion, datos y restauracion. |

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
- **Parametros de negocio en tabla:** anticipo, umbrales de descuento y de desviacion, vigencia, tope de unidades y horas diarias viven en `parametro_sistema` con su rango permitido, y se editan sin redesplegar.
- **Integridad declarada en la base:** claves foraneas en todas las relaciones (el borrado de registros referenciados lo impide ademas la aplicacion, para no perder historia), restricciones `UNIQUE` (RUT, numeros de documento, codigos) y `CHECK` (por ejemplo, horas y cantidades positivas).

## Diagramas entidad-relacion por modulo

GitHub dibuja estos diagramas automaticamente. Se muestran hasta siete columnas por tabla; el detalle completo esta en `diccionario_datos.md`. Las tablas sin columnas pertenecen a otro modulo y aparecen solo para mostrar la relacion.

### Seguridad y auditoria

Relacionado con: `cliente`.

```mermaid
erDiagram
    usuario ||--o{ auditoria : "id_usuario"
    rol ||--o{ rol_permiso : "id_rol"
    permiso ||--o{ rol_permiso : "id_permiso"
    cliente ||--o{ usuario : "id_cliente"
    usuario ||--o{ usuario_rol : "id_usuario"
    rol ||--o{ usuario_rol : "id_rol"
    auditoria {
        bigint id_auditoria PK
        integer id_usuario FK
        varchar entidad
        varchar id_registro
        varchar accion
        jsonb valor_anterior
        jsonb valor_nuevo
    }
    permiso {
        integer id_permiso PK
        varchar codigo
        varchar modulo
        varchar operacion
    }
    rol {
        boolean activo
        integer id_rol PK
        varchar nombre
        varchar descripcion
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
```

### Clientes

```mermaid
erDiagram
    region ||--o{ comuna : "id_region"
    cliente ||--o{ contacto_cliente : "id_cliente"
    cliente ||--o{ direccion_cliente : "id_cliente"
    comuna ||--o{ direccion_cliente : "id_comuna"
    cliente {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_cliente PK
        varchar rut
        varchar razon_social
        varchar nombre_fantasia
        varchar tipo_persona
    }
    comuna {
        integer id_comuna PK
        integer id_region FK
        varchar nombre
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
    region {
        integer id_region PK
        varchar nombre
        varchar codigo
    }
```

### Catalogo y recetas

Relacionado con: `empleado`, `material`, `usuario`.

```mermaid
erDiagram
    modelo_producto ||--o{ bom_modelo : "id_modelo"
    material ||--o{ bom_modelo : "id_material"
    modelo_producto ||--o{ modelo_parametro : "id_modelo"
    parametro_tecnico ||--o{ modelo_parametro : "id_parametro"
    familia_producto ||--o{ modelo_producto : "id_familia"
    modelo_producto ||--o{ precio_base_modelo : "id_modelo"
    usuario ||--o{ precio_base_modelo : "id_usuario"
    modelo_producto ||--o{ tarea_estandar_modelo : "id_modelo"
    empleado ||--o{ tarea_estandar_modelo : "id_empleado_sugerido"
    parametro_tecnico ||--o{ valor_parametro : "id_parametro"
    bom_modelo {
        integer id_bom PK
        integer id_modelo FK
        integer id_material FK
        numeric cantidad
        varchar observacion
    }
    familia_producto {
        boolean activo
        integer id_familia PK
        varchar nombre
        varchar descripcion
    }
    modelo_parametro {
        bigint id PK
        integer id_modelo FK
        integer id_parametro FK
        varchar valor_defecto
        boolean obligatorio
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
    parametro_tecnico {
        integer id_parametro PK
        varchar codigo
        varchar nombre
        varchar unidad
        varchar tipo_dato
        boolean obligatorio
        numeric valor_minimo
    }
    precio_base_modelo {
        date vigente_desde
        date vigente_hasta
        integer id_precio PK
        integer id_modelo FK
        numeric monto_uf
        integer id_usuario FK
    }
    tarea_estandar_modelo {
        integer id_tarea_estandar PK
        integer id_modelo FK
        varchar nombre
        smallint secuencia
        numeric horas_estimadas
        integer id_empleado_sugerido FK
    }
    valor_parametro {
        boolean activo
        integer id_valor PK
        integer id_parametro FK
        varchar valor
        smallint orden
    }
```

### Proceso comercial

Relacionado con: `cliente`, `direccion_cliente`, `modelo_producto`, `parametro_tecnico`, `usuario`.

```mermaid
erDiagram
    solicitud_presupuesto ||--o{ cotizacion : "id_solicitud"
    cliente ||--o{ cotizacion : "id_cliente"
    estado_documento ||--o{ cotizacion : "id_estado"
    usuario ||--o{ cotizacion : "id_ejecutivo"
    estado_documento ||--o{ cotizacion_historial : "estado_anterior_id"
    estado_documento ||--o{ cotizacion_historial : "estado_nuevo_id"
    usuario ||--o{ cotizacion_historial : "usuario_id"
    cotizacion ||--o{ cotizacion_historial : "id_cotizacion"
    cotizacion ||--o{ cotizacion_linea : "id_cotizacion"
    modelo_producto ||--o{ cotizacion_linea : "id_modelo"
    cotizacion ||--o{ orden_compra : "id_cotizacion"
    cliente ||--o{ orden_compra : "id_cliente"
    estado_documento ||--o{ orden_compra : "id_estado"
    estado_documento ||--o{ orden_compra_historial : "estado_anterior_id"
    estado_documento ||--o{ orden_compra_historial : "estado_nuevo_id"
    usuario ||--o{ orden_compra_historial : "usuario_id"
    orden_compra ||--o{ orden_compra_historial : "id_orden_compra"
    orden_compra ||--o{ orden_compra_linea : "id_orden_compra"
    cotizacion_linea ||--o{ orden_compra_linea : "id_cotizacion_linea"
    solicitud_presupuesto ||--o{ solicitud_especificacion : "id_solicitud"
    parametro_tecnico ||--o{ solicitud_especificacion : "id_parametro"
    estado_documento ||--o{ solicitud_historial : "estado_anterior_id"
    estado_documento ||--o{ solicitud_historial : "estado_nuevo_id"
    usuario ||--o{ solicitud_historial : "usuario_id"
    solicitud_presupuesto ||--o{ solicitud_historial : "id_solicitud"
    cliente ||--o{ solicitud_presupuesto : "id_cliente"
    modelo_producto ||--o{ solicitud_presupuesto : "id_modelo"
    direccion_cliente ||--o{ solicitud_presupuesto : "id_direccion"
    estado_documento ||--o{ solicitud_presupuesto : "id_estado"
    usuario ||--o{ solicitud_presupuesto : "id_ejecutivo"
    cotizacion {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_cotizacion PK
        varchar numero
        smallint version
        integer id_solicitud FK
        integer id_cliente FK
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
    cotizacion_linea {
        integer id_linea PK
        integer id_cotizacion FK
        integer id_modelo FK
        integer cantidad
        numeric costo_material_uf
        numeric costo_hh_uf
        numeric margen_pct
    }
    estado_documento {
        integer id_estado PK
        varchar tipo_documento
        varchar codigo
        varchar nombre
        boolean es_final
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
    orden_compra_historial {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer estado_anterior_id FK
        integer estado_nuevo_id FK
        integer usuario_id FK
        timestamp_with_time_zone fecha_hora
        varchar observacion
    }
    orden_compra_linea {
        integer id_linea_oc PK
        integer id_orden_compra FK
        integer id_cotizacion_linea FK
        integer cantidad
        numeric precio_uf
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
    solicitud_presupuesto {
        timestamp_with_time_zone creado_en
        timestamp_with_time_zone modificado_en
        integer id_solicitud PK
        varchar numero
        integer id_cliente FK
        integer id_modelo FK
        integer id_direccion FK
    }
```

### Produccion

Relacionado con: `bodega`, `estado_documento`, `material`, `modelo_producto`, `orden_compra`, `usuario`.

```mermaid
erDiagram
    tarea_ot ||--o{ consumo_material : "id_tarea"
    material ||--o{ consumo_material : "id_material"
    bodega ||--o{ consumo_material : "id_bodega"
    empleado ||--o{ consumo_material : "id_empleado"
    usuario ||--|| empleado : "id_usuario"
    orden_compra ||--o{ orden_trabajo : "id_orden_compra"
    modelo_producto ||--o{ orden_trabajo : "id_modelo"
    estado_documento ||--o{ orden_trabajo : "id_estado"
    estado_documento ||--o{ orden_trabajo_historial : "estado_anterior_id"
    estado_documento ||--o{ orden_trabajo_historial : "estado_nuevo_id"
    usuario ||--o{ orden_trabajo_historial : "usuario_id"
    orden_trabajo ||--o{ orden_trabajo_historial : "id_orden_trabajo"
    tarea_ot ||--o{ registro_hora_hombre : "id_tarea"
    empleado ||--o{ registro_hora_hombre : "id_empleado"
    usuario ||--o{ registro_hora_hombre : "id_usuario_registro"
    orden_trabajo ||--o{ tarea_ot : "id_orden_trabajo"
    empleado ||--o{ tarea_ot : "id_empleado"
    empleado ||--o{ tarifa_hora_hombre : "id_empleado"
    consumo_material {
        integer id_consumo PK
        integer id_tarea FK
        integer id_material FK
        integer id_bodega FK
        numeric cantidad
        numeric costo_unitario_uf
        boolean planificado
    }
    empleado {
        boolean activo
        integer id_empleado PK
        varchar rut
        varchar nombre
        varchar cargo
        integer id_usuario FK
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
    registro_hora_hombre {
        integer id_registro PK
        integer id_tarea FK
        integer id_empleado FK
        date fecha
        numeric horas
        numeric valor_hora_uf
        boolean anulado
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
    tarifa_hora_hombre {
        integer id_tarifa PK
        integer id_empleado FK
        numeric valor_hora_uf
        date vigente_desde
        date vigente_hasta
    }
```

### Control de calidad

Relacionado con: `modelo_producto`, `orden_trabajo`, `usuario`.

```mermaid
erDiagram
    orden_trabajo ||--o{ control_calidad : "id_orden_trabajo"
    protocolo_calidad ||--o{ control_calidad : "id_protocolo"
    usuario ||--o{ control_calidad : "id_inspector"
    usuario ||--o{ control_calidad : "id_aprobado_por"
    resultado_control ||--|| no_conformidad : "id_resultado"
    usuario ||--o{ no_conformidad : "id_responsable"
    usuario ||--o{ no_conformidad : "id_usuario_cierre"
    modelo_producto ||--o{ protocolo_calidad : "id_modelo"
    protocolo_calidad ||--o{ punto_control : "id_protocolo"
    control_calidad ||--o{ resultado_control : "id_control"
    punto_control ||--o{ resultado_control : "id_punto"
    control_calidad {
        integer id_control PK
        integer id_orden_trabajo FK
        integer id_protocolo FK
        integer id_inspector FK
        timestamp_with_time_zone fecha_hora
        varchar estado
        varchar observacion
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
    resultado_control {
        integer id_resultado PK
        integer id_control FK
        integer id_punto FK
        numeric valor_medido
        boolean conforme
        varchar observacion
        timestamp_with_time_zone registrado_en
    }
```

### Inventario

Relacionado con: `consumo_material`, `usuario`.

```mermaid
erDiagram
    categoria_material ||--o{ material : "id_categoria"
    material ||--o{ movimiento_inventario : "id_material"
    bodega ||--o{ movimiento_inventario : "id_bodega"
    proveedor ||--o{ movimiento_inventario : "id_proveedor"
    consumo_material ||--|| movimiento_inventario : "id_consumo"
    usuario ||--o{ movimiento_inventario : "id_usuario"
    material ||--o{ precio_material : "id_material"
    proveedor ||--o{ precio_material : "id_proveedor"
    bodega {
        boolean activo
        integer id_bodega PK
        varchar codigo
        varchar nombre
        varchar ubicacion
    }
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
    movimiento_inventario {
        bigint id_movimiento PK
        integer id_material FK
        integer id_bodega FK
        varchar tipo
        numeric cantidad
        numeric costo_unitario_uf
        integer id_proveedor FK
    }
    precio_material {
        date vigente_desde
        date vigente_hasta
        integer id_precio_material PK
        integer id_material FK
        integer id_proveedor FK
        numeric costo_uf
    }
    proveedor {
        boolean activo
        integer id_proveedor PK
        varchar rut
        varchar razon_social
        varchar email
        varchar telefono
    }
```

### Cobros, pagos e indicadores

Relacionado con: `orden_compra`.

```mermaid
erDiagram
    orden_compra ||--o{ documento_cobro : "id_orden_compra"
    documento_cobro ||--o{ transaccion_pago : "id_documento_cobro"
    documento_cobro {
        integer id_documento_cobro PK
        varchar numero
        integer id_orden_compra FK
        varchar tipo
        numeric monto_uf
        numeric valor_uf
        numeric monto_clp
    }
    indicador_economico {
        integer id_indicador PK
        varchar codigo
        date fecha
        numeric valor
        timestamp_with_time_zone obtenido_en
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
    usuario ||--o{ aviso_sitio : "id_usuario"
    usuario ||--o{ parametro_sistema : "id_usuario"
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
    parametro_sistema {
        integer id_parametro_sistema PK
        varchar clave
        varchar valor
        varchar tipo_dato
        varchar ambito
        varchar descripcion
        integer id_usuario FK
    }
```

## Datos de demostracion

`datos_demo.sql` se genero con los comandos de carga del sistema (`cargar_estados`, `cargar_parametros`, `cargar_roles --usuarios-demo`, `cargar_demo` y `cargar_demo_produccion`) y luego recorriendo el proceso con los mismos servicios y la misma API que usan la web y la aplicacion de escritorio. Contiene:

- **OC-2026-0001**, ciclo completo: anticipo pagado, orden de trabajo con horas y consumo de materiales, control de calidad con una no conformidad (corriente de vacio fuera de rango) cerrada con accion correctiva y ensayo repetido, aprobacion del inspector (orden liberada), cierre con desviacion justificada (RN-11), saldo emitido y pagado, y entrega registrada.
- **OC-2026-0002**, en produccion: solicitud desde el portal, cotizacion con 12 % de descuento que supero el umbral y fue aprobada y emitida por otro ejecutivo (RN-05), aceptacion del cliente, anticipo pagado y orden de trabajo generada e iniciada.
- **SP-2026-0002** recibida y **COT-2026-0001** emitida, pendientes de atender.
- Recepcion de compra en bodega, un aviso del sitio y el contacto principal del cliente.
- **Indicadores** UF, dolar observado y UTM con los valores publicados por mindicador.cl al 10-10-2026, y **feriados** legales de Chile 2026. En el sistema desplegado ambos los obtiene la tarea diaria; aqui se cargaron con esos valores porque el entorno de generacion no tenia acceso a esos servicios.

Filas por tabla en los datos de demostracion:

| Tabla | Filas | Tabla | Filas | Tabla | Filas |
|---|---:|---|---:|---|---:|
| `auditoria` | 6 | `aviso_sitio` | 1 | `bodega` | 1 |
| `bom_modelo` | 24 | `categoria_material` | 5 | `cliente` | 1 |
| `comuna` | 346 | `consumo_material` | 6 | `contacto_cliente` | 1 |
| `control_calidad` | 1 | `cotizacion` | 3 | `cotizacion_historial` | 7 |
| `cotizacion_linea` | 3 | `direccion_cliente` | 1 | `documento_cobro` | 3 |
| `empleado` | 3 | `estado_documento` | 22 | `familia_producto` | 2 |
| `feriado` | 16 | `indicador_economico` | 3 | `log_integracion` | 0 |
| `material` | 6 | `modelo_parametro` | 20 | `modelo_producto` | 4 |
| `movimiento_inventario` | 13 | `no_conformidad` | 1 | `orden_compra` | 2 |
| `orden_compra_historial` | 4 | `orden_compra_linea` | 2 | `orden_trabajo` | 2 |
| `orden_trabajo_historial` | 7 | `parametro_sistema` | 15 | `parametro_tecnico` | 5 |
| `permiso` | 93 | `precio_base_modelo` | 3 | `precio_material` | 6 |
| `protocolo_calidad` | 4 | `proveedor` | 2 | `punto_control` | 32 |
| `region` | 16 | `registro_hora_hombre` | 6 | `resultado_control` | 9 |
| `rol` | 6 | `rol_permiso` | 140 | `solicitud_especificacion` | 9 |
| `solicitud_historial` | 4 | `solicitud_presupuesto` | 3 | `tarea_estandar_modelo` | 20 |
| `tarea_ot` | 10 | `tarifa_hora_hombre` | 3 | `transaccion_pago` | 3 |
| `usuario` | 9 | `usuario_rol` | 7 | `valor_parametro` | 10 |

Consideraciones de privacidad y honestidad de los datos:

- No contiene informacion personal: el cliente, sus contactos y los empleados son ficticios, y los correos usan dominios de demostracion.
- **Todas las cuentas tienen la clave deshabilitada** (no se publica ningun hash de contrasena). Despues de restaurar, asigne claves con `python manage.py changepassword <usuario>` o vuelva a ejecutar `cargar_roles --usuarios-demo`.
- **Los pagos son simulados:** se registraron con el doble de prueba de PayPal que usan las pruebas automatizadas, por lo que sus identificadores llevan el prefijo `DEMO-SIM`. No corresponden a transacciones del sandbox de PayPal. Por lo mismo, `log_integracion` va vacia: no se publican como reales llamadas externas que no ocurrieron.
- Se omitieron sesiones, tokens JWT y el historial del administrador de Django.

## Restaurar la base

Con PostgreSQL 16 y una base vacia:

```bash
psql -U <usuario> -d <base> -f esquema_sitrafo.sql
psql -U <usuario> -d <base> -f datos_demo.sql
```

Se verifico restaurando ambos archivos en una base vacia: cargan sin errores, con las mismas filas que la base de origen, y `python manage.py migrate --check` confirma que no quedan migraciones pendientes.

Con el proyecto en Docker, la forma recomendada es crear el esquema con las migraciones del sistema, que generan exactamente este mismo DDL:

```bash
docker compose exec web python manage.py migrate
```
