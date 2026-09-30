# Diccionario de datos — SITRAFO

Base de datos relacional PostgreSQL 16. **54 tablas** del modelo de negocio, agrupadas por modulo. Generado desde los modelos del sistema, por lo que coincide exactamente con el esquema implementado.

Convenciones: **PK** clave primaria · **FK** clave foranea (tabla referenciada) · **UQ** valor unico · Nulo: *si* admite vacio.

## Seguridad y auditoria (6 tablas)

### `auditoria`

Bitacora de operaciones sobre entidades sensibles.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_auditoria` | bigint | no | PK | Id auditoria |
| `id_usuario` | integer | no | FK → usuario | Usuario |
| `entidad` | varchar(60) | no |  | Entidad afectada |
| `id_registro` | varchar(40) | no |  | Id del registro |
| `accion` | varchar(20) | no |  | Accion. Valores: creacion, modificacion, anulacion, acceso_denegado. |
| `valor_anterior` | jsonb | si |  | Valor anterior |
| `valor_nuevo` | jsonb | si |  | Valor nuevo |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `origen` | varchar(40) | no |  | Origen. Valores: escritorio, web, sistema. |

### `permiso`

Operacion atomica sobre un modulo. Unidad minima de autorizacion.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_permiso` | integer | no | PK | Id permiso |
| `codigo` | varchar(80) | no | UQ | Codigo |
| `modulo` | varchar(40) | no |  | Modulo |
| `operacion` | varchar(20) | no |  | Operacion. Valores: crear, leer, actualizar, anular. |

### `rol`

Perfil de acceso al que se asocian permisos (RF-SEG-02).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_rol` | integer | no | PK | Id rol |
| `nombre` | varchar(60) | no | UQ | Nombre |
| `descripcion` | varchar(200) | no |  | Descripcion |

### `rol_permiso`

Matriz de permisos por rol (RF-SEG-02).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id` | bigint | no | PK | Id |
| `id_rol` | integer | no | FK → rol | Rol |
| `id_permiso` | integer | no | FK → permiso | Permiso |
| `otorgado_en` | timestamp with time zone | no |  | Otorgado en |

Restricciones: UNIQUE (rol, permiso).

### `usuario`

Credencial de acceso al sistema.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `password` | varchar(128) | no |  | Contraseña |
| `last_login` | timestamp with time zone | si |  | Último inicio de sesión |
| `id_usuario` | integer | no | PK | Id usuario |
| `username` | varchar(60) | no | UQ | Nombre de acceso |
| `email` | varchar(150) | no | UQ | Correo electronico |
| `id_cliente` | integer | si | FK → cliente | Cliente asociado. Solo para cuentas web de cliente. Nulo en usuarios internos. |
| `es_interno` | boolean | no |  | Es usuario interno |
| `estado` | varchar(20) | no |  | Estado. Valores: activo, suspendido, bloqueado. |
| `intentos_fallidos` | smallint | no |  | Intentos fallidos consecutivos |
| `ultimo_acceso` | timestamp with time zone | si |  | Ultimo acceso exitoso |
| `bloqueado_hasta` | timestamp with time zone | si |  | Bloqueado hasta. Fin del bloqueo temporal por intentos fallidos (RF-SEG-04). |
| `is_staff` | boolean | no |  | Acceso al admin |
| `is_superuser` | boolean | no |  | Superusuario |
| `is_active` | boolean | no |  | Cuenta habilitada |
| `creado_en` | timestamp with time zone | no |  | Creado en |

### `usuario_rol`

Asignacion de roles a usuarios.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id` | bigint | no | PK | Id |
| `id_usuario` | integer | no | FK → usuario | Usuario |
| `id_rol` | integer | no | FK → rol | Rol |
| `asignado_en` | timestamp with time zone | no |  | Asignado en |

Restricciones: UNIQUE (usuario, rol).

## Clientes (5 tablas)

### `cliente`

Persona natural o juridica que solicita cotizaciones (RF-CLI-01).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `id_cliente` | integer | no | PK | Id cliente |
| `rut` | varchar(12) | no | UQ | Rut |
| `razon_social` | varchar(150) | no |  | Razon social |
| `nombre_fantasia` | varchar(150) | no |  | Nombre de fantasia |
| `tipo_persona` | varchar(10) | no |  | Tipo de persona. Valores: natural, juridica. |
| `giro` | varchar(150) | no |  | Giro |
| `estado` | varchar(20) | no |  | Estado. Valores: activo, inactivo. |

### `comuna`

Division administrativa menor.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_comuna` | integer | no | PK | Id comuna |
| `id_region` | integer | no | FK → region | Region |
| `nombre` | varchar(80) | no |  | Nombre |

Restricciones: UNIQUE (region, nombre).

### `contacto_cliente`

Persona de contacto asociada a un cliente (RF-CLI-03).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_contacto` | integer | no | PK | Id contacto |
| `id_cliente` | integer | no | FK → cliente | Cliente |
| `nombre` | varchar(120) | no |  | Nombre |
| `cargo` | varchar(80) | no |  | Cargo |
| `email` | varchar(150) | no |  | Correo |
| `telefono` | varchar(30) | no |  | Telefono |
| `principal` | boolean | no |  | Es contacto principal |

### `direccion_cliente`

Direccion del cliente, tipificada segun su uso (RF-CLI-04).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_direccion` | integer | no | PK | Id direccion |
| `id_cliente` | integer | no | FK → cliente | Cliente |
| `id_comuna` | integer | no | FK → comuna | Comuna |
| `tipo` | varchar(20) | no |  | Tipo de direccion. Valores: facturacion, despacho, instalacion. |
| `calle` | varchar(200) | no |  | Calle |
| `numero` | varchar(20) | no |  | Numero |
| `latitud` | numeric(9, 6) | si |  | Latitud |
| `longitud` | numeric(9, 6) | si |  | Longitud |
| `validada` | boolean | no |  | Validada por geocodificacion |

### `region`

Division administrativa mayor. Tabla de catalogo semilla.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_region` | integer | no | PK | Id region |
| `nombre` | varchar(80) | no | UQ | Nombre |
| `codigo` | varchar(10) | no |  | Codigo oficial |

## Catalogo y recetas (8 tablas)

### `bom_modelo`

Lista de materiales base del modelo (RF-CAT-04).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_bom` | integer | no | PK | Id bom |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo |
| `id_material` | integer | no | FK → material | Material |
| `cantidad` | numeric(12, 4) | no |  | Cantidad por unidad |
| `observacion` | varchar(200) | no |  | Observacion |

Restricciones: UNIQUE (modelo, material); CHECK `ck_bom_cantidad_positiva`.

### `familia_producto`

Agrupacion de modelos por caracteristicas comunes (RF-CAT-01).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_familia` | integer | no | PK | Id familia |
| `nombre` | varchar(80) | no | UQ | Nombre |
| `descripcion` | varchar(200) | no |  | Descripcion |

### `modelo_parametro`

Parametro aplicable a un modelo, con su valor por defecto.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id` | bigint | no | PK | Id |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo |
| `id_parametro` | integer | no | FK → parametro_tecnico | Parametro |
| `valor_defecto` | varchar(60) | no |  | Valor por defecto |
| `obligatorio` | boolean | no |  | Obligatorio para este modelo |

Restricciones: UNIQUE (modelo, parametro).

### `modelo_producto`

Modelo base parametrizable de transformador.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_modelo` | integer | no | PK | Id modelo |
| `id_familia` | integer | no | FK → familia_producto | Familia |
| `codigo` | varchar(40) | no | UQ | Codigo |
| `nombre` | varchar(150) | no |  | Nombre comercial |
| `descripcion` | text | no |  | Descripcion tecnica |
| `publicado` | boolean | no |  | Publicado en el catalogo web |

### `parametro_tecnico`

Caracteristica tecnica configurable de un transformador.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_parametro` | integer | no | PK | Id parametro |
| `codigo` | varchar(40) | no | UQ | Codigo |
| `nombre` | varchar(100) | no |  | Nombre visible |
| `unidad` | varchar(20) | no |  | Unidad de medida |
| `tipo_dato` | varchar(20) | no |  | Tipo de dato. Valores: numerico, texto, lista. |
| `obligatorio` | boolean | no |  | Obligatorio por defecto. Obligatoriedad en el formulario web. Configurable (RF-ADM-04). |

### `precio_base_modelo`

Precio base del modelo, versionado por vigencia (RN-17, RF-CAT-06).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `vigente_desde` | date | no |  | Vigente desde |
| `vigente_hasta` | date | si |  | Vigente hasta |
| `id_precio` | integer | no | PK | Id precio |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo |
| `monto_uf` | numeric(12, 4) | no |  | Monto en uf |
| `id_usuario` | integer | no | FK → usuario | Registrado por |

Restricciones: UNIQUE (modelo, vigente_desde); CHECK `ck_precio_modelo_no_negativo`.

### `tarea_estandar_modelo`

Tarea productiva estandar del modelo, con sus horas hombre (RF-CAT-05).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_tarea_estandar` | integer | no | PK | Id tarea estandar |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo |
| `nombre` | varchar(120) | no |  | Nombre de la tarea |
| `secuencia` | smallint | no |  | Secuencia |
| `horas_estimadas` | numeric(8, 2) | no |  | Horas hombre estimadas |
| `id_empleado_sugerido` | integer | si | FK → empleado | Responsable habitual. Se asigna automaticamente a la tarea al generar la orden de trabajo. |

Restricciones: UNIQUE (modelo, secuencia); CHECK `ck_tarea_horas_positivas`.

### `valor_parametro`

Valor admisible de un parametro de tipo lista.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_valor` | integer | no | PK | Id valor |
| `id_parametro` | integer | no | FK → parametro_tecnico | Parametro |
| `valor` | varchar(60) | no |  | Valor |
| `orden` | smallint | no |  | Orden de presentacion |

Restricciones: UNIQUE (parametro, valor).

## Proceso comercial (10 tablas)

### `cotizacion`

Oferta formal al cliente, con vigencia limitada y valores congelados.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `id_cotizacion` | integer | no | PK | Id cotizacion |
| `numero` | varchar(20) | no |  | Numero correlativo |
| `version` | smallint | no |  | Version |
| `id_solicitud` | integer | no | FK → solicitud_presupuesto | Solicitud de origen |
| `id_cliente` | integer | no | FK → cliente | Cliente |
| `id_estado` | integer | no | FK → estado_documento | Estado actual |
| `id_ejecutivo` | integer | no | FK → usuario | Ejecutivo responsable |
| `valor_uf` | numeric(12, 2) | no |  | Valor de la uf congelado |
| `fecha_valor_uf` | date | no |  | Fecha del valor de la uf |
| `total_uf` | numeric(14, 4) | no |  | Total en uf |
| `descuento_pct` | numeric(5, 2) | no |  | Descuento aplicado (%) |
| `plazo_dias_habiles` | smallint | si |  | Plazo de fabricacion (dias habiles) |
| `fecha_entrega` | date | si |  | Fecha comprometida de entrega |
| `vence_el` | date | no |  | Vence el |

Restricciones: UNIQUE (numero, version); CHECK `ck_cotizacion_descuento_rango`.

### `cotizacion_historial`

Historial de estados de la cotizacion (RN-14).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `estado_anterior_id` | integer | si | FK → estado_documento | Estado anterior |
| `estado_nuevo_id` | integer | no | FK → estado_documento | Estado nuevo |
| `usuario_id` | integer | no | FK → usuario | Responsable |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `observacion` | varchar(300) | no |  | Observacion |
| `id_historial` | bigint | no | PK | Id historial |
| `id_cotizacion` | integer | no | FK → cotizacion | Cotizacion |

### `cotizacion_linea`

Detalle de la cotizacion, con el desglose de costos.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_linea` | integer | no | PK | Id linea |
| `id_cotizacion` | integer | no | FK → cotizacion | Cotizacion |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo cotizado |
| `cantidad` | integer | no |  | Unidades |
| `costo_material_uf` | numeric(12, 4) | no |  | Costo estimado de materiales (uf) |
| `costo_hh_uf` | numeric(12, 4) | no |  | Costo estimado de horas hombre (uf) |
| `margen_pct` | numeric(5, 2) | no |  | Margen aplicado (%) |
| `precio_uf` | numeric(12, 4) | no |  | Precio unitario (uf) |

Restricciones: CHECK `ck_linea_cantidad_positiva`.

### `estado_documento`

Catalogo de estados aplicables a cada tipo de documento del flujo.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_estado` | integer | no | PK | Id estado |
| `tipo_documento` | varchar(30) | no |  | Tipo de documento. Valores: solicitud, cotizacion, orden_compra, orden_trabajo. |
| `codigo` | varchar(30) | no |  | Codigo |
| `nombre` | varchar(60) | no |  | Nombre visible |
| `es_final` | boolean | no |  | Cierra el ciclo del documento |

Restricciones: UNIQUE (tipo_documento, codigo).

### `orden_compra`

Documento que formaliza la compra.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `id_orden_compra` | integer | no | PK | Id orden compra |
| `numero` | varchar(20) | no | UQ | Numero correlativo |
| `id_cotizacion` | integer | no | FK → cotizacion | Cotizacion de origen |
| `id_cliente` | integer | no | FK → cliente | Cliente |
| `id_estado` | integer | no | FK → estado_documento | Estado actual |
| `total_uf` | numeric(14, 4) | no |  | Total en uf |
| `anticipo_pct` | numeric(5, 2) | si |  | Anticipo acordado (%) |

### `orden_compra_historial`

Historial de estados de la orden de compra (RN-14).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `estado_anterior_id` | integer | si | FK → estado_documento | Estado anterior |
| `estado_nuevo_id` | integer | no | FK → estado_documento | Estado nuevo |
| `usuario_id` | integer | no | FK → usuario | Responsable |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `observacion` | varchar(300) | no |  | Observacion |
| `id_historial` | bigint | no | PK | Id historial |
| `id_orden_compra` | integer | no | FK → orden_compra | Orden de compra |

### `orden_compra_linea`

Detalle de la orden de compra.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_linea_oc` | integer | no | PK | Id linea oc |
| `id_orden_compra` | integer | no | FK → orden_compra | Orden de compra |
| `id_cotizacion_linea` | integer | no | FK → cotizacion_linea | Linea de cotizacion |
| `cantidad` | integer | no |  | Unidades adquiridas |
| `precio_uf` | numeric(12, 4) | no |  | Precio unitario (uf) |

Restricciones: CHECK `ck_linea_oc_cantidad_positiva`.

### `solicitud_especificacion`

Valor de cada parametro tecnico declarado por el cliente (RN-02).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id` | bigint | no | PK | Id |
| `id_solicitud` | integer | no | FK → solicitud_presupuesto | Solicitud |
| `id_parametro` | integer | no | FK → parametro_tecnico | Parametro tecnico |
| `valor` | varchar(60) | no |  | Valor declarado |

Restricciones: UNIQUE (solicitud, parametro).

### `solicitud_historial`

Historial de estados de la solicitud (RN-14).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `estado_anterior_id` | integer | si | FK → estado_documento | Estado anterior |
| `estado_nuevo_id` | integer | no | FK → estado_documento | Estado nuevo |
| `usuario_id` | integer | no | FK → usuario | Responsable |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `observacion` | varchar(300) | no |  | Observacion |
| `id_historial` | bigint | no | PK | Id historial |
| `id_solicitud` | integer | no | FK → solicitud_presupuesto | Solicitud |

### `solicitud_presupuesto`

Requerimiento de cotizacion originado por el cliente en la web.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `id_solicitud` | integer | no | PK | Id solicitud |
| `numero` | varchar(20) | no | UQ | Numero correlativo |
| `id_cliente` | integer | no | FK → cliente | Cliente |
| `id_modelo` | integer | si | FK → modelo_producto | Modelo base. Nulo si la solicitud no parte de un modelo del catalogo. |
| `id_direccion` | integer | si | FK → direccion_cliente | Direccion de instalacion |
| `cantidad` | integer | no |  | Unidades requeridas |
| `fecha_deseada` | date | si |  | Fecha de entrega deseada |
| `id_estado` | integer | no | FK → estado_documento | Estado actual |
| `id_ejecutivo` | integer | si | FK → usuario | Ejecutivo asignado |

Restricciones: CHECK `ck_solicitud_cantidad_positiva`.

## Produccion (7 tablas)

### `consumo_material`

Material efectivamente utilizado en una tarea (RN-09).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_consumo` | integer | no | PK | Id consumo |
| `id_tarea` | integer | no | FK → tarea_ot | Tarea |
| `id_material` | integer | no | FK → material | Material |
| `id_bodega` | integer | no | FK → bodega | Bodega de origen |
| `cantidad` | numeric(12, 4) | no |  | Cantidad consumida |
| `costo_unitario_uf` | numeric(12, 4) | no |  | Costo unitario congelado (uf) |
| `planificado` | boolean | no |  | Estaba previsto en la lista de materiales |
| `id_empleado` | integer | no | FK → empleado | Registrado por |
| `fecha` | timestamp with time zone | no |  | Fecha del registro |

Restricciones: CHECK `ck_consumo_cantidad_positiva`.

### `empleado`

Trabajador que ejecuta tareas productivas (RF-OT-11).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_empleado` | integer | no | PK | Id empleado |
| `rut` | varchar(12) | no | UQ | Rut |
| `nombre` | varchar(120) | no |  | Nombre completo |
| `cargo` | varchar(80) | no |  | Cargo |
| `id_usuario` | integer | si | FK → usuario, UQ | Usuario del sistema. Solo si el empleado registra directamente en el sistema. |

### `orden_trabajo`

Instruccion de fabricacion derivada de una orden de compra confirmada.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `id_orden_trabajo` | integer | no | PK | Id orden trabajo |
| `numero` | varchar(20) | no | UQ | Numero correlativo |
| `id_orden_compra` | integer | no | FK → orden_compra | Orden de compra de origen |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo a fabricar |
| `cantidad` | integer | no |  | Unidades |
| `id_estado` | integer | no | FK → estado_documento | Estado actual |
| `costo_estimado_uf` | numeric(14, 4) | no |  | Costo estimado heredado (uf) |
| `costo_real_uf` | numeric(14, 4) | si |  | Costo real acumulado (uf) |
| `avance_pct` | numeric(5, 2) | si |  | Avance (%) |
| `fecha_inicio` | date | si |  | Inicio de fabricacion |
| `fecha_cierre` | date | si |  | Cierre |

Restricciones: CHECK `ck_ot_cantidad_positiva`.

### `orden_trabajo_historial`

Historial de estados de la orden de trabajo (RN-14).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `creado_en` | timestamp with time zone | no |  | Creado en |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
| `estado_anterior_id` | integer | si | FK → estado_documento | Estado anterior |
| `estado_nuevo_id` | integer | no | FK → estado_documento | Estado nuevo |
| `usuario_id` | integer | no | FK → usuario | Responsable |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `observacion` | varchar(300) | no |  | Observacion |
| `id_historial` | bigint | no | PK | Id historial |
| `id_orden_trabajo` | integer | no | FK → orden_trabajo | Orden de trabajo |

### `registro_hora_hombre`

Horas trabajadas por un empleado sobre una tarea en una fecha (RN-10).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_registro` | integer | no | PK | Id registro |
| `id_tarea` | integer | no | FK → tarea_ot | Tarea |
| `id_empleado` | integer | no | FK → empleado | Empleado |
| `fecha` | date | no |  | Fecha de la jornada |
| `horas` | numeric(6, 2) | no |  | Horas trabajadas |
| `valor_hora_uf` | numeric(10, 4) | no |  | Tarifa congelada (uf/hora) |
| `anulado` | boolean | no |  | Anulado |
| `id_usuario_registro` | integer | no | FK → usuario | Usuario que registro. Se distingue del empleado: el jefe puede registrar por un ausente. |

Restricciones: CHECK `ck_horas_positivas`.

### `tarea_ot`

Actividad productiva concreta dentro de una orden de trabajo.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_tarea` | integer | no | PK | Id tarea |
| `id_orden_trabajo` | integer | no | FK → orden_trabajo | Orden de trabajo |
| `nombre` | varchar(120) | no |  | Nombre de la tarea |
| `secuencia` | smallint | no |  | Secuencia |
| `horas_estimadas` | numeric(8, 2) | no |  | Horas hombre estimadas |
| `estado` | varchar(20) | no |  | Estado. Valores: pendiente, en_ejecucion, terminada. |
| `id_empleado` | integer | si | FK → empleado | Empleado asignado |
| `fecha_estimada` | date | si |  | Fecha estimada |

Restricciones: UNIQUE (orden_trabajo, secuencia).

### `tarifa_hora_hombre`

Valor de la hora de trabajo, versionado por vigencia (RN-10, RN-17).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_tarifa` | integer | no | PK | Id tarifa |
| `id_empleado` | integer | no | FK → empleado | Empleado |
| `valor_hora_uf` | numeric(10, 4) | no |  | Valor hora (uf) |
| `vigente_desde` | date | no |  | Vigente desde |
| `vigente_hasta` | date | si |  | Vigente hasta |

Restricciones: UNIQUE (empleado, vigente_desde); CHECK `ck_tarifa_positiva`.

## Control de calidad (5 tablas)

### `control_calidad`

Ejecucion de un protocolo sobre una orden de trabajo (RF-CAL-03).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_control` | integer | no | PK | Id control |
| `id_orden_trabajo` | integer | no | FK → orden_trabajo | Orden de trabajo |
| `id_protocolo` | integer | no | FK → protocolo_calidad | Protocolo aplicado |
| `id_inspector` | integer | no | FK → usuario | Inspector responsable |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `estado` | varchar(20) | no |  | Estado. Valores: en_proceso, conforme, con_nc. |
| `observacion` | varchar(300) | no |  | Observacion general |

### `no_conformidad`

Desviacion detectada en un punto de control (RF-CAL-04).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_no_conformidad` | integer | no | PK | Id no conformidad |
| `id_resultado` | integer | no | FK → resultado_control, UQ | Resultado que la origino |
| `descripcion` | varchar(300) | no |  | Descripcion |
| `severidad` | varchar(20) | no |  | Severidad. Valores: menor, mayor, critica. |
| `id_responsable` | integer | no | FK → usuario | Responsable de la accion correctiva |
| `accion_correctiva` | text | no |  | Accion correctiva |
| `estado` | varchar(20) | no |  | Estado. Valores: abierta, cerrada. |
| `abierta_en` | timestamp with time zone | no |  | Abierta en |
| `cerrada_en` | timestamp with time zone | si |  | Cerrada en |
| `id_usuario_cierre` | integer | si | FK → usuario | Usuario que cerro |

### `protocolo_calidad`

Conjunto de ensayos aplicables a un modelo de producto (RF-CAL-01).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_protocolo` | integer | no | PK | Id protocolo |
| `id_modelo` | integer | no | FK → modelo_producto | Modelo |
| `nombre` | varchar(120) | no |  | Nombre del protocolo |
| `version` | smallint | no |  | Version |
| `norma_referencia` | varchar(80) | no |  | Norma de referencia |

Restricciones: UNIQUE (modelo, nombre, version).

### `punto_control`

Ensayo individual con su criterio de aceptacion (RF-CAL-02).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_punto` | integer | no | PK | Id punto |
| `id_protocolo` | integer | no | FK → protocolo_calidad | Protocolo |
| `nombre` | varchar(120) | no |  | Nombre del ensayo |
| `tipo_ensayo` | varchar(60) | no |  | Tipo de ensayo |
| `unidad` | varchar(20) | no |  | Unidad de medida |
| `valor_esperado` | numeric(14, 4) | si |  | Valor nominal esperado |
| `tolerancia_inf` | numeric(14, 4) | si |  | Limite inferior admisible |
| `tolerancia_sup` | numeric(14, 4) | si |  | Limite superior admisible |
| `obligatorio` | boolean | no |  | Obligatorio. Si es obligatorio, condiciona el cierre de la orden (RN-12). |
| `secuencia` | smallint | no |  | Secuencia |

Restricciones: UNIQUE (protocolo, secuencia).

### `resultado_control`

Valor medido en un punto de control.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_resultado` | integer | no | PK | Id resultado |
| `id_control` | integer | no | FK → control_calidad | Control |
| `id_punto` | integer | no | FK → punto_control | Punto de control |
| `valor_medido` | numeric(14, 4) | no |  | Valor medido |
| `conforme` | boolean | no |  | Conforme |
| `observacion` | varchar(300) | no |  | Observacion |
| `registrado_en` | timestamp with time zone | no |  | Registrado en |

## Inventario (6 tablas)

### `bodega`

Ubicacion fisica de almacenamiento (RF-INV-03).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_bodega` | integer | no | PK | Id bodega |
| `codigo` | varchar(20) | no | UQ | Codigo |
| `nombre` | varchar(100) | no |  | Nombre |
| `ubicacion` | varchar(150) | no |  | Ubicacion fisica |

### `categoria_material`

Agrupacion de materiales por tipo. Catalogo semilla.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_categoria` | integer | no | PK | Id categoria |
| `nombre` | varchar(80) | no | UQ | Nombre |

### `material`

Insumo utilizado en la fabricacion. No incluye productos terminados.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_material` | integer | no | PK | Id material |
| `id_categoria` | integer | no | FK → categoria_material | Categoria |
| `codigo` | varchar(40) | no | UQ | Codigo |
| `nombre` | varchar(150) | no |  | Nombre |
| `unidad_medida` | varchar(20) | no |  | Unidad de medida. Valores: un, kg, m, m2, l. |
| `stock_minimo` | numeric(12, 4) | si |  | Stock minimo. Nivel bajo el cual se emite alerta (RF-INV-06). |

### `movimiento_inventario`

Registro de toda variacion de existencias (RF-INV-04, RF-INV-05).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_movimiento` | bigint | no | PK | Id movimiento |
| `id_material` | integer | no | FK → material | Material |
| `id_bodega` | integer | no | FK → bodega | Bodega |
| `tipo` | varchar(20) | no |  | Tipo de movimiento. Valores: recepcion, consumo, ajuste, devolucion. |
| `cantidad` | numeric(12, 4) | no |  | Cantidad. Positiva en entradas, negativa en salidas. |
| `costo_unitario_uf` | numeric(12, 4) | no |  | Costo unitario (uf) |
| `id_proveedor` | integer | si | FK → proveedor | Proveedor. Solo en recepciones. |
| `id_consumo` | integer | si | FK → consumo_material, UQ | Consumo productivo de origen |
| `id_usuario` | integer | no | FK → usuario | Responsable |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |
| `observacion` | varchar(300) | no |  | Observacion |

### `precio_material`

Costo de compra del material, versionado por vigencia (RN-17).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `vigente_desde` | date | no |  | Vigente desde |
| `vigente_hasta` | date | si |  | Vigente hasta |
| `id_precio_material` | integer | no | PK | Id precio material |
| `id_material` | integer | no | FK → material | Material |
| `id_proveedor` | integer | si | FK → proveedor | Proveedor |
| `costo_uf` | numeric(12, 4) | no |  | Costo en uf |

Restricciones: UNIQUE (material, vigente_desde); CHECK `ck_precio_material_no_negativo`.

### `proveedor`

Empresa que abastece materiales (RF-INV-02).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `activo` | boolean | no |  | Activo |
| `id_proveedor` | integer | no | PK | Id proveedor |
| `rut` | varchar(12) | no | UQ | Rut |
| `razon_social` | varchar(150) | no |  | Razon social |
| `email` | varchar(150) | no |  | Correo |
| `telefono` | varchar(30) | no |  | Telefono |

## Cobros, pagos e indicadores (3 tablas)

### `documento_cobro`

Obligacion de pago derivada de una orden de compra (RN-15).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_documento_cobro` | integer | no | PK | Id documento cobro |
| `numero` | varchar(20) | no | UQ | Numero correlativo |
| `id_orden_compra` | integer | no | FK → orden_compra | Orden de compra |
| `tipo` | varchar(20) | no |  | Tipo de cobro. Valores: anticipo, saldo. |
| `monto_uf` | numeric(14, 4) | no |  | Monto en uf |
| `valor_uf` | numeric(12, 2) | no |  | Valor de la uf aplicado |
| `monto_clp` | numeric(16, 2) | no |  | Monto en pesos (congelado) |
| `estado` | varchar(20) | no |  | Estado. Valores: pendiente, pagado, anulado. |
| `vence_el` | date | no |  | Vence el |
| `creado_en` | timestamp with time zone | no |  | Emitido en |

Restricciones: CHECK `ck_cobro_monto_positivo`.

### `indicador_economico`

Serie historica de indicadores obtenidos del servicio externo.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_indicador` | integer | no | PK | Id indicador |
| `codigo` | varchar(10) | no |  | Indicador. Valores: UF, UTM, USD. |
| `fecha` | date | no |  | Fecha del valor |
| `valor` | numeric(14, 4) | no |  | Valor |
| `obtenido_en` | timestamp with time zone | no |  | Obtenido del servicio en |

Restricciones: UNIQUE (codigo, fecha); CHECK `ck_indicador_positivo`.

### `transaccion_pago`

Intento de pago procesado por la pasarela externa.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_transaccion` | integer | no | PK | Id transaccion |
| `id_documento_cobro` | integer | no | FK → documento_cobro | Documento de cobro |
| `id_externo` | varchar(120) | no |  | Identificador de la pasarela |
| `pasarela` | varchar(40) | no |  | Pasarela utilizada |
| `monto` | numeric(16, 2) | no |  | Monto |
| `moneda` | varchar(3) | no |  | Moneda (iso 4217) |
| `estado` | varchar(30) | no |  | Estado. Valores: iniciada, aprobada, rechazada, cancelada, pendiente_conciliacion. |
| `iniciada_en` | timestamp with time zone | no |  | Iniciada en |
| `resuelta_en` | timestamp with time zone | si |  | Resuelta en |
| `respuesta` | jsonb | si |  | Respuesta completa de la pasarela |

## Configuracion e integraciones (4 tablas)

### `aviso_sitio`

Mensaje publicado en la web, administrado desde escritorio (RF-ADM-05).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_aviso` | integer | no | PK | Id aviso |
| `titulo` | varchar(120) | no |  | Titulo |
| `cuerpo` | text | no |  | Contenido |
| `tipo` | varchar(20) | no |  | Tipo. Valores: informativo, advertencia, mantencion. |
| `vigente_desde` | timestamp with time zone | no |  | Publicar desde |
| `vigente_hasta` | timestamp with time zone | si |  | Publicar hasta |
| `activo` | boolean | no |  | Activo |
| `id_usuario` | integer | no | FK → usuario | Creado por |

### `feriado`

Feriado legal obtenido del servicio externo (RN-08).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_feriado` | integer | no | PK | Id feriado |
| `fecha` | date | no | UQ | Fecha |
| `nombre` | varchar(120) | no |  | Denominacion oficial |
| `tipo` | varchar(30) | no |  | Tipo. Valores: civil, religioso, regional. |
| `obtenido_en` | timestamp with time zone | no |  | Obtenido en |

### `log_integracion`

Registro de llamadas a servicios externos (RF-INT-01).

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_log` | bigint | no | PK | Id log |
| `servicio` | varchar(40) | no |  | Servicio invocado |
| `endpoint` | varchar(255) | no |  | Recurso |
| `metodo` | varchar(10) | no |  | Metodo http |
| `codigo_respuesta` | smallint | no |  | Codigo de estado |
| `latencia_ms` | integer | no |  | Latencia (ms) |
| `exitoso` | boolean | no |  | Exitoso |
| `mensaje_error` | varchar(500) | no |  | Detalle del error |
| `fecha_hora` | timestamp with time zone | no |  | Fecha y hora |

### `parametro_sistema`

Parametro configurable del sistema y del canal web.

| Columna | Tipo | Nulo | Claves | Descripcion |
|---|---|---|---|---|
| `id_parametro_sistema` | integer | no | PK | Id parametro sistema |
| `clave` | varchar(60) | no | UQ | Clave |
| `valor` | varchar(300) | no |  | Valor actual |
| `tipo_dato` | varchar(20) | no |  | Tipo de dato. Valores: booleano, numerico, texto, fecha. |
| `ambito` | varchar(30) | no |  | Ambito. Valores: sistema, canal_web, comercial, produccion. |
| `descripcion` | varchar(200) | no |  | Descripcion funcional |
| `id_usuario` | integer | no | FK → usuario | Modificado por |
| `modificado_en` | timestamp with time zone | no |  | Modificado en |
