# SITRAFO

Sistema Integral de Gestion Comercial y Productiva para Transformadores Electricos.

Proyecto APT — Capstone (PTY4614), Ingenieria en Informatica, Duoc UC Sede Puente Alto.

## Equipo

| Integrante | Rol |
|---|---|
| Benjamin Delgado Bravo | Lider de Proyecto / Product Owner |
| Camila Olivares | Scrum Master |
| Milko Soto | Desarrollador / Responsable de Calidad |

## Arquitectura

Tres componentes sobre un backend comun:

1. **API REST** — Django + Django REST Framework sobre PostgreSQL. Unico punto de acceso a los datos.
2. **Aplicacion de escritorio** — Python + PySide6, para administracion interna.
3. **Aplicacion web** — Django + Bootstrap 5 + htmx, orientada al cliente.

**Regla no negociable:** la aplicacion de escritorio nunca accede directamente a la
base de datos. Siempre lo hace a traves de la API REST, igual que la web.

## Estructura del repositorio

```
sitrafo/
├── config/                 Configuracion del proyecto
│   ├── settings/           base.py, dev.py, prod.py
│   ├── urls.py             Rutas raiz
│   └── api_urls.py         Rutas de la API REST
├── apps/                   Una app por dominio del modelo de datos
│   ├── common/             Modelos abstractos y validadores compartidos
│   ├── seguridad/          Usuarios, roles, permisos, auditoria
│   ├── clientes/           Clientes, contactos, direcciones
│   ├── catalogo/           Modelos de producto, parametros, precios, BOM
│   ├── comercial/          Solicitudes, cotizaciones, ordenes de compra
│   ├── produccion/         Ordenes de trabajo, tareas, consumos, horas hombre
│   ├── inventario/         Materiales, proveedores, bodegas, movimientos
│   ├── calidad/            Protocolos, ensayos, no conformidades
│   ├── pagos/              Indicadores, documentos de cobro, transacciones
│   └── configuracion/      Parametros, avisos, feriados, log de integraciones
├── escritorio/             Aplicacion de escritorio en PySide6
│   ├── main.py             Punto de entrada
│   ├── cliente_api.py      Unico acceso a los datos, via API REST
│   ├── ventana_login.py    Autenticacion por token
│   ├── ventana_principal.py
│   └── paneles.py          Catalogo, clientes, solicitudes, canal web
├── requirements/           base.txt, dev.txt, prod.txt
├── docker-compose.yml
└── Dockerfile
```

## Puesta en marcha

Requisitos: Docker y Docker Compose.

```bash
# 1. Clonar y entrar
git clone <url-del-repositorio>
cd sitrafo

# 2. Crear el archivo de entorno
cp .env.example .env

# 3. Levantar los contenedores
docker compose up --build

# 4. En otra terminal, aplicar migraciones
docker compose exec web python manage.py migrate

# 5. Crear un usuario administrador
docker compose exec web python manage.py createsuperuser

# 6. Sembrar los datos iniciales
docker compose exec web python manage.py cargar_estados
docker compose exec web python manage.py cargar_parametros

# 7. Cargar un caso de demostracion (opcional, recomendado)
docker compose exec web python manage.py cargar_demo

# 8. Sincronizar los servicios externos
docker compose exec web python manage.py sincronizar_indicadores
docker compose exec web python manage.py sincronizar_feriados

# 9. Emitir los anticipos de ordenes de compra que aun no lo tengan
docker compose exec web python manage.py emitir_cobros

# 10. Cargar los roles y la matriz de permisos (y un usuario por rol)
docker compose exec web python manage.py cargar_roles --usuarios-demo

# 11. Datos del taller: materiales con stock, tareas estandar y empleados
docker compose exec web python manage.py cargar_demo_produccion
```

Los comandos del paso 6 cargan los 21 estados del flujo documental y los 12
parametros de configuracion del sistema. Sin ellos no es posible crear
solicitudes ni cotizaciones.

La aplicacion queda en http://localhost:8000 y el panel de administracion en
http://localhost:8000/admin/

## Comandos frecuentes

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell
docker compose exec web pytest
docker compose exec web pytest --cov=apps
docker compose exec web ruff check .
docker compose down            # detener
docker compose down -v         # detener y borrar la base de datos
```

## Modelo de datos

54 tablas relacionales normalizadas hasta tercera forma normal, distribuidas
en nueve dominios:

| Dominio | Tablas |
|---|---|
| Seguridad y auditoria | 6 |
| Clientes | 5 |
| Catalogo de productos | 8 |
| Proceso comercial | 10 |
| Ejecucion productiva | 7 |
| Inventario | 6 |
| Control de calidad | 5 |
| Pagos y moneda | 3 |
| Configuracion e integraciones | 4 |

## Aplicacion de escritorio

Se ejecuta en el equipo del usuario, no en Docker: es una interfaz grafica.

```powershell
cd escritorio
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Se invoca directamente el interprete del entorno virtual para evitar la
politica de ejecucion de scripts de PowerShell.

Requiere el backend corriendo. Se ingresa con una cuenta interna; las cuentas
de cliente web son rechazadas.

Paneles disponibles:

| Panel | Que permite |
|---|---|
| Catalogo | Crear y editar modelos (parametros tecnicos y precio base versionado) y publicarlos o retirarlos de la web |
| Clientes | Consultar clientes, contactos y direcciones |
| Solicitudes | Tomar una solicitud y elaborar su cotizacion con el costeo calculado |
| Cotizaciones | Enviar a aprobacion, emitir (con envio por correo), reenviar y generar la orden de compra |
| Ordenes de compra | Ver el estado del anticipo, confirmar la orden y generar sus ordenes de trabajo |
| Ordenes de trabajo | Asignar responsables, iniciar, registrar por un ausente, costo real contra estimado, enviar a calidad y cerrar |
| Taller (operario) | Vista propia sin menu, con campos grandes: sus tareas, horas, material y termino de tarea |
| Canal web | Modo mantencion, pago en linea, autorregistro y parametros |
| Integraciones | Registro de llamadas a servicios externos |
| Control de calidad | El inspector ejecuta los ensayos de las ordenes en calidad; el sistema evalua la conformidad y abre las no conformidades |
| No conformidades | Seguimiento y cierre con accion correctiva |
| Protocolos de calidad | Ensayos por modelo con su rango de aceptacion, versionados |
| Usuarios y roles | Crear usuarios internos, asignar roles, asociar empleados del taller, suspender, reactivar y restablecer claves (solo Administrador) |

Con estos paneles el flujo comercial completo (solicitud, cotizacion,
emision, orden de compra) se opera sin usar el admin de Django.

Detalle en `escritorio/README.md`.

## Ejecucion productiva (HU-07, HU-08)

Reglas en `apps/produccion/services.py`, expuestas en `/api/v1/ordenes-trabajo/`
y `/api/v1/tareas/`:

- La orden de trabajo nace solo de una orden de compra confirmada (RN-07),
  una por linea, con las tareas estandar del modelo y el costo estimado de la
  cotizacion.
- Las horas se valorizan con la tarifa vigente del empleado a la fecha y
  respetan el tope diario configurable (RN-10).
- El consumo de material descuenta stock con un movimiento de inventario y
  se rechaza si no hay saldo suficiente, informando lo disponible (RN-09).
- Cada registro actualiza el costo real; un registro de horas no se edita ni
  se borra, se anula con motivo y queda auditado (RN-13).
- El avance es el porcentaje de tareas terminadas, no de horas consumidas:
  una tarea hecha en menos horas de las estimadas cuenta completa. La
  diferencia de horas se refleja en el costo real y su desviacion.
- El operario registra solo en sus tareas; el jefe de produccion puede
  registrar por un ausente.
- La orden pasa a calidad cuando todas sus tareas estan terminadas y no se
  cierra con controles pendientes o no conformidades abiertas (RN-12). Una
  desviacion de costo sobre el umbral exige justificacion al cerrar (RN-11).

## Control de calidad (HU-09)

Reglas en `apps/calidad/services.py`, expuestas en `/api/v1/protocolos/`,
`/api/v1/controles-calidad/` y `/api/v1/no-conformidades/`:

- Cada modelo tiene un protocolo de ensayos con su rango de aceptacion. Un
  protocolo ya aplicado no se modifica: se crea una version nueva y la
  anterior queda retirada, conservando el criterio historico.
- El inspector registra el valor medido; la conformidad la calcula el
  sistema contra el rango. Un resultado fuera de rango abre una no
  conformidad con su severidad.
- Mientras la no conformidad este abierta no se repite el ensayo; se cierra
  solo registrando la accion correctiva, y luego se repite. Todas las
  mediciones se conservan.
- La orden de trabajo se cierra solo con todos los ensayos obligatorios
  ejecutados y sin no conformidades abiertas (RN-12).

`cargar_demo_produccion` carga un protocolo de ensayos de rutina (IEC 60076-1)
para cada modelo de la demostracion.

## Saldo y entrega (RN-15)

- Al cerrar la ultima orden de trabajo de una orden de compra se emite el
  cobro del saldo, con la UF del dia de emision, y se avisa al cliente por
  correo. El cliente lo paga desde la web con PayPal, igual que el anticipo.
- La entrega del pedido se registra desde el escritorio (panel Ordenes de
  compra) solo con la fabricacion terminada y el saldo pagado; la orden de
  compra queda entregada y el flujo documental termina.

## Horas de demostracion

Las tareas estandar de la demostracion estiman como maximo 2 horas cada una,
para poder recorrer el flujo completo en una sesion de pruebas.
`cargar_demo_produccion` acota a ese valor las tareas cargadas por versiones
anteriores. En operacion real se registran las horas propias del taller.

## Roles y matriz de permisos

La matriz de acceso de la ERS-01 (seccion 8.2) esta transcrita en
`apps/seguridad/matriz.py` y se carga en las tablas `rol`, `permiso` y
`rol_permiso` con `cargar_roles`. Desde ahi es configurable: la API autoriza
leyendo la tabla, no la constante.

| Rol | Opera | Solo lectura |
|---|---|---|
| Administrador | usuarios, roles, parametros, catalogo, precios, empleados, canal web | clientes, solicitudes, ordenes de compra, auditoria |
| Ejecutivo comercial | clientes, solicitudes, cotizaciones (incluida aprobacion), ordenes de compra | catalogo, precios, canal web |
| Jefe de produccion | listas de materiales, ordenes de trabajo, taller | clientes, catalogo, solicitudes, cotizaciones, ordenes de compra |
| Operario de taller | registro de horas y consumos | ordenes de trabajo |
| Inspector de calidad | protocolos, ensayos, no conformidades | catalogo, ordenes de trabajo |
| Encargado de bodega | materiales, bodegas, movimientos, kardex | listas de materiales, ordenes de trabajo |

Reglas aplicadas en `apps/common/permissions.py` (`PermisoPorRol`):

- Denegacion por defecto (RN-18): lo que un viewset no declara, no se permite.
  Un usuario interno sin rol no puede operar ni ingresar al escritorio.
- Cada acceso denegado queda en la bitacora de auditoria (CU-SEG-07).
- El cliente web solo usa las acciones que le corresponden (ver, solicitar,
  aceptar, rechazar) y solo sobre sus documentos (RN-16).
- Los documentos solo cambian por las acciones del flujo: ni siquiera el
  superusuario puede crear o editar a mano una cotizacion u orden de compra.
- Una cotizacion con descuento sobre el umbral la aprueba un ejecutivo
  distinto del que la elaboro (RN-05).

Administracion de cuentas (`apps/seguridad/services.py`):

- Solo el Administrador crea usuarios y asigna roles; todo usuario interno
  requiere al menos un rol.
- Nadie se suspende a si mismo ni se quita el rol de Administrador, y una
  cuenta de superusuario solo la modifica otro superusuario.
- La clave temporal se genera y se muestra una sola vez.
- Al ingresar, cada clave incorrecta suma un intento; al llegar al maximo
  configurado (`sistema.intentos_fallidos_max`) la cuenta se bloquea hasta
  que el Administrador la reactive (RF-SEG-04). Se registra el ultimo acceso.

`cargar_roles --usuarios-demo` crea `administrador`, `comercial`,
`comercial2`, `produccion`, `operario`, `calidad` y `bodega`, todos con clave
`Clave123456`. El escritorio muestra a cada uno solo sus paneles y acciones.

## Diseno de la aplicacion web

El lenguaje visual sale del objeto que se fabrica. La **placa de
caracteristicas** remachada a cada transformador, con sus datos grabados en
una grilla de etiqueta y valor, es el dispositivo que organiza el catalogo,
las fichas y las cotizaciones.

| Decision | Motivo |
|---|---|
| Gris ANSI 70 en bordes y separadores | Es el color de pintura normalizado de los transformadores de distribucion |
| Cobre como unico acento | Es el material del bobinado |
| Amarillo de senalizacion electrica | Reservado solo para advertencias |
| Superficies planas con borde de 1 px | Chapa metalica, no tarjetas con sombra |
| Numeros tabulares en toda la interfaz | Cada cifra es una magnitud medida y debe alinearse |
| Archivo como unica familia tipografica | Grotesca de senaletica industrial |

La pagina de inicio no muestra tarjetas con metricas: muestra la cadena
documental completa y ubica los documentos del cliente en la etapa donde
estan. La cadena es el producto.

Bootstrap se sirve desde `static/vendor/` y no desde una CDN, de modo que el
sistema se vea correcto tambien sin conexion a internet.

## Servicios externos integrados

| Servicio | Uso | Requerimiento |
|---|---|---|
| mindicador.cl | Valor diario de UF, UTM y dolar | RF-PAG-05, RF-PAG-06 |
| Nager.Date | Feriados legales para plazos en dias habiles | RF-COM-08, RN-08 |
| PayPal (Sandbox) | Pago en linea de anticipos y saldos | RF-PAG-02 |
| Brevo | Correo transaccional: cotizaciones, acuses y comprobantes | RF-COM-09 |
| Geocodificacion | Validacion de direcciones | RF-CLI-05 |

La API REST propia corresponde a la arquitectura del sistema y no se
contabiliza dentro de ese total.

Los tres requerimientos de integracion se implementan en
`apps/configuracion/services/base.py`:

- **RF-INT-01**: toda llamada queda registrada en `log_integracion` con
  endpoint, codigo de respuesta, latencia y resultado.
- **RF-INT-02**: reintentos con espera incremental ante fallos transitorios.
  Un codigo 4xx no se reintenta.
- **RF-INT-03**: degradacion controlada. El cliente nunca propaga la excepcion
  de red al proceso de negocio: cuando mindicador.cl no responde, el sistema
  opera con el ultimo valor de UF almacenado e informa su fecha; cuando el
  servicio de feriados no responde, el plazo se calcula excluyendo solo
  sabados y domingos, y se advierte que requiere verificacion.

### Nota sobre el proveedor de feriados

La API del Estado (`apis.digital.gob.cl/fl`) fue descontinuada y su subdominio
ya no resuelve por DNS. El listado oficial de APIs publicas de Chile la marca
como DEPRECATED. Se intento migrar a `feriadito.cl`, que documenta una API de
archivos JSON estaticos, pero su sitio en produccion aun no la publica
(responde 404). El proveedor actual es Nager.Date
(`https://date.nager.at/api/v3/PublicHolidays/{anio}/CL`), publico, gratuito y
sin clave. Los feriados regionales (por ejemplo, los de Arica o Nuble) se
omiten para no correr plazos de empresas de otras regiones.

El cliente acepta los formatos de ambos proveedores, de modo que un nuevo
cambio de proveedor no obligue a reescribir el parser. La URL se configura en
`.env` mediante `FERIADOS_URL`.

Este episodio es, en si mismo, la justificacion de RF-INT-03: el proveedor
externo desaparecio y el sistema siguio calculando plazos con los feriados ya
almacenados.

### Pago en linea con PayPal (CU-PAG-02)

Codigo en `apps/pagos/services/` (`paypal.py` para la pasarela, `cobros.py`
para las reglas de negocio).

1. Al generar la orden de compra se emite el documento de cobro del anticipo,
   con la UF congelada (RN-03, RN-15) y vencimiento en dias habiles.
2. El cliente abre el documento desde Pedidos y paga con PayPal. PayPal no
   opera en pesos chilenos, por lo que el monto en pesos se convierte a USD
   con el dolar observado de mindicador.cl; la conversion queda registrada.
3. Al volver de PayPal se captura el pago y se concilia: el documento solo se
   marca pagado si el monto cobrado coincide exactamente (excepcion E7).
4. Si PayPal no responde al capturar, la transaccion queda pendiente de
   conciliacion y se resuelve con `python manage.py conciliar_pagos`.

Toda llamada que crea o captura envia `PayPal-Request-Id`, de modo que los
reintentos no generen cobros duplicados. El pago puede apagarse desde la
aplicacion de escritorio (panel Canal web) sin redesplegar.

Credenciales: crear una app en developer.paypal.com (modo Sandbox) y copiar
Client ID y Secret en `.env` (`PAYPAL_CLIENT_ID`, `PAYPAL_SECRET`). Para pagar
se usa la cuenta personal de prueba que PayPal crea en Sandbox Accounts.

### Correo transaccional con Brevo (RF-COM-09)

Codigo en `apps/configuracion/services/correo.py` (cliente y backend de
correo de Django) y `notificaciones.py` (que correo se envia en cada evento).
Plantillas en `templates/correo/`, cada una en version HTML y texto plano.

| Evento | Correo |
|---|---|
| El cliente envia una solicitud desde la web | Acuse de recibo |
| Se emite una cotizacion (API o accion del admin) | Cotizacion con detalle y enlace para responder |
| Se confirma un pago en linea | Comprobante con referencia de PayPal |

Se implementa como backend de correo de Django: el resto del sistema usa las
herramientas estandar de Django y no depende del proveedor. Sin
`BREVO_API_KEY`, en desarrollo los correos se imprimen en la consola del
contenedor. Un fallo del correo nunca revierte la operacion que lo origino, y
los correos se envian solo despues de confirmada la transaccion.

`CORREO_REDIRIGIR_A` desvia todos los correos a una direccion de prueba
(indicando en el asunto el destinatario original), para no escribir a los
clientes ficticios de los datos de demostracion.

## Pruebas

```bash
docker compose exec web pytest
```

138 pruebas automatizadas con 91% de cobertura sobre `apps/`, por encima del
70% exigido por RNF-13. Las llamadas a servicios externos (incluido PayPal) se
simulan con dobles de prueba.

## Convenciones

- Nombres de tabla y campo en minusculas, palabras separadas por guion bajo.
- Clave primaria sustituta `id_<tabla>`.
- Las entidades de negocio no se eliminan: se desactivan o se anulan.
- Montos en Unidades de Fomento con cuatro decimales.
- Fechas y horas en UTC, presentadas en horario de Chile.

## Metodologia

Scrum, aplicada de principio a fin. Cada mensaje de commit referencia la historia
de usuario que resuelve, con el formato:

```
HU-12: agregar validacion de RUT en el registro de cliente
```

## Documentacion del proyecto

| Documento | Contenido |
|---|---|
| ERS-01 | Toma de requerimientos |
| CU-01 | Modelo de casos de uso |
| MER-01 | Modelo de datos y diccionario |
