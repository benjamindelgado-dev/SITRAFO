--
-- PostgreSQL database dump
--

\restrict 2h5fweI90gBZT6fnwBIe5jRrNApeVCUqzrQScsVcPmYsubYm98iQqrcut5FHNSy

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: cliente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cliente (creado_en, modificado_en, id_cliente, rut, razon_social, nombre_fantasia, tipo_persona, giro, estado) FROM stdin;
2026-09-23 10:12:06.580142+00	2026-09-23 10:12:06.580164+00	1	11111111-1	Cliente de prueba SpA		natural	aaa	activo
2026-09-25 02:13:36.150067+00	2026-09-25 02:13:36.150078+00	4	76543210-3	Electrica del Maipo SpA		juridica	Distribucion electrica	activo
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario (password, last_login, id_usuario, username, email, es_interno, estado, intentos_fallidos, ultimo_acceso, is_staff, is_superuser, is_active, creado_en, id_cliente, bloqueado_hasta) FROM stdin;
pbkdf2_sha256$870000$L69qRdfjhrGHRVGsajXvZD$0BQ1RsRBrc50FN0h5jyqPIie4xowozdYUT8pIXxV4Yw=	2026-09-25 08:16:47.426273+00	7	ejecutivo	ejecutivo@sitrafo.cl	t	activo	0	\N	t	t	t	2026-09-25 02:13:35.769171+00	\N	\N
!ClaveNoUtilizable	2026-09-25 18:45:39.028533+00	1	benjaadb	superusuario@sitrafo.cl	t	activo	0	2026-09-25 20:12:51.62202+00	t	t	t	2026-09-23 09:21:47.67586+00	\N	\N
pbkdf2_sha256$870000$s6y252O8HtR7Zz52RQYULO$qaVz5Qqry6sF95n/mTr+9rIN9U2IbejTpI+6uH0Jiog=	\N	11	comercial2	comercial2@sitrafo.cl	t	activo	0	\N	f	f	t	2026-09-25 09:04:52.790567+00	\N	\N
pbkdf2_sha256$870000$7yEYqiqv2JzvyJNcPxaQY7$mT1kBTVh9YsENFzFmqNnQ9IEPHozEtI5uGqqA0gqvHU=	\N	12	produccion	produccion@sitrafo.cl	t	activo	0	2026-09-29 12:34:30.477853+00	f	f	t	2026-09-25 09:04:53.190295+00	\N	\N
pbkdf2_sha256$870000$dIijxAhmha6bcgRwqxxHfH$yd/+Gt7Vk1eOIclbIr5672IrkMyQrzObD88fFExjt5U=	2026-09-25 18:01:38.638527+00	10	comercial	comercial@sitrafo.cl	t	activo	0	2026-09-29 12:40:32.534863+00	f	f	t	2026-09-25 09:04:52.410458+00	\N	\N
pbkdf2_sha256$870000$SMwf7u7YbuFv38eZpuohP5$61V1jaXL/LYN3Gjj8r4BvqMf3JKu7ZMZ2JFxdzwrknM=	2026-09-25 07:24:28.556945+00	2	prueba1	prueba1@gmail.com	f	activo	0	\N	f	f	t	2026-09-23 10:12:06.990808+00	1	\N
pbkdf2_sha256$870000$oFapp0rErd3pyWa3ObO7P5$wkg7i01MpvmgQmrvCq/FKUzK2ExuqUrzsIGNk2vTk6s=	\N	9	administrador	administrador@sitrafo.cl	t	activo	0	2026-09-29 13:01:07.58262+00	f	f	t	2026-09-25 09:04:52.011946+00	\N	\N
pbkdf2_sha256$870000$6DbtCbIDxSsONVAFkUlyAV$ntZK5il4Pml54ulspz+cpAhbZekQBFn/v8sLdS/GgxQ=	2026-09-25 18:02:20.573481+00	13	operario	operario@sitrafo.cl	t	activo	0	2026-09-25 20:42:28.895048+00	f	f	t	2026-09-25 09:04:53.571615+00	\N	\N
pbkdf2_sha256$870000$W3VW5txbWhzxD5OIx4LO9h$wqlsl4OKBQbGY/cn3XGqmO7W7qRT7Oxi9lsTfxOos90=	2026-09-29 14:18:49.095682+00	8	maipo	contacto@maipo.cl	f	activo	0	2026-09-29 14:18:49.075441+00	f	f	t	2026-09-25 02:13:36.158184+00	4	\N
pbkdf2_sha256$870000$oZXWoLPS1ydEDcQom949GW$WcxROc8l20efURoPA4hfu4Doci9F3EAsrFFQHUO3cvw=	\N	16	mdiaz	mdiaz@gmail.com	t	activo	0	2026-09-25 20:50:38.833876+00	f	f	t	2026-09-25 18:47:01.235821+00	\N	\N
pbkdf2_sha256$870000$AlxhgFC0UUrh2plGn5XAHF$j52W8V6mYwRuQOldMa/dz4cNzxclyXcaBUjtRGx9y1A=	\N	14	calidad	calidad@sitrafo.cl	t	activo	0	2026-09-25 20:52:28.597394+00	f	f	t	2026-09-25 09:04:53.942657+00	\N	\N
pbkdf2_sha256$870000$LPpwWJfNZYmwNbgHMXoCCu$dulTnYTnxt0bOTxvrKIU7RNVPdDajeVy0b5c5cK+3J4=	\N	15	bodega	bodega@sitrafo.cl	t	activo	0	2026-09-26 02:29:41.72262+00	f	f	t	2026-09-25 09:04:54.328956+00	\N	\N
\.


--
-- Data for Name: auditoria; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auditoria (id_auditoria, entidad, id_registro, accion, valor_anterior, valor_nuevo, fecha_hora, origen, id_usuario) FROM stdin;
1	parametro_sistema	web.pago_en_linea_habilitado	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-24 09:54:30.682733+00	escritorio	1
2	parametro_sistema	web.pago_en_linea_habilitado	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-24 09:54:31.021109+00	escritorio	1
3	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-24 09:54:31.401988+00	escritorio	1
4	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-24 09:54:34.199019+00	escritorio	1
5	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-24 09:56:51.290367+00	escritorio	1
6	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-24 09:59:36.799767+00	escritorio	1
7	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-24 10:00:37.393881+00	escritorio	1
8	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-24 10:00:47.086018+00	escritorio	1
9	documento_cobro	1	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "2WF72195YD9756041"}	2026-09-25 02:33:35.014605+00	web	8
10	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-25 02:34:43.153808+00	escritorio	1
11	parametro_sistema	web.mensaje_mantencion	modificacion	{"valor": "Sitio en mantencion. Volvemos pronto."}	{"valor": "Sitio en mantencion. Volvemos pronto.asdasdasd"}	2026-09-25 02:34:50.855293+00	escritorio	1
12	parametro_sistema	web.mensaje_mantencion	modificacion	{"valor": "Sitio en mantencion. Volvemos pronto.asdasdasd"}	{"valor": "Sitio en mantencion. Volvemos pronto."}	2026-09-25 02:34:58.61159+00	escritorio	1
13	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-25 02:35:49.160826+00	escritorio	1
14	parametro_sistema	web.mensaje_mantencion	modificacion	{"valor": "Sitio en mantencion. Volvemos pronto."}	{"valor": "Sitio en mantencion. Volvemos pronto."}	2026-09-25 02:35:53.921122+00	escritorio	1
15	documento_cobro	2	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "6MP02347FF579830B"}	2026-09-25 07:59:30.138441+00	web	8
16	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-25 08:00:37.79254+00	escritorio	7
17	parametro_sistema	web.modo_mantencion	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-25 08:00:45.966051+00	escritorio	7
18	parametro_sistema	web.mensaje_mantencion	modificacion	{"valor": "Sitio en mantencion. Volvemos pronto."}	{"valor": "Sitio en mantencion. Volvemos pronto."}	2026-09-25 08:00:47.062386+00	escritorio	7
19	documento_cobro	3	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "2CG96871FV821860R"}	2026-09-25 08:22:11.296803+00	web	8
20	documento_cobro	4	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "167871419F152234B"}	2026-09-25 18:07:12.046232+00	web	8
21	modelo_producto	13	creacion	\N	{"codigo": "TD-750", "nombre": "Transformador de Tritio"}	2026-09-25 18:29:54.371905+00	escritorio	9
22	modelo_producto	13	modificacion	{"precio_base_uf": null}	{"precio_base_uf": "100.0000"}	2026-09-25 18:29:54.398118+00	escritorio	9
23	modelo_producto	12	modificacion	{"precio_base_uf": null}	{"precio_base_uf": "1000.0000"}	2026-09-25 18:30:18.432841+00	escritorio	9
24	modelo_producto	12	modificacion	{"precio_base_uf": "1000.0000"}	{"precio_base_uf": "220.0000"}	2026-09-25 18:31:08.077558+00	escritorio	9
25	modelo_producto	13	modificacion	{"publicado": false}	{"publicado": true}	2026-09-25 18:31:24.510587+00	escritorio	9
26	usuario	12	modificacion	{"estado": "bloqueado"}	{"estado": "activo"}	2026-09-25 19:16:41.459903+00	escritorio	9
27	no_conformidad	1	modificacion	{"estado": "abierta"}	{"accion": "asdasdasdasdasdasd", "estado": "cerrada"}	2026-09-25 19:51:41.120312+00	escritorio	14
28	no_conformidad	2	modificacion	{"estado": "abierta"}	{"accion": "4553453453453", "estado": "cerrada"}	2026-09-25 19:53:16.58443+00	escritorio	14
29	protocolo_calidad	1	modificacion	\N	{"puntos": 8}	2026-09-25 19:54:36.179241+00	escritorio	14
30	no_conformidad	3	modificacion	{"estado": "abierta"}	{"accion": "adfasdasdas", "estado": "cerrada"}	2026-09-25 20:01:49.250267+00	escritorio	14
31	documento_cobro	5	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "06N30997C8643492G"}	2026-09-25 20:08:20.642739+00	web	8
32	documento_cobro	6	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "5ME23869JX4590734"}	2026-09-25 20:11:35.173577+00	web	8
33	protocolo_calidad	5	creacion	\N	{"modelo": "TD-100", "nombre": "Ensayos de rutina", "version": 2}	2026-09-25 20:12:32.527101+00	escritorio	14
34	documento_cobro	8	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "26V21497HC984222R"}	2026-09-25 20:36:36.222181+00	web	8
35	documento_cobro	9	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "1Y261100CC6822530"}	2026-09-25 20:48:07.479244+00	web	8
36	no_conformidad	4	modificacion	{"estado": "abierta"}	{"accion": "error de seleccion", "estado": "cerrada"}	2026-09-25 20:54:30.582362+00	escritorio	14
37	documento_cobro	10	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "0G245954Y94744203"}	2026-09-25 20:57:23.656808+00	web	8
38	parametro_sistema	web.autorregistro_habilitado	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-25 20:59:39.044372+00	escritorio	9
39	parametro_sistema	web.autorregistro_habilitado	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-25 20:59:39.387117+00	escritorio	9
40	parametro_sistema	web.pago_en_linea_habilitado	modificacion	{"valor": "true"}	{"valor": "false"}	2026-09-25 20:59:40.874004+00	escritorio	9
41	parametro_sistema	web.pago_en_linea_habilitado	modificacion	{"valor": "false"}	{"valor": "true"}	2026-09-25 20:59:42.049583+00	escritorio	9
42	cuenta_web	8	modificacion	{"estado": "activo"}	{"estado": "suspendido", "cliente": "Electrica del Maipo SpA"}	2026-09-29 12:09:15.300479+00	escritorio	10
43	cuenta_web	8	modificacion	{"estado": "suspendido"}	{"estado": "suspendido", "cliente": "Electrica del Maipo SpA"}	2026-09-29 12:09:34.252936+00	escritorio	10
44	cuenta_web	8	modificacion	{"estado": "suspendido"}	{"estado": "suspendido", "cliente": "Electrica del Maipo SpA"}	2026-09-29 12:09:37.373148+00	escritorio	10
45	cuenta_web	8	modificacion	{"estado": "suspendido"}	{"estado": "activo", "cliente": "Electrica del Maipo SpA"}	2026-09-29 12:09:40.304602+00	escritorio	10
46	modelo_producto	14	creacion	\N	{"codigo": "t800", "nombre": "t800prueba"}	2026-09-29 12:33:44.816494+00	escritorio	9
47	modelo_producto	14	modificacion	{"precio_base_uf": null}	{"precio_base_uf": "799.0000"}	2026-09-29 12:33:44.840169+00	escritorio	9
48	modelo_producto	14	modificacion	{"publicado": false}	{"publicado": true}	2026-09-29 12:33:49.196094+00	escritorio	9
49	modelo_producto	14	modificacion	{"publicado": true}	{"publicado": false}	2026-09-29 12:34:03.965151+00	escritorio	9
50	modelo_producto	14	modificacion	{"publicado": false}	{"publicado": true}	2026-09-29 12:34:08.6257+00	escritorio	9
51	modelo_producto	14	modificacion	{"tareas": 0, "materiales": 0}	{"tareas": 3, "materiales": 3}	2026-09-29 12:36:36.701739+00	escritorio	12
52	cotizacion	10	anulacion	{"estado": "borrador", "numero": "COT-2026-0008"}	{"estado": "anulada", "motivo": "anular prueba"}	2026-09-29 12:44:20.280559+00	escritorio	10
53	empleado	4	modificacion	{"valor_hora_uf": null}	{"valor_hora_uf": "10.0000", "vigente_desde": "2026-09-29"}	2026-09-29 13:03:59.215785+00	escritorio	9
54	empleado	4	modificacion	{"valor_hora_uf": "10.0000"}	{"valor_hora_uf": "10.0000", "vigente_desde": "2026-09-29"}	2026-09-29 13:05:12.595848+00	escritorio	9
55	rol	1	modificacion	{"permiso": "taller.leer", "otorgado": false}	{"rol": "Administrador", "permiso": "taller.leer", "otorgado": true}	2026-09-29 13:08:23.333355+00	escritorio	9
56	rol	1	modificacion	{"permiso": "taller.leer", "otorgado": true}	{"rol": "Administrador", "permiso": "taller.leer", "otorgado": false}	2026-09-29 13:08:23.788388+00	escritorio	9
57	rol	1	modificacion	{"permiso": "taller.leer", "otorgado": false}	{"rol": "Administrador", "permiso": "taller.leer", "otorgado": true}	2026-09-29 13:08:25.300873+00	escritorio	9
58	rol	1	modificacion	{"permiso": "taller.leer", "otorgado": true}	{"rol": "Administrador", "permiso": "taller.leer", "otorgado": false}	2026-09-29 13:08:25.903155+00	escritorio	9
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	seguridad	permiso
7	seguridad	rol
8	seguridad	usuario
9	seguridad	usuariorol
10	seguridad	auditoria
11	seguridad	rolpermiso
12	clientes	cliente
13	clientes	comuna
14	clientes	region
15	clientes	contactocliente
16	clientes	direccioncliente
17	catalogo	familiaproducto
18	catalogo	parametrotecnico
19	catalogo	modeloproducto
20	catalogo	modeloparametro
21	catalogo	preciobasemodelo
22	catalogo	tareaestandarmodelo
23	catalogo	valorparametro
24	catalogo	bommodelo
25	inventario	bodega
26	inventario	categoriamaterial
27	inventario	proveedor
28	inventario	material
29	inventario	preciomaterial
30	comercial	cotizacion
31	comercial	cotizacionlinea
32	comercial	estadodocumento
33	comercial	cotizacionhistorial
34	comercial	ordencompra
35	comercial	ordencomprahistorial
36	comercial	ordencompralinea
37	comercial	solicitudpresupuesto
38	comercial	solicitudhistorial
39	comercial	solicitudespecificacion
40	produccion	empleado
41	produccion	ordentrabajo
42	produccion	ordentrabajohistorial
43	produccion	tareaot
44	produccion	registrohorahombre
45	produccion	consumomaterial
46	produccion	tarifahorahombre
47	inventario	movimientoinventario
48	calidad	noconformidad
49	calidad	protocolocalidad
50	calidad	puntocontrol
51	calidad	resultadocontrol
52	calidad	controlcalidad
53	pagos	documentocobro
54	pagos	indicadoreconomico
55	pagos	transaccionpago
56	configuracion	feriado
57	configuracion	avisositio
58	configuracion	logintegracion
59	configuracion	parametrosistema
60	token_blacklist	blacklistedtoken
61	token_blacklist	outstandingtoken
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add permiso	6	add_permiso
22	Can change permiso	6	change_permiso
23	Can delete permiso	6	delete_permiso
24	Can view permiso	6	view_permiso
25	Can add rol	7	add_rol
26	Can change rol	7	change_rol
27	Can delete rol	7	delete_rol
28	Can view rol	7	view_rol
29	Can add usuario	8	add_usuario
30	Can change usuario	8	change_usuario
31	Can delete usuario	8	delete_usuario
32	Can view usuario	8	view_usuario
33	Can add rol de usuario	9	add_usuariorol
34	Can change rol de usuario	9	change_usuariorol
35	Can delete rol de usuario	9	delete_usuariorol
36	Can view rol de usuario	9	view_usuariorol
37	Can add registro de auditoria	10	add_auditoria
38	Can change registro de auditoria	10	change_auditoria
39	Can delete registro de auditoria	10	delete_auditoria
40	Can view registro de auditoria	10	view_auditoria
41	Can add permiso de rol	11	add_rolpermiso
42	Can change permiso de rol	11	change_rolpermiso
43	Can delete permiso de rol	11	delete_rolpermiso
44	Can view permiso de rol	11	view_rolpermiso
45	Can add cliente	12	add_cliente
46	Can change cliente	12	change_cliente
47	Can delete cliente	12	delete_cliente
48	Can view cliente	12	view_cliente
49	Can add comuna	13	add_comuna
50	Can change comuna	13	change_comuna
51	Can delete comuna	13	delete_comuna
52	Can view comuna	13	view_comuna
53	Can add region	14	add_region
54	Can change region	14	change_region
55	Can delete region	14	delete_region
56	Can view region	14	view_region
57	Can add contacto de cliente	15	add_contactocliente
58	Can change contacto de cliente	15	change_contactocliente
59	Can delete contacto de cliente	15	delete_contactocliente
60	Can view contacto de cliente	15	view_contactocliente
61	Can add direccion de cliente	16	add_direccioncliente
62	Can change direccion de cliente	16	change_direccioncliente
63	Can delete direccion de cliente	16	delete_direccioncliente
64	Can view direccion de cliente	16	view_direccioncliente
65	Can add familia de producto	17	add_familiaproducto
66	Can change familia de producto	17	change_familiaproducto
67	Can delete familia de producto	17	delete_familiaproducto
68	Can view familia de producto	17	view_familiaproducto
69	Can add parametro tecnico	18	add_parametrotecnico
70	Can change parametro tecnico	18	change_parametrotecnico
71	Can delete parametro tecnico	18	delete_parametrotecnico
72	Can view parametro tecnico	18	view_parametrotecnico
73	Can add modelo de producto	19	add_modeloproducto
74	Can change modelo de producto	19	change_modeloproducto
75	Can delete modelo de producto	19	delete_modeloproducto
76	Can view modelo de producto	19	view_modeloproducto
77	Can add parametro del modelo	20	add_modeloparametro
78	Can change parametro del modelo	20	change_modeloparametro
79	Can delete parametro del modelo	20	delete_modeloparametro
80	Can view parametro del modelo	20	view_modeloparametro
81	Can add precio base de modelo	21	add_preciobasemodelo
82	Can change precio base de modelo	21	change_preciobasemodelo
83	Can delete precio base de modelo	21	delete_preciobasemodelo
84	Can view precio base de modelo	21	view_preciobasemodelo
85	Can add tarea estandar del modelo	22	add_tareaestandarmodelo
86	Can change tarea estandar del modelo	22	change_tareaestandarmodelo
87	Can delete tarea estandar del modelo	22	delete_tareaestandarmodelo
88	Can view tarea estandar del modelo	22	view_tareaestandarmodelo
89	Can add valor de parametro	23	add_valorparametro
90	Can change valor de parametro	23	change_valorparametro
91	Can delete valor de parametro	23	delete_valorparametro
92	Can view valor de parametro	23	view_valorparametro
93	Can add material del modelo	24	add_bommodelo
94	Can change material del modelo	24	change_bommodelo
95	Can delete material del modelo	24	delete_bommodelo
96	Can view material del modelo	24	view_bommodelo
97	Can add bodega	25	add_bodega
98	Can change bodega	25	change_bodega
99	Can delete bodega	25	delete_bodega
100	Can view bodega	25	view_bodega
101	Can add categoria de material	26	add_categoriamaterial
102	Can change categoria de material	26	change_categoriamaterial
103	Can delete categoria de material	26	delete_categoriamaterial
104	Can view categoria de material	26	view_categoriamaterial
105	Can add proveedor	27	add_proveedor
106	Can change proveedor	27	change_proveedor
107	Can delete proveedor	27	delete_proveedor
108	Can view proveedor	27	view_proveedor
109	Can add material	28	add_material
110	Can change material	28	change_material
111	Can delete material	28	delete_material
112	Can view material	28	view_material
113	Can add precio de material	29	add_preciomaterial
114	Can change precio de material	29	change_preciomaterial
115	Can delete precio de material	29	delete_preciomaterial
116	Can view precio de material	29	view_preciomaterial
117	Can add cotizacion	30	add_cotizacion
118	Can change cotizacion	30	change_cotizacion
119	Can delete cotizacion	30	delete_cotizacion
120	Can view cotizacion	30	view_cotizacion
121	Can add linea de cotizacion	31	add_cotizacionlinea
122	Can change linea de cotizacion	31	change_cotizacionlinea
123	Can delete linea de cotizacion	31	delete_cotizacionlinea
124	Can view linea de cotizacion	31	view_cotizacionlinea
125	Can add estado de documento	32	add_estadodocumento
126	Can change estado de documento	32	change_estadodocumento
127	Can delete estado de documento	32	delete_estadodocumento
128	Can view estado de documento	32	view_estadodocumento
129	Can add historial de la cotizacion	33	add_cotizacionhistorial
130	Can change historial de la cotizacion	33	change_cotizacionhistorial
131	Can delete historial de la cotizacion	33	delete_cotizacionhistorial
132	Can view historial de la cotizacion	33	view_cotizacionhistorial
133	Can add orden de compra	34	add_ordencompra
134	Can change orden de compra	34	change_ordencompra
135	Can delete orden de compra	34	delete_ordencompra
136	Can view orden de compra	34	view_ordencompra
137	Can add historial de la orden de compra	35	add_ordencomprahistorial
138	Can change historial de la orden de compra	35	change_ordencomprahistorial
139	Can delete historial de la orden de compra	35	delete_ordencomprahistorial
140	Can view historial de la orden de compra	35	view_ordencomprahistorial
141	Can add linea de orden de compra	36	add_ordencompralinea
142	Can change linea de orden de compra	36	change_ordencompralinea
143	Can delete linea de orden de compra	36	delete_ordencompralinea
144	Can view linea de orden de compra	36	view_ordencompralinea
145	Can add solicitud de presupuesto	37	add_solicitudpresupuesto
146	Can change solicitud de presupuesto	37	change_solicitudpresupuesto
147	Can delete solicitud de presupuesto	37	delete_solicitudpresupuesto
148	Can view solicitud de presupuesto	37	view_solicitudpresupuesto
149	Can add historial de la solicitud	38	add_solicitudhistorial
150	Can change historial de la solicitud	38	change_solicitudhistorial
151	Can delete historial de la solicitud	38	delete_solicitudhistorial
152	Can view historial de la solicitud	38	view_solicitudhistorial
153	Can add especificacion de la solicitud	39	add_solicitudespecificacion
154	Can change especificacion de la solicitud	39	change_solicitudespecificacion
155	Can delete especificacion de la solicitud	39	delete_solicitudespecificacion
156	Can view especificacion de la solicitud	39	view_solicitudespecificacion
157	Can add empleado	40	add_empleado
158	Can change empleado	40	change_empleado
159	Can delete empleado	40	delete_empleado
160	Can view empleado	40	view_empleado
161	Can add orden de trabajo	41	add_ordentrabajo
162	Can change orden de trabajo	41	change_ordentrabajo
163	Can delete orden de trabajo	41	delete_ordentrabajo
164	Can view orden de trabajo	41	view_ordentrabajo
165	Can add historial de la orden de trabajo	42	add_ordentrabajohistorial
166	Can change historial de la orden de trabajo	42	change_ordentrabajohistorial
167	Can delete historial de la orden de trabajo	42	delete_ordentrabajohistorial
168	Can view historial de la orden de trabajo	42	view_ordentrabajohistorial
169	Can add tarea de la orden de trabajo	43	add_tareaot
170	Can change tarea de la orden de trabajo	43	change_tareaot
171	Can delete tarea de la orden de trabajo	43	delete_tareaot
172	Can view tarea de la orden de trabajo	43	view_tareaot
173	Can add registro de horas hombre	44	add_registrohorahombre
174	Can change registro de horas hombre	44	change_registrohorahombre
175	Can delete registro de horas hombre	44	delete_registrohorahombre
176	Can view registro de horas hombre	44	view_registrohorahombre
177	Can add consumo de material	45	add_consumomaterial
178	Can change consumo de material	45	change_consumomaterial
179	Can delete consumo de material	45	delete_consumomaterial
180	Can view consumo de material	45	view_consumomaterial
181	Can add tarifa de hora hombre	46	add_tarifahorahombre
182	Can change tarifa de hora hombre	46	change_tarifahorahombre
183	Can delete tarifa de hora hombre	46	delete_tarifahorahombre
184	Can view tarifa de hora hombre	46	view_tarifahorahombre
185	Can add movimiento de inventario	47	add_movimientoinventario
186	Can change movimiento de inventario	47	change_movimientoinventario
187	Can delete movimiento de inventario	47	delete_movimientoinventario
188	Can view movimiento de inventario	47	view_movimientoinventario
189	Can add no conformidad	48	add_noconformidad
190	Can change no conformidad	48	change_noconformidad
191	Can delete no conformidad	48	delete_noconformidad
192	Can view no conformidad	48	view_noconformidad
193	Can add protocolo de calidad	49	add_protocolocalidad
194	Can change protocolo de calidad	49	change_protocolocalidad
195	Can delete protocolo de calidad	49	delete_protocolocalidad
196	Can view protocolo de calidad	49	view_protocolocalidad
197	Can add punto de control	50	add_puntocontrol
198	Can change punto de control	50	change_puntocontrol
199	Can delete punto de control	50	delete_puntocontrol
200	Can view punto de control	50	view_puntocontrol
201	Can add resultado de control	51	add_resultadocontrol
202	Can change resultado de control	51	change_resultadocontrol
203	Can delete resultado de control	51	delete_resultadocontrol
204	Can view resultado de control	51	view_resultadocontrol
205	Can add control de calidad	52	add_controlcalidad
206	Can change control de calidad	52	change_controlcalidad
207	Can delete control de calidad	52	delete_controlcalidad
208	Can view control de calidad	52	view_controlcalidad
209	Can add documento de cobro	53	add_documentocobro
210	Can change documento de cobro	53	change_documentocobro
211	Can delete documento de cobro	53	delete_documentocobro
212	Can view documento de cobro	53	view_documentocobro
213	Can add indicador economico	54	add_indicadoreconomico
214	Can change indicador economico	54	change_indicadoreconomico
215	Can delete indicador economico	54	delete_indicadoreconomico
216	Can view indicador economico	54	view_indicadoreconomico
217	Can add transaccion de pago	55	add_transaccionpago
218	Can change transaccion de pago	55	change_transaccionpago
219	Can delete transaccion de pago	55	delete_transaccionpago
220	Can view transaccion de pago	55	view_transaccionpago
221	Can add feriado	56	add_feriado
222	Can change feriado	56	change_feriado
223	Can delete feriado	56	delete_feriado
224	Can view feriado	56	view_feriado
225	Can add aviso del sitio	57	add_avisositio
226	Can change aviso del sitio	57	change_avisositio
227	Can delete aviso del sitio	57	delete_avisositio
228	Can view aviso del sitio	57	view_avisositio
229	Can add llamada a servicio externo	58	add_logintegracion
230	Can change llamada a servicio externo	58	change_logintegracion
231	Can delete llamada a servicio externo	58	delete_logintegracion
232	Can view llamada a servicio externo	58	view_logintegracion
233	Can add parametro del sistema	59	add_parametrosistema
234	Can change parametro del sistema	59	change_parametrosistema
235	Can delete parametro del sistema	59	delete_parametrosistema
236	Can view parametro del sistema	59	view_parametrosistema
237	Can add blacklisted token	60	add_blacklistedtoken
238	Can change blacklisted token	60	change_blacklistedtoken
239	Can delete blacklisted token	60	delete_blacklistedtoken
240	Can view blacklisted token	60	view_blacklistedtoken
241	Can add outstanding token	61	add_outstandingtoken
242	Can change outstanding token	61	change_outstandingtoken
243	Can delete outstanding token	61	delete_outstandingtoken
244	Can view outstanding token	61	view_outstandingtoken
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: aviso_sitio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.aviso_sitio (id_aviso, titulo, cuerpo, tipo, vigente_desde, vigente_hasta, activo, id_usuario) FROM stdin;
1	aviso de prueba	aviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de prueba	informativo	2026-09-29 13:06:28+00	2026-10-06 13:07:28+00	f	9
3	aviso de pruebaaviso de prueba	aviso de pruebaaviso de prueba	advertencia	2026-09-29 13:07:10+00	2026-10-07 13:09:10+00	f	9
4	aviso de prueba	aviso de prueba	informativo	2026-09-29 13:07:30+00	2026-10-06 13:09:30+00	f	9
2	aviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de prueba	aviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de pruebaaviso de prueba	advertencia	2026-09-30 13:07:44+00	2026-10-07 13:09:44+00	f	9
\.


--
-- Data for Name: bodega; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bodega (activo, id_bodega, codigo, nombre, ubicacion) FROM stdin;
t	1	B1	Bodega central	Planta
\.


--
-- Data for Name: categoria_material; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categoria_material (activo, id_categoria, nombre) FROM stdin;
t	1	Nucleo
t	2	Conductores
t	3	Aislantes
t	4	Accesorios
t	5	Estructura
\.


--
-- Data for Name: familia_producto; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.familia_producto (activo, id_familia, nombre, descripcion) FROM stdin;
t	5	Distribucion trifasicos	
t	6	Distribucion monofasicos	
\.


--
-- Data for Name: material; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.material (activo, id_material, codigo, nombre, unidad_medida, stock_minimo, id_categoria) FROM stdin;
t	1	ACE-SI	Acero al silicio grano orientado	kg	500.0000	1
t	2	CU-ESM	Alambre de cobre esmaltado	kg	200.0000	2
t	4	AIS-BT	Aislador pasatapas BT	un	20.0000	4
t	5	AIS-AT	Aislador pasatapas AT	un	15.0000	4
t	6	TNQ-01	Tanque de acero con radiadores	un	4.0000	5
t	3	ACT-DIE	Aceite dielectrico mineral	l	400.0000	3
\.


--
-- Data for Name: modelo_producto; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modelo_producto (activo, id_modelo, codigo, nombre, descripcion, publicado, id_familia) FROM stdin;
t	9	TD-050	Transformador de distribucion 50 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	5
t	10	TD-100	Transformador de distribucion 100 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	5
t	11	TD-250	Transformador de distribucion 250 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	5
t	12	TM-025	Transformador monofasico 25 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	6
t	13	TD-750	Transformador de Tritio	Transformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de TritioTransformador de Tritio	t	5
t	14	t800	t800prueba	t800pruebat800pruebat800pruebat800pruebat800pruebat800pruebat800prueba	t	6
\.


--
-- Data for Name: bom_modelo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bom_modelo (id_bom, cantidad, observacion, id_material, id_modelo) FROM stdin;
1	108.0000		1	9
2	36.0000		2	9
3	90.0000		3	9
4	2.0000		4	9
5	2.0000		5	9
6	1.0000		6	9
7	180.0000		1	10
8	60.0000		2	10
9	150.0000		3	10
10	4.0000		4	10
11	3.0000		5	10
12	1.0000		6	10
13	360.0000		1	11
14	120.0000		2	11
15	300.0000		3	11
16	8.0000		4	11
17	6.0000		5	11
18	2.0000		6	11
19	63.0000		1	12
20	21.0000		2	12
21	52.5000		3	12
22	1.0000		4	12
23	1.0000		5	12
24	1.0000		6	12
25	17.0000		1	14
26	10.0000		2	14
27	137.0000		6	14
\.


--
-- Data for Name: region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.region (id_region, nombre, codigo) FROM stdin;
3	Metropolitana de Santiago	RM
\.


--
-- Data for Name: comuna; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.comuna (id_comuna, nombre, id_region) FROM stdin;
3	Puente Alto	3
\.


--
-- Data for Name: direccion_cliente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.direccion_cliente (id_direccion, tipo, calle, numero, latitud, longitud, validada, id_cliente, id_comuna) FROM stdin;
3	instalacion	Av. Concha y Toro	2450	\N	\N	f	4	3
\.


--
-- Data for Name: estado_documento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estado_documento (id_estado, tipo_documento, codigo, nombre, es_final) FROM stdin;
1	solicitud	recibida	Recibida	f
2	solicitud	asignada	Asignada	f
3	solicitud	cotizada	Cotizada	f
4	solicitud	desestimada	Desestimada	t
5	cotizacion	borrador	Borrador	f
6	cotizacion	en_aprobacion	En aprobacion	f
7	cotizacion	emitida	Emitida	f
8	cotizacion	aceptada	Aceptada	t
9	cotizacion	rechazada	Rechazada	t
10	cotizacion	vencida	Vencida	t
11	cotizacion	anulada	Anulada	t
12	orden_compra	pendiente	Pendiente	f
13	orden_compra	confirmada	Confirmada	f
14	orden_compra	en_produccion	En produccion	f
15	orden_compra	entregada	Entregada	t
16	orden_compra	anulada	Anulada	t
17	orden_trabajo	planificada	Planificada	f
18	orden_trabajo	en_ejecucion	En ejecucion	f
19	orden_trabajo	en_calidad	En control de calidad	f
20	orden_trabajo	cerrada	Cerrada	t
21	orden_trabajo	anulada	Anulada	t
\.


--
-- Data for Name: solicitud_presupuesto; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitud_presupuesto (creado_en, modificado_en, id_solicitud, numero, cantidad, fecha_deseada, id_cliente, id_direccion, id_ejecutivo, id_estado, id_modelo) FROM stdin;
2026-09-25 02:13:36.620006+00	2026-09-25 02:13:36.620015+00	4	SP-2026-0002	2	2026-12-01	4	\N	\N	3	10
2026-09-25 07:28:10.841019+00	2026-09-25 07:28:10.841033+00	6	SP-2026-0004	2	2026-09-30	4	3	\N	1	9
2026-09-25 07:38:01.075829+00	2026-09-25 07:38:01.075842+00	7	SP-2026-0005	2	2026-09-26	4	3	\N	1	\N
2026-09-25 07:47:40.630456+00	2026-09-25 07:47:40.630469+00	8	SP-2026-0006	4	2026-09-27	4	3	7	2	12
2026-09-25 08:18:13.745571+00	2026-09-25 08:18:13.745584+00	9	SP-2026-0007	10	2026-10-02	4	3	7	3	9
2026-09-25 18:04:12.423738+00	2026-09-25 18:04:12.423751+00	10	SP-2026-0008	12	2026-09-30	4	3	10	3	10
2026-09-23 10:12:28.801897+00	2026-09-23 10:12:28.801913+00	1	SP-2026-0001	1	\N	1	\N	10	2	\N
2026-09-25 18:32:09.85449+00	2026-09-25 18:32:09.854501+00	11	SP-2026-0009	1	2026-09-30	4	3	10	3	13
2026-09-25 20:33:19.683045+00	2026-09-25 20:33:19.683057+00	12	SP-2026-0010	2	2026-09-29	4	3	10	3	13
2026-09-25 20:44:42.985881+00	2026-09-25 20:44:42.985895+00	13	SP-2026-0011	2	2026-09-28	4	3	10	3	11
2026-09-25 02:13:36.63388+00	2026-09-25 02:13:36.633889+00	5	SP-2026-0003	1	\N	4	\N	10	2	11
\.


--
-- Data for Name: cotizacion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotizacion (creado_en, modificado_en, id_cotizacion, numero, version, valor_uf, fecha_valor_uf, total_uf, descuento_pct, plazo_dias_habiles, fecha_entrega, vence_el, id_cliente, id_ejecutivo, id_estado, id_solicitud) FROM stdin;
2026-09-25 02:13:36.653118+00	2026-09-25 02:13:36.653126+00	2	COT-2026-0002	1	39980.00	2026-08-05	118.5000	0.00	\N	\N	2026-09-04	4	7	8	4
2026-09-25 02:13:36.640805+00	2026-09-25 02:13:36.640813+00	1	COT-2026-0001	1	40125.50	2026-09-20	412.6000	0.00	25	2026-10-28	2026-10-20	4	7	8	4
2026-09-25 07:53:26.066841+00	2026-09-25 07:53:26.066852+00	3	SP-2026-0006	1	41008.10	2026-09-25	300.0000	0.00	25	\N	2026-10-08	4	7	8	8
2026-09-25 08:18:38.419361+00	2026-09-25 08:18:38.41937+00	4	COT-2026-0003	1	41008.10	2026-09-24	1185.0000	0.00	30	2026-11-09	2026-10-25	4	7	8	9
2026-09-25 18:04:31.391424+00	2026-09-25 18:04:31.391434+00	5	COT-2026-0004	1	41008.10	2026-09-24	1335.0000	0.00	30	2026-11-09	2026-10-25	4	10	8	10
2026-09-25 20:10:25.947738+00	2026-09-25 20:10:25.947749+00	6	COT-2026-0005	1	41008.10	2026-09-24	90.9000	10.00	30	2026-11-09	2026-10-25	4	10	8	11
2026-09-25 20:34:33.512698+00	2026-09-25 20:34:33.512709+00	7	COT-2026-0006	1	41008.10	2026-09-24	200.0000	0.00	30	2026-11-09	2026-10-25	4	10	8	12
2026-09-25 20:45:51.986353+00	2026-09-25 20:45:51.986366+00	8	COT-2026-0007	1	41008.10	2026-09-24	366.5000	0.00	30	2026-11-09	2026-10-25	4	10	8	13
2026-09-29 12:42:20.521278+00	2026-09-29 12:42:20.52129+00	9	COT-2026-0008	1	41008.10	2026-09-24	232.9750	0.00	30	2026-11-11	2026-10-29	4	10	11	5
2026-09-29 12:43:59.318625+00	2026-09-29 12:43:59.318637+00	10	COT-2026-0008	2	41008.10	2026-09-24	232.9750	0.00	30	2026-11-11	2026-10-29	4	10	11	5
\.


--
-- Data for Name: empleado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empleado (activo, id_empleado, rut, nombre, cargo, id_usuario) FROM stdin;
t	1	15432876-9	Juan Soto	Bobinador	13
t	2	16789234-5	Pedro Rojas	Armador	\N
t	3	17234568-9	Maria Diaz	Tecnica de ensayos	16
t	4	20221980-2	Bobinador 2	Bobinador	\N
\.


--
-- Data for Name: orden_compra; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_compra (creado_en, modificado_en, id_orden_compra, numero, total_uf, anticipo_pct, id_cliente, id_cotizacion, id_estado) FROM stdin;
2026-09-25 02:13:36.660976+00	2026-09-25 07:41:37.910194+00	1	OC-2026-0001	118.5000	50.00	4	2	13
2026-09-25 18:06:44.134958+00	2026-09-25 18:06:44.13497+00	4	OC-2026-0004	1335.0000	\N	4	5	14
2026-09-25 07:58:30.957152+00	2026-09-25 07:58:30.957166+00	2	OC-2026-0002	300.0000	\N	4	3	14
2026-09-25 08:20:58.213134+00	2026-09-25 08:20:58.213146+00	3	OC-2026-0003	1185.0000	\N	4	4	14
2026-09-25 20:11:16.188701+00	2026-09-25 20:11:16.188711+00	6	OC-2026-0006	90.9000	\N	4	6	14
2026-09-25 20:07:35.049125+00	2026-09-25 20:07:35.049139+00	5	OC-2026-0005	412.6000	\N	4	1	14
2026-09-25 20:36:04.47054+00	2026-09-25 20:36:04.470577+00	7	OC-2026-0007	200.0000	\N	4	7	14
2026-09-25 20:47:36.353907+00	2026-09-25 20:47:36.353919+00	8	OC-2026-0008	366.5000	\N	4	8	14
\.


--
-- Data for Name: orden_trabajo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_trabajo (creado_en, modificado_en, id_orden_trabajo, numero, cantidad, costo_estimado_uf, costo_real_uf, avance_pct, fecha_inicio, fecha_cierre, id_estado, id_modelo, id_orden_compra) FROM stdin;
2026-09-25 20:49:08.524516+00	2026-09-25 20:49:08.52458+00	8	OT-2026-0008	2	274.0000	2.5810	100.00	2026-09-25	2026-09-25	20	11	8
2026-09-25 20:38:52.235138+00	2026-09-25 20:40:30.109666+00	7	OT-2026-0007	2	0.0000	1.6550	100.00	2026-09-25	\N	19	13	7
2026-09-25 20:16:53.0181+00	2026-09-25 20:16:53.018114+00	6	OT-2026-0006	2	330.2000	0.0000	0.00	\N	\N	17	10	5
2026-09-25 20:16:49.724751+00	2026-09-25 20:16:49.724763+00	5	OT-2026-0005	1	0.0000	0.0000	0.00	\N	\N	17	13	6
2026-09-25 20:16:41.007275+00	2026-09-25 20:16:41.007306+00	4	OT-2026-0004	10	0.0000	0.5500	20.00	2026-09-25	\N	18	9	3
2026-09-25 20:16:37.817815+00	2026-09-25 20:16:37.817828+00	3	OT-2026-0003	2	0.0000	4.5000	100.00	2026-09-25	\N	18	12	2
2026-09-25 18:12:19.032125+00	2026-09-25 18:12:19.032137+00	2	OT-2026-0002	12	1068.0000	28.6150	100.00	2026-09-25	2026-09-25	20	10	4
2026-09-25 02:13:36.67072+00	2026-09-25 20:05:37.655659+00	1	OT-2026-0001	1	94.8000	20.3044	100.00	2026-09-08	\N	18	9	1
\.


--
-- Data for Name: tarea_ot; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarea_ot (id_tarea, nombre, secuencia, horas_estimadas, estado, fecha_estimada, id_empleado, id_orden_trabajo) FROM stdin;
15	Ensayos de rutina	5	2.80	terminada	\N	2	3
14	Ensamble y llenado de aceite	4	4.00	terminada	\N	2	3
13	Bobinado de alta tension	3	4.00	terminada	\N	2	3
12	Bobinado de baja tension	2	4.00	terminada	\N	2	3
11	Corte y armado de nucleo	1	4.00	terminada	\N	2	3
26	1	1	1.00	terminada	\N	3	7
6	Corte y armado de nucleo	1	96.00	terminada	\N	3	2
7	Bobinado de baja tension	2	144.00	terminada	\N	3	2
8	Bobinado de alta tension	3	168.00	terminada	\N	3	2
9	Ensamble y llenado de aceite	4	96.00	terminada	\N	3	2
10	Ensayos de rutina	5	48.00	terminada	\N	3	2
27	Corte y armado de nucleo	1	4.00	terminada	\N	3	8
28	Bobinado de baja tension	2	4.00	terminada	\N	3	8
29	Bobinado de alta tension	3	4.00	terminada	\N	3	8
30	Ensamble y llenado de aceite	4	4.00	terminada	\N	3	8
31	Ensayos de rutina	5	4.00	terminada	\N	3	8
16	Corte y armado de nucleo	1	20.00	terminada	\N	3	4
1	Corte y armado de nucleo	1	2.00	terminada	\N	1	1
2	Bobinado de baja tension	2	2.00	terminada	\N	1	1
3	Bobinado de alta tension	3	2.00	terminada	\N	1	1
4	Ensamble y llenado de aceite	4	2.00	terminada	\N	1	1
5	Ensayos de rutina	5	2.00	terminada	\N	2	1
21	Corte y armado de nucleo	1	4.00	pendiente	\N	1	6
22	Bobinado de baja tension	2	4.00	pendiente	\N	1	6
23	Bobinado de alta tension	3	4.00	pendiente	\N	1	6
24	Ensamble y llenado de aceite	4	4.00	pendiente	\N	1	6
25	Ensayos de rutina	5	4.00	pendiente	\N	2	6
17	Bobinado de baja tension	2	20.00	pendiente	\N	1	4
18	Bobinado de alta tension	3	20.00	pendiente	\N	1	4
19	Ensamble y llenado de aceite	4	20.00	pendiente	\N	3	4
20	Ensayos de rutina	5	20.00	pendiente	\N	1	4
\.


--
-- Data for Name: consumo_material; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.consumo_material (id_consumo, cantidad, costo_unitario_uf, planificado, fecha, id_bodega, id_material, id_empleado, id_tarea) FROM stdin;
1	0.0100	0.0850	t	2026-09-25 18:15:38.439197+00	1	1	1	3
2	4.0100	0.3500	t	2026-09-25 18:15:44.806178+00	1	2	1	3
3	249.0000	0.0850	t	2026-09-25 18:38:47.264542+00	1	1	3	10
4	10.0000	0.3500	t	2026-09-25 18:39:08.347046+00	1	2	3	10
5	2.0000	0.6000	t	2026-09-25 18:39:20.954314+00	1	4	3	10
6	13.0000	0.0850	f	2026-09-25 20:41:10.517443+00	1	1	3	26
7	2.0100	0.6000	t	2026-09-25 20:51:18.64388+00	1	4	3	31
\.


--
-- Data for Name: contacto_cliente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contacto_cliente (id_contacto, nombre, cargo, email, telefono, principal, id_cliente) FROM stdin;
\.


--
-- Data for Name: protocolo_calidad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.protocolo_calidad (activo, id_protocolo, nombre, version, norma_referencia, id_modelo) FROM stdin;
t	3	Ensayos de rutina	1	IEC 60076-1	11
t	4	Ensayos de rutina	1	IEC 60076-1	12
t	1	Ensayos de rutina	1	IEC 60076-1	9
f	2	Ensayos de rutina	1	IEC 60076-1	10
t	5	Ensayos de rutina	2	IEC 60076-1	10
\.


--
-- Data for Name: control_calidad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.control_calidad (id_control, fecha_hora, estado, observacion, id_inspector, id_orden_trabajo, id_protocolo) FROM stdin;
1	2026-09-25 19:51:02.522994+00	conforme		14	2	2
2	2026-09-25 20:52:56.787896+00	conforme		14	8	3
\.


--
-- Data for Name: cotizacion_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotizacion_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, id_cotizacion, usuario_id, estado_anterior_id, estado_nuevo_id) FROM stdin;
2026-09-25 02:13:36.645843+00	2026-09-25 02:13:36.645852+00	2026-09-25 02:13:36.645861+00	Cotizacion elaborada.	1	1	7	\N	5
2026-09-25 02:13:36.650833+00	2026-09-25 02:13:36.650841+00	2026-09-25 02:13:36.650851+00	Emitida al cliente.	2	1	7	5	7
2026-09-25 02:13:36.65499+00	2026-09-25 02:13:36.654999+00	2026-09-25 02:13:36.655008+00	Aceptada por el cliente.	3	2	8	\N	8
2026-09-25 07:35:45.714202+00	2026-09-25 07:35:45.714215+00	2026-09-25 07:35:45.714227+00	Aceptada por el cliente.	4	1	8	7	8
2026-09-25 07:57:12.630925+00	2026-09-25 07:57:12.63094+00	2026-09-25 07:57:12.630953+00	Emitida al cliente.	5	3	7	5	7
2026-09-25 07:57:49.562169+00	2026-09-25 07:57:49.562182+00	2026-09-25 07:57:49.562196+00	Aceptada por el cliente.	6	3	8	7	8
2026-09-25 08:18:38.424394+00	2026-09-25 08:18:38.424403+00	2026-09-25 08:18:38.424414+00	Elaborada desde la solicitud SP-2026-0007.	7	4	7	\N	5
2026-09-25 08:19:15.688433+00	2026-09-25 08:19:15.688445+00	2026-09-25 08:19:15.688456+00	Emitida al cliente.	8	4	7	5	7
2026-09-25 08:20:13.115759+00	2026-09-25 08:20:13.115773+00	2026-09-25 08:20:13.115789+00	Aceptada por el cliente.	9	4	8	7	8
2026-09-25 18:04:31.397212+00	2026-09-25 18:04:31.397221+00	2026-09-25 18:04:31.397233+00	Elaborada desde la solicitud SP-2026-0008.	10	5	10	\N	5
2026-09-25 18:06:05.489393+00	2026-09-25 18:06:05.489408+00	2026-09-25 18:06:05.489421+00	Emitida al cliente.	11	5	10	5	7
2026-09-25 18:06:23.311435+00	2026-09-25 18:06:23.31145+00	2026-09-25 18:06:23.311464+00	Aceptada por el cliente.	12	5	8	7	8
2026-09-25 20:10:25.954201+00	2026-09-25 20:10:25.954209+00	2026-09-25 20:10:25.954219+00	Elaborada desde la solicitud SP-2026-0009.	13	6	10	\N	5
2026-09-25 20:10:46.709041+00	2026-09-25 20:10:46.709057+00	2026-09-25 20:10:46.70907+00	Emitida al cliente.	14	6	10	5	7
2026-09-25 20:11:03.802551+00	2026-09-25 20:11:03.802565+00	2026-09-25 20:11:03.802576+00	Aceptada por el cliente.	15	6	8	7	8
2026-09-25 20:34:33.518625+00	2026-09-25 20:34:33.518642+00	2026-09-25 20:34:33.518661+00	Elaborada desde la solicitud SP-2026-0010.	16	7	10	\N	5
2026-09-25 20:35:18.522738+00	2026-09-25 20:35:18.522752+00	2026-09-25 20:35:18.522765+00	Emitida al cliente.	17	7	10	5	7
2026-09-25 20:35:38.907732+00	2026-09-25 20:35:38.907747+00	2026-09-25 20:35:38.90776+00	Aceptada por el cliente.	18	7	8	7	8
2026-09-25 20:45:51.991315+00	2026-09-25 20:45:51.991324+00	2026-09-25 20:45:51.991336+00	Elaborada desde la solicitud SP-2026-0011.	19	8	10	\N	5
2026-09-25 20:46:36.476061+00	2026-09-25 20:46:36.476077+00	2026-09-25 20:46:36.47609+00	Emitida al cliente.	20	8	10	5	7
2026-09-25 20:47:07.056882+00	2026-09-25 20:47:07.056895+00	2026-09-25 20:47:07.056909+00	Aceptada por el cliente.	21	8	8	7	8
2026-09-29 12:42:20.533691+00	2026-09-29 12:42:20.533702+00	2026-09-29 12:42:20.533713+00	Elaborada desde la solicitud SP-2026-0003.	22	9	10	\N	5
2026-09-29 12:43:45.854625+00	2026-09-29 12:43:45.854638+00	2026-09-29 12:43:45.854651+00	Emitida al cliente.	23	9	10	5	7
2026-09-29 12:43:59.32261+00	2026-09-29 12:43:59.32262+00	2026-09-29 12:43:59.322632+00	Version 2 creada desde la version 1.	24	10	10	\N	5
2026-09-29 12:43:59.324563+00	2026-09-29 12:43:59.324572+00	2026-09-29 12:43:59.324584+00	Reemplazada por la version 2.	25	9	10	7	11
2026-09-29 12:44:20.275845+00	2026-09-29 12:44:20.275858+00	2026-09-29 12:44:20.275896+00	Anulada: anular prueba	26	10	10	5	11
\.


--
-- Data for Name: cotizacion_linea; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotizacion_linea (id_linea, cantidad, costo_material_uf, costo_hh_uf, margen_pct, precio_uf, id_cotizacion, id_modelo) FROM stdin;
1	2	108.4000	56.7000	25.00	206.3000	1	10
2	1	0.0000	0.0000	25.00	118.5000	2	9
3	2	0.0000	0.0000	25.00	150.0000	3	12
4	10	0.0000	0.0000	25.00	118.5000	4	9
5	12	66.0000	23.0000	25.00	111.2500	5	10
6	1	0.0000	0.0000	25.00	101.0000	6	13
7	2	0.0000	0.0000	25.00	100.0000	7	13
8	2	132.0000	5.0000	25.00	183.2500	8	11
10	1	132.0000	5.0000	25.00	171.2500	9	11
11	1	44.3800	5.0000	25.00	61.7250	9	9
12	1	132.0000	5.0000	25.00	171.2500	10	11
13	1	44.3800	5.0000	25.00	61.7250	10	9
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

-- Datos de django_admin_log omitidos (sesiones, tokens o historial del admin)


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	clientes	0001_initial	2026-09-23 09:20:37.734476+00
2	seguridad	0001_initial	2026-09-23 09:20:37.945175+00
3	contenttypes	0001_initial	2026-09-23 09:20:37.964224+00
4	admin	0001_initial	2026-09-23 09:20:38.00626+00
5	admin	0002_logentry_remove_auto_add	2026-09-23 09:20:38.013702+00
6	admin	0003_logentry_add_action_flag_choices	2026-09-23 09:20:38.02164+00
7	contenttypes	0002_remove_content_type_name	2026-09-23 09:20:38.038924+00
8	auth	0001_initial	2026-09-23 09:20:38.14307+00
9	auth	0002_alter_permission_name_max_length	2026-09-23 09:20:38.156901+00
10	auth	0003_alter_user_email_max_length	2026-09-23 09:20:38.162975+00
11	auth	0004_alter_user_username_opts	2026-09-23 09:20:38.170822+00
12	auth	0005_alter_user_last_login_null	2026-09-23 09:20:38.177252+00
13	auth	0006_require_contenttypes_0002	2026-09-23 09:20:38.180722+00
14	auth	0007_alter_validators_add_error_messages	2026-09-23 09:20:38.188104+00
15	auth	0008_alter_user_username_max_length	2026-09-23 09:20:38.194962+00
16	auth	0009_alter_user_last_name_max_length	2026-09-23 09:20:38.20204+00
17	auth	0010_alter_group_name_max_length	2026-09-23 09:20:38.218404+00
18	auth	0011_update_proxy_permissions	2026-09-23 09:20:38.230507+00
19	auth	0012_alter_user_first_name_max_length	2026-09-23 09:20:38.23755+00
20	sessions	0001_initial	2026-09-23 09:20:38.269296+00
21	inventario	0001_initial	2026-09-23 09:32:04.392083+00
22	catalogo	0001_initial	2026-09-23 09:32:04.698662+00
23	comercial	0001_initial	2026-09-23 09:36:44.925228+00
24	inventario	0002_movimientoinventario	2026-09-23 09:47:14.776816+00
25	produccion	0001_initial	2026-09-23 09:47:15.313539+00
26	calidad	0001_initial	2026-09-23 09:47:15.404756+00
27	calidad	0002_initial	2026-09-23 09:47:15.779293+00
28	inventario	0003_movimientoinventario_consumo_and_more	2026-09-23 09:47:16.023138+00
29	configuracion	0001_initial	2026-09-23 09:54:27.80391+00
30	pagos	0001_initial	2026-09-23 09:54:27.973346+00
31	seguridad	0002_bloqueo_temporal	2026-09-29 11:52:16.226395+00
32	token_blacklist	0001_initial	2026-09-29 11:52:16.405795+00
33	token_blacklist	0002_outstandingtoken_jti_hex	2026-09-29 11:52:16.428591+00
34	token_blacklist	0003_auto_20171017_2007	2026-09-29 11:52:16.473238+00
35	token_blacklist	0004_auto_20171017_2013	2026-09-29 11:52:16.510118+00
36	token_blacklist	0005_remove_outstandingtoken_jti	2026-09-29 11:52:16.536667+00
37	token_blacklist	0006_auto_20171017_2113	2026-09-29 11:52:16.558479+00
38	token_blacklist	0007_auto_20171017_2214	2026-09-29 11:52:16.644774+00
39	token_blacklist	0008_migrate_to_bigautofield	2026-09-29 11:52:16.764073+00
40	token_blacklist	0010_fix_migrate_to_bigautofield	2026-09-29 11:52:16.812257+00
41	token_blacklist	0011_linearizes_history	2026-09-29 11:52:16.816585+00
42	token_blacklist	0012_alter_outstandingtoken_user	2026-09-29 11:52:16.857873+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

-- Datos de django_session omitidos (sesiones, tokens o historial del admin)


--
-- Data for Name: documento_cobro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documento_cobro (id_documento_cobro, numero, tipo, monto_uf, valor_uf, monto_clp, estado, vence_el, creado_en, id_orden_compra) FROM stdin;
1	DC-2026-0001	anticipo	59.2500	41008.10	2429730.00	pagado	2026-10-08	2026-09-25 02:13:36.699086+00	1
2	DC-2026-0002	anticipo	150.0000	41008.10	6151215.00	pagado	2026-10-09	2026-09-25 07:58:30.984087+00	2
3	DC-2026-0003	anticipo	592.5000	41008.10	24297299.00	pagado	2026-10-09	2026-09-25 08:20:58.235229+00	3
4	DC-2026-0004	anticipo	667.5000	41008.10	27372907.00	pagado	2026-10-09	2026-09-25 18:06:44.158492+00	4
5	DC-2026-0005	anticipo	206.3000	41008.10	8459971.00	pagado	2026-10-09	2026-09-25 20:07:35.081912+00	5
6	DC-2026-0006	anticipo	45.4500	41008.10	1863818.00	pagado	2026-10-09	2026-09-25 20:11:16.210008+00	6
7	DC-2026-0007	saldo	667.5000	41008.10	27372907.00	pendiente	2026-10-09	2026-09-25 20:27:25.829697+00	4
8	DC-2026-0008	anticipo	100.0000	41008.10	4100810.00	pagado	2026-10-09	2026-09-25 20:36:04.493496+00	7
9	DC-2026-0009	anticipo	183.2500	41008.10	7514734.00	pagado	2026-10-09	2026-09-25 20:47:36.37536+00	8
10	DC-2026-0010	saldo	183.2500	41008.10	7514734.00	pagado	2026-10-09	2026-09-25 20:56:45.339809+00	8
\.


--
-- Data for Name: feriado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feriado (id_feriado, fecha, nombre, tipo, obtenido_en) FROM stdin;
1	2026-01-01	Año Nuevo	civil	2026-09-25 01:29:32.754937+00
2	2026-04-03	Viernes Santo	civil	2026-09-25 01:29:32.759902+00
3	2026-04-04	Sábado Santo	civil	2026-09-25 01:29:32.763758+00
4	2026-05-01	Día del Trabajo	civil	2026-09-25 01:29:32.767895+00
5	2026-05-21	Día de las Glorias Navales	civil	2026-09-25 01:29:32.771892+00
6	2026-06-21	Día Nacional de los Pueblos Indígenas	civil	2026-09-25 01:29:32.775733+00
7	2026-06-29	San Pedro y San Pablo	civil	2026-09-25 01:29:32.779543+00
8	2026-07-16	Virgen del Carmen	civil	2026-09-25 01:29:32.783571+00
9	2026-08-15	Asunción de la Virgen	civil	2026-09-25 01:29:32.787368+00
10	2026-09-18	Fiestas Patrias	civil	2026-09-25 01:29:32.791399+00
11	2026-09-19	Día de las Glorias del Ejército	civil	2026-09-25 01:29:32.795295+00
12	2026-10-12	Día del Descubrimiento de Dos Mundos	civil	2026-09-25 01:29:32.799575+00
13	2026-10-31	Día Nacional de las Iglesias Evangélicas y Protestantes	civil	2026-09-25 01:29:32.803885+00
14	2026-11-01	Día de Todos los Santos	civil	2026-09-25 01:29:32.807651+00
15	2026-12-08	Inmaculada Concepción	civil	2026-09-25 01:29:32.811428+00
16	2026-12-25	Navidad / Natividad del Señor	civil	2026-09-25 01:29:32.815132+00
17	2027-01-01	Año Nuevo	civil	2026-09-29 12:59:29.163005+00
18	2027-03-26	Viernes Santo	civil	2026-09-29 12:59:29.167535+00
19	2027-03-27	Sábado Santo	civil	2026-09-29 12:59:29.171392+00
20	2027-05-01	Día del Trabajo	civil	2026-09-29 12:59:29.175226+00
21	2027-05-21	Día de las Glorias Navales	civil	2026-09-29 12:59:29.179004+00
22	2027-06-21	Día Nacional de los Pueblos Indígenas	civil	2026-09-29 12:59:29.182999+00
23	2027-06-28	San Pedro y San Pablo	civil	2026-09-29 12:59:29.186712+00
24	2027-07-16	Virgen del Carmen	civil	2026-09-29 12:59:29.190947+00
25	2027-08-15	Asunción de la Virgen	civil	2026-09-29 12:59:29.19479+00
26	2027-09-18	Fiestas Patrias	civil	2026-09-29 12:59:29.198907+00
27	2027-09-19	Día de las Glorias del Ejército	civil	2026-09-29 12:59:29.202483+00
28	2027-10-11	Día del Descubrimiento de Dos Mundos	civil	2026-09-29 12:59:29.206074+00
29	2027-10-31	Día Nacional de las Iglesias Evangélicas y Protestantes	civil	2026-09-29 12:59:29.209471+00
30	2027-11-01	Día de Todos los Santos	civil	2026-09-29 12:59:29.213247+00
31	2027-12-08	Inmaculada Concepción	civil	2026-09-29 12:59:29.21697+00
32	2027-12-25	Navidad / Natividad del Señor	civil	2026-09-29 12:59:29.220756+00
\.


--
-- Data for Name: indicador_economico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.indicador_economico (id_indicador, codigo, fecha, valor, obtenido_en) FROM stdin;
1	UF	2026-09-24	41008.1000	2026-09-24 09:23:07.49849+00
3	USD	2026-09-24	959.3900	2026-09-24 09:23:07.509977+00
4	UF	2026-09-29	41049.0100	2026-09-29 12:59:28.705671+00
2	UTM	2026-09-01	71721.0000	2026-09-24 09:23:07.505241+00
5	USD	2026-09-29	969.7000	2026-09-29 12:59:28.717915+00
\.


--
-- Data for Name: log_integracion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.log_integracion (id_log, servicio, endpoint, metodo, codigo_respuesta, latencia_ms, exitoso, mensaje_error, fecha_hora) FROM stdin;
1	mindicador	https://mindicador.cl/api	GET	200	884	t		2026-09-24 09:23:07.479128+00
2	feriados	https://apis.digital.gob.cl/fl/feriados/2026	GET	0	70	f	ConnectionError: HTTPSConnectionPool(host='apis.digital.gob.cl', port=443): Max retries exceeded with url: /fl/feriados/2026 (Caused by NameResolutionError("HTTPSConnection(host='apis.digital.gob.cl', port=443): Failed to resolve 'apis.digital.gob.cl' ([Errno -2] Name or service not known)"))	2026-09-24 09:23:10.7034+00
3	feriados	https://apis.digital.gob.cl/fl/feriados/2026	GET	0	6	f	ConnectionError: HTTPSConnectionPool(host='apis.digital.gob.cl', port=443): Max retries exceeded with url: /fl/feriados/2026 (Caused by NameResolutionError("HTTPSConnection(host='apis.digital.gob.cl', port=443): Failed to resolve 'apis.digital.gob.cl' ([Errno -2] Name or service not known)"))	2026-09-24 09:23:11.714906+00
4	feriados	https://apis.digital.gob.cl/fl/feriados/2026	GET	0	7	f	ConnectionError: HTTPSConnectionPool(host='apis.digital.gob.cl', port=443): Max retries exceeded with url: /fl/feriados/2026 (Caused by NameResolutionError("HTTPSConnection(host='apis.digital.gob.cl', port=443): Failed to resolve 'apis.digital.gob.cl' ([Errno -2] Name or service not known)"))	2026-09-24 09:23:13.727759+00
5	mindicador	https://mindicador.cl/api	GET	200	808	t		2026-09-24 09:28:53.284386+00
6	feriados	https://feriadito.cl/api/feriados/2026.json	GET	404	459	f	HTTP 404	2026-09-24 09:28:56.810314+00
7	mindicador	https://mindicador.cl/api	GET	200	1259	t		2026-09-25 01:23:24.379836+00
8	feriados	https://feriadito.cl/api/feriados.json/2026.json	GET	404	585	f	HTTP 404	2026-09-25 01:23:27.711085+00
9	feriados	https://date.nager.at/api/v3/PublicHolidays/2026/CL	GET	200	665	t		2026-09-25 01:29:32.74678+00
10	mindicador	https://mindicador.cl/api	GET	200	1338	t		2026-09-25 02:13:40.853042+00
11	feriados	https://date.nager.at/api/v3/PublicHolidays/2026/CL	GET	200	519	t		2026-09-25 02:13:44.153771+00
12	paypal	https://api-m.sandbox.paypal.com/v1/oauth2/token	POST	200	1045	t		2026-09-25 02:17:33.308607+00
13	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1537	t		2026-09-25 02:17:34.851506+00
14	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1388	t		2026-09-25 02:18:32.829866+00
15	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1317	t		2026-09-25 02:23:45.537513+00
16	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1285	t		2026-09-25 02:26:43.444963+00
17	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1461	t		2026-09-25 02:32:41.53685+00
18	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/2WF72195YD9756041/capture	POST	201	1965	t		2026-09-25 02:33:35.009455+00
19	correo	https://api.brevo.com/v3/smtp/email	POST	201	857	t		2026-09-25 07:28:11.755011+00
20	correo	https://api.brevo.com/v3/smtp/email	POST	201	675	t		2026-09-25 07:34:21.077608+00
21	correo	https://api.brevo.com/v3/smtp/email	POST	201	650	t		2026-09-25 07:38:01.740508+00
22	correo	https://api.brevo.com/v3/smtp/email	POST	201	730	t		2026-09-25 07:47:41.374242+00
23	correo	https://api.brevo.com/v3/smtp/email	POST	201	750	t		2026-09-25 07:57:13.389505+00
24	paypal	https://api-m.sandbox.paypal.com/v1/oauth2/token	POST	200	1131	t		2026-09-25 07:59:07.33202+00
25	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1325	t		2026-09-25 07:59:08.662552+00
26	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/6MP02347FF579830B/capture	POST	201	3383	t		2026-09-25 07:59:30.134563+00
27	correo	https://api.brevo.com/v3/smtp/email	POST	201	646	t		2026-09-25 07:59:30.80742+00
28	correo	https://api.brevo.com/v3/smtp/email	POST	201	741	t		2026-09-25 08:18:14.537317+00
29	correo	https://api.brevo.com/v3/smtp/email	POST	201	722	t		2026-09-25 08:19:16.428087+00
30	paypal	https://api-m.sandbox.paypal.com/v1/oauth2/token	POST	200	1131	t		2026-09-25 08:21:50.599912+00
31	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1427	t		2026-09-25 08:21:52.031846+00
32	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/2CG96871FV821860R/capture	POST	201	1939	t		2026-09-25 08:22:11.292774+00
33	correo	https://api.brevo.com/v3/smtp/email	POST	201	731	t		2026-09-25 08:22:12.047332+00
34	correo	https://api.brevo.com/v3/smtp/email	POST	201	714	t		2026-09-25 18:04:13.184525+00
35	correo	https://api.brevo.com/v3/smtp/email	POST	201	858	t		2026-09-25 18:06:06.363817+00
36	paypal	https://api-m.sandbox.paypal.com/v1/oauth2/token	POST	200	927	t		2026-09-25 18:06:57.432996+00
37	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1398	t		2026-09-25 18:06:58.836066+00
38	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/167871419F152234B/capture	POST	201	2091	t		2026-09-25 18:07:12.041546+00
39	correo	https://api.brevo.com/v3/smtp/email	POST	201	881	t		2026-09-25 18:07:12.947557+00
40	correo	https://api.brevo.com/v3/smtp/email	POST	201	706	t		2026-09-25 18:32:10.602232+00
41	paypal	https://api-m.sandbox.paypal.com/v1/oauth2/token	POST	200	1120	t		2026-09-25 20:08:04.243868+00
42	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1349	t		2026-09-25 20:08:05.601706+00
43	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/06N30997C8643492G/capture	POST	201	1763	t		2026-09-25 20:08:20.638538+00
44	correo	https://api.brevo.com/v3/smtp/email	POST	201	683	t		2026-09-25 20:08:21.366784+00
45	correo	https://api.brevo.com/v3/smtp/email	POST	201	765	t		2026-09-25 20:10:47.491328+00
46	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1365	t		2026-09-25 20:11:28.533245+00
47	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/5ME23869JX4590734/capture	POST	201	1862	t		2026-09-25 20:11:35.170064+00
48	correo	https://api.brevo.com/v3/smtp/email	POST	201	759	t		2026-09-25 20:11:35.943238+00
49	correo	https://api.brevo.com/v3/smtp/email	POST	201	755	t		2026-09-25 20:27:26.674741+00
50	correo	https://api.brevo.com/v3/smtp/email	POST	201	694	t		2026-09-25 20:33:20.425248+00
51	correo	https://api.brevo.com/v3/smtp/email	POST	201	758	t		2026-09-25 20:35:19.298754+00
52	paypal	https://api-m.sandbox.paypal.com/v1/oauth2/token	POST	200	994	t		2026-09-25 20:36:20.741585+00
53	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1344	t		2026-09-25 20:36:22.096247+00
54	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/26V21497HC984222R/capture	POST	201	2044	t		2026-09-25 20:36:36.218501+00
55	correo	https://api.brevo.com/v3/smtp/email	POST	201	672	t		2026-09-25 20:36:36.914423+00
56	correo	https://api.brevo.com/v3/smtp/email	POST	201	827	t		2026-09-25 20:44:43.82925+00
57	correo	https://api.brevo.com/v3/smtp/email	POST	201	740	t		2026-09-25 20:46:37.225136+00
58	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1309	t		2026-09-25 20:47:59.341594+00
59	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/1Y261100CC6822530/capture	POST	201	1952	t		2026-09-25 20:48:07.475115+00
60	correo	https://api.brevo.com/v3/smtp/email	POST	201	684	t		2026-09-25 20:48:08.175566+00
61	correo	https://api.brevo.com/v3/smtp/email	POST	201	739	t		2026-09-25 20:56:46.111834+00
62	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders	POST	200	1172	t		2026-09-25 20:57:17.492687+00
63	paypal	https://api-m.sandbox.paypal.com/v2/checkout/orders/0G245954Y94744203/capture	POST	201	1756	t		2026-09-25 20:57:23.651982+00
64	correo	https://api.brevo.com/v3/smtp/email	POST	201	662	t		2026-09-25 20:57:24.331826+00
65	correo	https://api.brevo.com/v3/smtp/email	POST	201	789	t		2026-09-29 12:02:52.836212+00
66	correo	https://api.brevo.com/v3/smtp/email	POST	201	688	t		2026-09-29 12:43:46.606299+00
67	mindicador	https://mindicador.cl/api	GET	200	1404	t		2026-09-29 12:59:28.69038+00
68	feriados	https://date.nager.at/api/v3/PublicHolidays/2026/CL	GET	200	224	t		2026-09-29 12:59:28.945757+00
69	feriados	https://date.nager.at/api/v3/PublicHolidays/2027/CL	GET	200	195	t		2026-09-29 12:59:29.157982+00
\.


--
-- Data for Name: parametro_tecnico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.parametro_tecnico (id_parametro, codigo, nombre, unidad, tipo_dato, obligatorio) FROM stdin;
11	potencia_kva	Potencia nominal	kVA	lista	t
12	tension_prim	Tension primaria	kV	numerico	t
13	tension_sec	Tension secundaria	V	numerico	t
14	grupo_conexion	Grupo de conexion		lista	t
15	refrigeracion	Refrigeracion		lista	t
\.


--
-- Data for Name: modelo_parametro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modelo_parametro (id, valor_defecto, obligatorio, id_modelo, id_parametro) FROM stdin;
41	50	t	9	11
42	15	t	9	12
43	400	t	9	13
44	Dyn11	t	9	14
45	ONAN	t	9	15
46	100	t	10	11
47	15	t	10	12
48	400	t	10	13
49	Dyn11	t	10	14
50	ONAN	t	10	15
51	250	t	11	11
52	23	t	11	12
53	400	t	11	13
54	Dyn11	t	11	14
55	ONAN	t	11	15
61	Dyn11	t	13	14
62	500	t	13	11
63	ONAF	t	13	15
64	100000	t	13	12
65	95000	t	13	13
59	Yzn11	t	12	14
56	50	t	12	11
60	ONAF	t	12	15
57	15	t	12	12
58	400	t	12	13
66		t	14	14
67		t	14	11
68		t	14	15
69		t	14	12
\.


--
-- Data for Name: proveedor; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.proveedor (activo, id_proveedor, rut, razon_social, email, telefono) FROM stdin;
t	1	76086428-5	Cobres del Sur SpA	ventas@cobresdelsur.cl	
t	2	77111222-6	Aceros y Aislantes Andinos Ltda	contacto@andinos.cl	
\.


--
-- Data for Name: movimiento_inventario; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.movimiento_inventario (id_movimiento, tipo, cantidad, costo_unitario_uf, fecha_hora, observacion, id_bodega, id_consumo, id_material, id_proveedor, id_usuario) FROM stdin;
1	recepcion	2500.0000	0.0850	2026-09-25 18:00:04.144718+00	Stock inicial de demostracion	1	\N	1	\N	1
2	recepcion	900.0000	0.3500	2026-09-25 18:00:04.151618+00	Stock inicial de demostracion	1	\N	2	\N	1
3	recepcion	1800.0000	0.0800	2026-09-25 18:00:04.156713+00	Stock inicial de demostracion	1	\N	3	\N	1
4	recepcion	80.0000	0.6000	2026-09-25 18:00:04.161467+00	Stock inicial de demostracion	1	\N	4	\N	1
5	recepcion	60.0000	1.1000	2026-09-25 18:00:04.165799+00	Stock inicial de demostracion	1	\N	5	\N	1
6	recepcion	10.0000	12.0000	2026-09-25 18:00:04.170694+00	Stock inicial de demostracion	1	\N	6	\N	1
7	consumo	-0.0100	0.0850	2026-09-25 18:15:38.443006+00	OT-2026-0001 / Bobinado de alta tension	1	1	1	\N	13
8	consumo	-4.0100	0.3500	2026-09-25 18:15:44.808003+00	OT-2026-0001 / Bobinado de alta tension	1	2	2	\N	13
9	consumo	-249.0000	0.0850	2026-09-25 18:38:47.266522+00	OT-2026-0002 / Ensayos de rutina	1	3	1	\N	1
10	consumo	-10.0000	0.3500	2026-09-25 18:39:08.34853+00	OT-2026-0002 / Ensayos de rutina	1	4	2	\N	1
11	consumo	-2.0000	0.6000	2026-09-25 18:39:20.955771+00	OT-2026-0002 / Ensayos de rutina	1	5	4	\N	1
12	consumo	-13.0000	0.0850	2026-09-25 20:41:10.540947+00	OT-2026-0007 / 1	1	6	1	\N	12
13	consumo	-2.0100	0.6000	2026-09-25 20:51:18.645869+00	OT-2026-0008 / Ensayos de rutina	1	7	4	\N	16
14	recepcion	14.0100	12.0000	2026-09-26 02:30:55.14418+00	Documento 1	1	\N	6	1	15
15	recepcion	0.0900	12.0000	2026-09-26 02:31:07.490867+00	Recepcion de compra	1	\N	6	\N	15
\.


--
-- Data for Name: punto_control; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.punto_control (id_punto, nombre, tipo_ensayo, unidad, valor_esperado, tolerancia_inf, tolerancia_sup, obligatorio, secuencia, id_protocolo) FROM stdin;
9	Resistencia de aislamiento AT-BT y a tierra	Rutina	MOhm	\N	1000.0000	\N	t	1	2
10	Relacion de transformacion (desviacion)	Rutina	%	0.0000	-0.5000	0.5000	t	2	2
11	Resistencia de devanados (desbalance entre fases)	Rutina	%	0.0000	\N	2.0000	t	3	2
12	Tension aplicada durante 60 s	Rutina	kV	34.0000	34.0000	\N	t	4	2
13	Corriente de vacio	Rutina	%	\N	\N	2.5000	t	5	2
14	Perdidas en vacio	Rutina	W	\N	\N	320.0000	t	6	2
15	Rigidez dielectrica del aceite	Rutina	kV	\N	30.0000	\N	t	7	2
16	Nivel de ruido	Rutina	dB	\N	\N	60.0000	f	8	2
17	Resistencia de aislamiento AT-BT y a tierra	Rutina	MOhm	\N	1000.0000	\N	t	1	3
18	Relacion de transformacion (desviacion)	Rutina	%	0.0000	-0.5000	0.5000	t	2	3
19	Resistencia de devanados (desbalance entre fases)	Rutina	%	0.0000	\N	2.0000	t	3	3
20	Tension aplicada durante 60 s	Rutina	kV	34.0000	34.0000	\N	t	4	3
21	Corriente de vacio	Rutina	%	\N	\N	2.5000	t	5	3
22	Perdidas en vacio	Rutina	W	\N	\N	650.0000	t	6	3
23	Rigidez dielectrica del aceite	Rutina	kV	\N	30.0000	\N	t	7	3
24	Nivel de ruido	Rutina	dB	\N	\N	60.0000	f	8	3
25	Resistencia de aislamiento AT-BT y a tierra	Rutina	MOhm	\N	1000.0000	\N	t	1	4
26	Relacion de transformacion (desviacion)	Rutina	%	0.0000	-0.5000	0.5000	t	2	4
27	Resistencia de devanados (desbalance entre fases)	Rutina	%	0.0000	\N	2.0000	t	3	4
28	Tension aplicada durante 60 s	Rutina	kV	34.0000	34.0000	\N	t	4	4
29	Corriente de vacio	Rutina	%	\N	\N	2.5000	t	5	4
30	Perdidas en vacio	Rutina	W	\N	\N	110.0000	t	6	4
31	Rigidez dielectrica del aceite	Rutina	kV	\N	30.0000	\N	t	7	4
32	Nivel de ruido	Rutina	dB	\N	\N	60.0000	f	8	4
33	Resistencia de aislamiento AT-BT y a tierra	Rutina	MOhm	\N	1000.0000	\N	f	1	1
34	Relacion de transformacion (desviacion)	Rutina	%	0.0000	-0.5000	0.5000	f	2	1
35	Resistencia de devanados (desbalance entre fases)	Rutina	%	0.0000	\N	2.0000	f	3	1
36	Tension aplicada durante 60 s	Rutina	kV	34.0000	34.0000	\N	f	4	1
37	Corriente de vacio	Rutina	%	\N	\N	2.5000	f	5	1
38	Perdidas en vacio	Rutina	W	\N	\N	190.0000	f	6	1
39	Rigidez dielectrica del aceite	Rutina	kV	\N	30.0000	\N	f	7	1
40	Nivel de ruido	Rutina	dB	\N	\N	60.0000	f	8	1
41	Resistencia de aislamiento AT-BT y a tierra	Rutina	MOhm	\N	1000.0000	\N	t	1	5
42	Relacion de transformacion (desviacion)	Rutina	%	0.0000	-0.5000	0.5000	t	2	5
43	Resistencia de devanados (desbalance entre fases)	Rutina	%	0.0000	\N	2.0000	t	3	5
44	Tension aplicada durante 60 s	Rutina	kV	34.0000	34.0000	\N	t	4	5
45	Corriente de vacio	Rutina	%	\N	\N	2.5000	t	5	5
46	Perdidas en vacio	Rutina	W	\N	\N	320.0000	t	6	5
47	Rigidez dielectrica del aceite	Rutina	kV	\N	30.0000	\N	t	7	5
48	Nivel de ruido	Rutina	dB	\N	\N	60.0000	f	8	5
\.


--
-- Data for Name: resultado_control; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resultado_control (id_resultado, valor_medido, conforme, observacion, registrado_en, id_control, id_punto) FROM stdin;
1	0.0000	f		2026-09-25 19:51:15.801743+00	1	9
2	10002.0000	t		2026-09-25 19:52:00.383194+00	1	9
3	1.0000	f		2026-09-25 19:52:11.020674+00	1	10
4	1.0000	t		2026-09-25 19:52:31.33373+00	1	11
5	35.0000	t		2026-09-25 19:52:39.293775+00	1	12
6	1.0000	t		2026-09-25 19:52:49.044249+00	1	13
7	310.0000	t		2026-09-25 19:52:56.302132+00	1	14
8	35.0000	t		2026-09-25 19:53:04.037164+00	1	15
9	55.0000	t		2026-09-25 19:53:07.666814+00	1	16
10	0.0000	t		2026-09-25 19:53:33.277014+00	1	10
11	0.0000	t		2026-09-25 19:55:16.194325+00	1	16
12	0.0000	f		2026-09-25 20:01:39.713598+00	1	9
13	20000.0000	t		2026-09-25 20:01:57.574414+00	1	9
14	55.0000	t		2026-09-25 20:02:06.397488+00	1	16
15	55.0000	t		2026-09-25 20:02:09.405505+00	1	16
16	100000.0000	t		2026-09-25 20:53:28.650462+00	2	17
17	0.0000	t		2026-09-25 20:53:34.289871+00	2	18
18	1.0000	t		2026-09-25 20:53:37.463851+00	2	19
19	36.0000	t		2026-09-25 20:53:44.018461+00	2	20
20	1.0000	t		2026-09-25 20:53:53.271732+00	2	21
21	640.0000	t		2026-09-25 20:53:58.745825+00	2	22
22	23.0000	f		2026-09-25 20:54:05.203169+00	2	23
23	23.0000	t		2026-09-25 20:54:14.76091+00	2	24
24	33.0000	t		2026-09-25 20:54:39.402649+00	2	23
\.


--
-- Data for Name: no_conformidad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.no_conformidad (id_no_conformidad, descripcion, severidad, accion_correctiva, estado, abierta_en, cerrada_en, id_responsable, id_usuario_cierre, id_resultado) FROM stdin;
1	Resistencia de aislamiento AT-BT y a tierra: 0 MOhm fuera de rango (min 1E+3).	mayor	asdasdasdasdasdasd	cerrada	2026-09-25 19:51:15.804031+00	2026-09-25 19:51:41.118504+00	14	14	1
2	Relacion de transformacion (desviacion): 1 % fuera de rango (min -0.5, max 0.5).	mayor	4553453453453	cerrada	2026-09-25 19:52:11.021617+00	2026-09-25 19:53:16.582719+00	14	14	3
3	Resistencia de aislamiento AT-BT y a tierra: 0 MOhm fuera de rango (min 1E+3).	mayor	adfasdasdas	cerrada	2026-09-25 20:01:39.718516+00	2026-09-25 20:01:49.248825+00	14	14	12
4	Rigidez dielectrica del aceite: 23 kV fuera de rango (min 3E+1).	mayor	error de seleccion	cerrada	2026-09-25 20:54:05.204222+00	2026-09-25 20:54:30.58041+00	14	14	22
\.


--
-- Data for Name: orden_compra_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_compra_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, estado_anterior_id, estado_nuevo_id, id_orden_compra, usuario_id) FROM stdin;
2026-09-25 07:58:30.96967+00	2026-09-25 07:58:30.969682+00	2026-09-25 07:58:30.969694+00	Generada desde la cotizacion SP-2026-0006.	1	\N	12	2	7
2026-09-25 08:20:58.223208+00	2026-09-25 08:20:58.223221+00	2026-09-25 08:20:58.223234+00	Generada desde la cotizacion COT-2026-0003.	2	\N	12	3	7
2026-09-25 08:22:43.766955+00	2026-09-25 08:22:43.766967+00	2026-09-25 08:22:43.766978+00	Orden confirmada.	3	12	13	1	7
2026-09-25 08:22:46.662454+00	2026-09-25 08:22:46.662467+00	2026-09-25 08:22:46.662478+00	Orden confirmada.	4	12	13	2	7
2026-09-25 08:22:49.03986+00	2026-09-25 08:22:49.039873+00	2026-09-25 08:22:49.039884+00	Orden confirmada.	5	12	13	3	7
2026-09-25 18:06:44.146347+00	2026-09-25 18:06:44.146358+00	2026-09-25 18:06:44.14637+00	Generada desde la cotizacion COT-2026-0004.	6	\N	12	4	10
2026-09-25 18:08:50.323912+00	2026-09-25 18:08:50.323926+00	2026-09-25 18:08:50.32394+00	Orden confirmada.	7	12	13	4	10
2026-09-25 18:12:19.051292+00	2026-09-25 18:12:19.051331+00	2026-09-25 18:12:19.051349+00	1 orden(es) de trabajo generada(s).	8	13	14	4	12
2026-09-25 20:07:35.063639+00	2026-09-25 20:07:35.063668+00	2026-09-25 20:07:35.063681+00	Generada desde la cotizacion COT-2026-0001.	9	\N	12	5	10
2026-09-25 20:11:16.197602+00	2026-09-25 20:11:16.197614+00	2026-09-25 20:11:16.197625+00	Generada desde la cotizacion COT-2026-0005.	10	\N	12	6	10
2026-09-25 20:16:37.831257+00	2026-09-25 20:16:37.831265+00	2026-09-25 20:16:37.831277+00	1 orden(es) de trabajo generada(s).	11	13	14	2	1
2026-09-25 20:16:41.018002+00	2026-09-25 20:16:41.018015+00	2026-09-25 20:16:41.018027+00	1 orden(es) de trabajo generada(s).	12	13	14	3	1
2026-09-25 20:16:44.680844+00	2026-09-25 20:16:44.680856+00	2026-09-25 20:16:44.680866+00	Orden confirmada.	13	12	13	5	1
2026-09-25 20:16:47.082021+00	2026-09-25 20:16:47.082034+00	2026-09-25 20:16:47.082046+00	Orden confirmada.	14	12	13	6	1
2026-09-25 20:16:49.730938+00	2026-09-25 20:16:49.730948+00	2026-09-25 20:16:49.730959+00	1 orden(es) de trabajo generada(s).	15	13	14	6	1
2026-09-25 20:16:53.027005+00	2026-09-25 20:16:53.027014+00	2026-09-25 20:16:53.027025+00	1 orden(es) de trabajo generada(s).	16	13	14	5	1
2026-09-25 20:36:04.480407+00	2026-09-25 20:36:04.480419+00	2026-09-25 20:36:04.48043+00	Generada desde la cotizacion COT-2026-0006.	17	\N	12	7	10
2026-09-25 20:37:13.717713+00	2026-09-25 20:37:13.717726+00	2026-09-25 20:37:13.717739+00	Orden confirmada.	18	12	13	7	10
2026-09-25 20:38:52.242267+00	2026-09-25 20:38:52.242278+00	2026-09-25 20:38:52.242289+00	1 orden(es) de trabajo generada(s).	19	13	14	7	12
2026-09-25 20:47:36.36321+00	2026-09-25 20:47:36.363222+00	2026-09-25 20:47:36.363234+00	Generada desde la cotizacion COT-2026-0007.	20	\N	12	8	10
2026-09-25 20:48:36.767761+00	2026-09-25 20:48:36.767775+00	2026-09-25 20:48:36.767788+00	Orden confirmada.	21	12	13	8	10
2026-09-25 20:49:08.535424+00	2026-09-25 20:49:08.535436+00	2026-09-25 20:49:08.535448+00	1 orden(es) de trabajo generada(s).	22	13	14	8	12
\.


--
-- Data for Name: orden_compra_linea; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_compra_linea (id_linea_oc, cantidad, precio_uf, id_cotizacion_linea, id_orden_compra) FROM stdin;
1	1	118.5000	2	1
2	2	150.0000	3	2
3	10	118.5000	4	3
4	12	111.2500	5	4
5	2	206.3000	1	5
6	1	101.0000	6	6
7	2	100.0000	7	7
8	2	183.2500	8	8
\.


--
-- Data for Name: orden_trabajo_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_trabajo_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, estado_anterior_id, estado_nuevo_id, id_orden_trabajo, usuario_id) FROM stdin;
2026-09-25 02:13:36.678811+00	2026-09-25 02:13:36.67882+00	2026-09-25 02:13:36.67883+00	Generada desde la orden de compra OC-2026-0001.	1	\N	17	1	7
2026-09-25 02:13:36.684556+00	2026-09-25 02:13:36.684565+00	2026-09-25 02:13:36.684576+00	Inicio de fabricacion en taller.	2	17	18	1	7
2026-09-25 18:12:19.045408+00	2026-09-25 18:12:19.045419+00	2026-09-25 18:12:19.04543+00	Generada desde la orden de compra OC-2026-0004.	3	\N	17	2	12
2026-09-25 18:14:30.575328+00	2026-09-25 18:14:30.575338+00	2026-09-25 18:14:30.575348+00	Inicio de fabricacion en taller.	4	17	18	2	12
2026-09-25 18:53:12.914506+00	2026-09-25 18:53:12.914518+00	2026-09-25 18:53:12.914529+00	Fabricacion terminada; pasa a control de calidad.	5	18	19	2	1
2026-09-25 20:13:18.739213+00	2026-09-25 20:13:18.739228+00	2026-09-25 20:13:18.739241+00	Orden cerrada. Desviacion justificada: asdasdasdasd	6	19	20	2	1
2026-09-25 20:16:37.828524+00	2026-09-25 20:16:37.828535+00	2026-09-25 20:16:37.828545+00	Generada desde la orden de compra OC-2026-0002.	7	\N	17	3	1
2026-09-25 20:16:41.014886+00	2026-09-25 20:16:41.014898+00	2026-09-25 20:16:41.014909+00	Generada desde la orden de compra OC-2026-0003.	8	\N	17	4	1
2026-09-25 20:16:49.728009+00	2026-09-25 20:16:49.728023+00	2026-09-25 20:16:49.728039+00	Generada desde la orden de compra OC-2026-0006.	9	\N	17	5	1
2026-09-25 20:16:53.024305+00	2026-09-25 20:16:53.024315+00	2026-09-25 20:16:53.024324+00	Generada desde la orden de compra OC-2026-0005.	10	\N	17	6	1
2026-09-25 20:29:49.139208+00	2026-09-25 20:29:49.139226+00	2026-09-25 20:29:49.13924+00	Inicio de fabricacion en taller.	11	17	18	3	12
2026-09-25 20:38:52.239212+00	2026-09-25 20:38:52.239226+00	2026-09-25 20:38:52.239238+00	Generada desde la orden de compra OC-2026-0007.	12	\N	17	7	12
2026-09-25 20:40:37.295333+00	2026-09-25 20:40:37.29535+00	2026-09-25 20:40:37.295362+00	Inicio de fabricacion en taller.	13	17	18	7	12
2026-09-25 20:41:36.237742+00	2026-09-25 20:41:36.237755+00	2026-09-25 20:41:36.237767+00	Fabricacion terminada; pasa a control de calidad.	14	18	19	7	12
2026-09-25 20:49:08.532332+00	2026-09-25 20:49:08.532343+00	2026-09-25 20:49:08.532353+00	Generada desde la orden de compra OC-2026-0008.	15	\N	17	8	12
2026-09-25 20:50:12.538909+00	2026-09-25 20:50:12.538921+00	2026-09-25 20:50:12.538933+00	Inicio de fabricacion en taller.	16	17	18	8	12
2026-09-25 20:52:09.788898+00	2026-09-25 20:52:09.78891+00	2026-09-25 20:52:09.788921+00	Fabricacion terminada; pasa a control de calidad.	17	18	19	8	12
2026-09-25 20:56:45.329741+00	2026-09-25 20:56:45.329752+00	2026-09-25 20:56:45.329764+00	Orden cerrada. Desviacion justificada: prueba	18	19	20	8	12
2026-09-26 02:11:28.831507+00	2026-09-26 02:11:28.831522+00	2026-09-26 02:11:28.831536+00	Inicio de fabricacion en taller.	19	17	18	4	12
\.


--
-- Data for Name: parametro_sistema; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.parametro_sistema (id_parametro_sistema, clave, valor, tipo_dato, ambito, descripcion, modificado_en, id_usuario) FROM stdin;
5	comercial.vigencia_cotizacion_dias	30	numerico	comercial	Dias de vigencia de una cotizacion (RN-04).	2026-09-23 09:54:33.70043+00	1
6	comercial.umbral_descuento_pct	10	numerico	comercial	Descuento sobre el cual se exige aprobacion interna (RN-05).	2026-09-23 09:54:33.704477+00	1
7	comercial.anticipo_pct	50	numerico	comercial	Porcentaje de anticipo por defecto (RN-15).	2026-09-23 09:54:33.708767+00	1
8	comercial.margen_defecto_pct	25	numerico	comercial	Margen aplicado por defecto al costo estimado.	2026-09-23 09:54:33.713055+00	1
9	produccion.max_horas_diarias	12	numerico	produccion	Maximo de horas hombre registrables por empleado y dia.	2026-09-23 09:54:33.717157+00	1
10	produccion.umbral_desviacion_costo_pct	15	numerico	produccion	Desviacion sobre la cual se exige justificacion al cerrar (RN-11).	2026-09-23 09:54:33.721544+00	1
11	sistema.intentos_fallidos_max	5	numerico	sistema	Intentos fallidos antes de bloquear la cuenta (RF-SEG-04).	2026-09-23 09:54:33.726115+00	1
12	sistema.minutos_inactividad	30	numerico	sistema	Minutos de inactividad antes de cerrar sesion (RF-SEG-07).	2026-09-23 09:54:33.730762+00	1
1	web.modo_mantencion	false	booleano	canal_web	Suspende la operacion de la aplicacion web (RF-ADM-01).	2026-09-25 08:00:45.961976+00	7
2	web.mensaje_mantencion	Sitio en mantencion. Volvemos pronto.	texto	canal_web	Aviso mostrado durante la mantencion.	2026-09-25 08:00:47.058056+00	7
4	web.autorregistro_habilitado	true	booleano	canal_web	Permite que nuevos clientes se registren solos (RF-CLI-06).	2026-09-25 20:59:39.382595+00	9
3	web.pago_en_linea_habilitado	true	booleano	canal_web	Habilita el pago en linea en la web (RF-ADM-02).	2026-09-25 20:59:42.045515+00	9
13	sistema.minutos_bloqueo	15	numerico	sistema	Minutos de bloqueo temporal tras superar los intentos fallidos (RF-SEG-04).	2026-09-29 12:59:24.216104+00	1
14	produccion.costo_indirecto_pct	10	numerico	produccion	Recargo por costos indirectos sobre materiales y horas hombre (RN-11).	2026-09-29 12:59:24.230047+00	1
\.


--
-- Data for Name: permiso; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permiso (id_permiso, codigo, modulo, operacion) FROM stdin;
1	usuario.leer	usuario	leer
2	usuario.crear	usuario	crear
3	usuario.actualizar	usuario	actualizar
4	usuario.anular	usuario	anular
5	rol.leer	rol	leer
6	rol.crear	rol	crear
7	rol.actualizar	rol	actualizar
8	rol.anular	rol	anular
9	auditoria.leer	auditoria	leer
10	auditoria.crear	auditoria	crear
11	auditoria.actualizar	auditoria	actualizar
12	auditoria.anular	auditoria	anular
13	parametro.leer	parametro	leer
14	parametro.crear	parametro	crear
15	parametro.actualizar	parametro	actualizar
16	parametro.anular	parametro	anular
17	cliente.leer	cliente	leer
18	cliente.crear	cliente	crear
19	cliente.actualizar	cliente	actualizar
20	cliente.anular	cliente	anular
21	catalogo.leer	catalogo	leer
22	catalogo.crear	catalogo	crear
23	catalogo.actualizar	catalogo	actualizar
24	catalogo.anular	catalogo	anular
25	bom.leer	bom	leer
26	bom.crear	bom	crear
27	bom.actualizar	bom	actualizar
28	bom.anular	bom	anular
29	precio.leer	precio	leer
30	precio.crear	precio	crear
31	precio.actualizar	precio	actualizar
32	precio.anular	precio	anular
33	solicitud.leer	solicitud	leer
34	solicitud.crear	solicitud	crear
35	solicitud.actualizar	solicitud	actualizar
36	solicitud.anular	solicitud	anular
37	cotizacion.leer	cotizacion	leer
38	cotizacion.crear	cotizacion	crear
39	cotizacion.actualizar	cotizacion	actualizar
40	cotizacion.anular	cotizacion	anular
41	cotizacion.aprobar	cotizacion	actualizar
42	orden_compra.leer	orden_compra	leer
43	orden_compra.crear	orden_compra	crear
44	orden_compra.actualizar	orden_compra	actualizar
45	orden_compra.anular	orden_compra	anular
46	orden_trabajo.leer	orden_trabajo	leer
47	orden_trabajo.crear	orden_trabajo	crear
48	orden_trabajo.actualizar	orden_trabajo	actualizar
49	orden_trabajo.anular	orden_trabajo	anular
50	taller.leer	taller	leer
51	taller.crear	taller	crear
52	taller.actualizar	taller	actualizar
53	taller.anular	taller	anular
54	protocolo_calidad.leer	protocolo_calidad	leer
55	protocolo_calidad.crear	protocolo_calidad	crear
56	protocolo_calidad.actualizar	protocolo_calidad	actualizar
57	protocolo_calidad.anular	protocolo_calidad	anular
58	ensayo.leer	ensayo	leer
59	ensayo.crear	ensayo	crear
60	ensayo.actualizar	ensayo	actualizar
61	ensayo.anular	ensayo	anular
62	no_conformidad.leer	no_conformidad	leer
63	no_conformidad.crear	no_conformidad	crear
64	no_conformidad.actualizar	no_conformidad	actualizar
65	no_conformidad.anular	no_conformidad	anular
66	material.leer	material	leer
67	material.crear	material	crear
68	material.actualizar	material	actualizar
69	material.anular	material	anular
70	bodega.leer	bodega	leer
71	bodega.crear	bodega	crear
72	bodega.actualizar	bodega	actualizar
73	bodega.anular	bodega	anular
74	kardex.leer	kardex	leer
75	kardex.crear	kardex	crear
76	kardex.actualizar	kardex	actualizar
77	kardex.anular	kardex	anular
78	empleado.leer	empleado	leer
79	empleado.crear	empleado	crear
80	empleado.actualizar	empleado	actualizar
81	empleado.anular	empleado	anular
82	canal_web.leer	canal_web	leer
83	canal_web.crear	canal_web	crear
84	canal_web.actualizar	canal_web	actualizar
85	canal_web.anular	canal_web	anular
86	cuenta_web.leer	cuenta_web	leer
87	cuenta_web.crear	cuenta_web	crear
88	cuenta_web.actualizar	cuenta_web	actualizar
89	cuenta_web.anular	cuenta_web	anular
90	reporte.leer	reporte	leer
91	reporte.crear	reporte	crear
92	reporte.actualizar	reporte	actualizar
93	reporte.anular	reporte	anular
\.


--
-- Data for Name: precio_base_modelo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.precio_base_modelo (vigente_desde, vigente_hasta, id_precio, monto_uf, id_modelo, id_usuario) FROM stdin;
2026-01-01	\N	7	118.5000	9	7
2026-01-01	\N	8	185.0000	10	7
2026-01-01	\N	9	342.8000	11	7
2026-09-25	\N	10	100.0000	13	9
2026-09-25	\N	11	220.0000	12	9
2026-09-29	\N	12	799.0000	14	9
\.


--
-- Data for Name: precio_material; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.precio_material (vigente_desde, vigente_hasta, id_precio_material, costo_uf, id_material, id_proveedor) FROM stdin;
2026-01-01	\N	1	0.0850	1	\N
2026-01-01	\N	2	0.3500	2	\N
2026-01-01	\N	3	0.0800	3	\N
2026-01-01	\N	4	0.6000	4	\N
2026-01-01	\N	5	1.1000	5	\N
2026-01-01	\N	6	12.0000	6	\N
\.


--
-- Data for Name: registro_hora_hombre; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.registro_hora_hombre (id_registro, fecha, horas, valor_hora_uf, anulado, id_empleado, id_usuario_registro, id_tarea) FROM stdin;
1	2026-09-24	8.00	0.5000	f	1	1	1
2	2026-09-23	8.00	0.5000	f	1	1	2
3	2026-09-22	8.00	0.5000	f	1	1	2
4	2026-09-25	1.00	0.5000	f	1	12	3
5	2026-09-25	1.00	0.5000	f	1	12	3
6	2026-09-25	6.00	0.5000	f	1	12	3
7	2026-09-25	3.50	0.5000	f	1	12	3
8	2026-09-25	0.50	0.5000	f	1	13	4
9	2026-09-25	0.50	0.5500	f	3	1	6
10	2026-09-25	0.50	0.5500	f	3	1	7
11	2026-09-25	0.50	0.5500	f	3	1	8
12	2026-09-25	0.50	0.5500	f	3	1	9
13	2026-09-25	0.50	0.5500	f	3	1	10
14	2026-09-25	0.50	0.5500	f	3	16	6
15	2026-09-25	0.50	0.5500	f	3	16	7
16	2026-09-25	0.50	0.5500	f	3	16	8
17	2026-09-25	0.50	0.5500	f	3	16	9
18	2026-09-25	0.50	0.5500	f	3	16	10
19	2026-09-24	2.00	0.4500	f	2	1	5
20	2026-09-25	4.00	0.4500	f	2	12	11
21	2026-09-25	4.00	0.4500	f	2	12	12
22	2026-09-25	1.00	0.4500	f	2	12	13
23	2026-09-25	0.50	0.4500	f	2	12	14
24	2026-09-25	0.50	0.4500	f	2	12	15
25	2026-09-25	1.00	0.5500	f	3	12	26
26	2026-09-25	0.50	0.5500	f	3	16	27
27	2026-09-25	0.50	0.5500	f	3	16	28
28	2026-09-25	0.50	0.5500	f	3	16	29
29	2026-09-25	0.50	0.5500	f	3	16	30
30	2026-09-25	0.50	0.5500	f	3	16	31
31	2026-09-25	1.00	0.5500	f	3	12	16
\.


--
-- Data for Name: rol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rol (activo, id_rol, nombre, descripcion) FROM stdin;
t	1	Administrador	Usuarios, roles, auditoria, parametros, catalogo, precios, empleados y canal web.
t	2	Ejecutivo comercial	Clientes, solicitudes, cotizaciones y ordenes de compra.
t	3	Jefe de produccion	Listas de materiales, ordenes de trabajo y registro en taller.
t	4	Operario de taller	Registro de horas hombre y consumo de materiales en taller.
t	5	Inspector de calidad	Protocolos, ensayos y no conformidades.
t	6	Encargado de bodega	Materiales, proveedores, bodegas, movimientos y kardex.
\.


--
-- Data for Name: rol_permiso; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rol_permiso (id, otorgado_en, id_permiso, id_rol) FROM stdin;
1	2026-09-25 09:04:51.765972+00	30	1
2	2026-09-25 09:04:51.769193+00	33	1
3	2026-09-25 09:04:51.770782+00	22	1
4	2026-09-25 09:04:51.772216+00	82	1
5	2026-09-25 09:04:51.773553+00	7	1
6	2026-09-25 09:04:51.775017+00	16	1
7	2026-09-25 09:04:51.776351+00	32	1
8	2026-09-25 09:04:51.777661+00	92	1
9	2026-09-25 09:04:51.778976+00	29	1
10	2026-09-25 09:04:51.780285+00	93	1
11	2026-09-25 09:04:51.782294+00	1	1
12	2026-09-25 09:04:51.783812+00	54	1
13	2026-09-25 09:04:51.785142+00	74	1
14	2026-09-25 09:04:51.786561+00	3	1
15	2026-09-25 09:04:51.78786+00	25	1
16	2026-09-25 09:04:51.789164+00	86	1
17	2026-09-25 09:04:51.79041+00	15	1
18	2026-09-25 09:04:51.791741+00	17	1
19	2026-09-25 09:04:51.793038+00	4	1
20	2026-09-25 09:04:51.794306+00	80	1
21	2026-09-25 09:04:51.795598+00	6	1
22	2026-09-25 09:04:51.796878+00	14	1
23	2026-09-25 09:04:51.798229+00	89	1
24	2026-09-25 09:04:51.799712+00	78	1
25	2026-09-25 09:04:51.801053+00	31	1
26	2026-09-25 09:04:51.802423+00	21	1
27	2026-09-25 09:04:51.8038+00	62	1
28	2026-09-25 09:04:51.805102+00	42	1
29	2026-09-25 09:04:51.806393+00	85	1
30	2026-09-25 09:04:51.807757+00	9	1
31	2026-09-25 09:04:51.809039+00	8	1
32	2026-09-25 09:04:51.810546+00	2	1
33	2026-09-25 09:04:51.813265+00	66	1
34	2026-09-25 09:04:51.8154+00	88	1
35	2026-09-25 09:04:51.817353+00	91	1
36	2026-09-25 09:04:51.819473+00	24	1
37	2026-09-25 09:04:51.821062+00	87	1
38	2026-09-25 09:04:51.82288+00	46	1
39	2026-09-25 09:04:51.824816+00	5	1
40	2026-09-25 09:04:51.82647+00	79	1
41	2026-09-25 09:04:51.828361+00	83	1
42	2026-09-25 09:04:51.830107+00	90	1
43	2026-09-25 09:04:51.831565+00	81	1
44	2026-09-25 09:04:51.832992+00	84	1
45	2026-09-25 09:04:51.834677+00	23	1
46	2026-09-25 09:04:51.836507+00	13	1
47	2026-09-25 09:04:51.839281+00	38	2
48	2026-09-25 09:04:51.840619+00	20	2
49	2026-09-25 09:04:51.841904+00	33	2
50	2026-09-25 09:04:51.843287+00	40	2
51	2026-09-25 09:04:51.844649+00	41	2
52	2026-09-25 09:04:51.846324+00	45	2
53	2026-09-25 09:04:51.848176+00	82	2
54	2026-09-25 09:04:51.849823+00	18	2
55	2026-09-25 09:04:51.851271+00	44	2
56	2026-09-25 09:04:51.852677+00	34	2
57	2026-09-25 09:04:51.85412+00	29	2
58	2026-09-25 09:04:51.855492+00	35	2
59	2026-09-25 09:04:51.856834+00	92	2
60	2026-09-25 09:04:51.85822+00	93	2
61	2026-09-25 09:04:51.85961+00	25	2
62	2026-09-25 09:04:51.860962+00	86	2
63	2026-09-25 09:04:51.862337+00	43	2
64	2026-09-25 09:04:51.863676+00	17	2
65	2026-09-25 09:04:51.864926+00	39	2
66	2026-09-25 09:04:51.866356+00	89	2
67	2026-09-25 09:04:51.867923+00	21	2
68	2026-09-25 09:04:51.869482+00	62	2
69	2026-09-25 09:04:51.87093+00	42	2
70	2026-09-25 09:04:51.872273+00	88	2
71	2026-09-25 09:04:51.873687+00	91	2
72	2026-09-25 09:04:51.875019+00	87	2
73	2026-09-25 09:04:51.876276+00	46	2
74	2026-09-25 09:04:51.877823+00	36	2
75	2026-09-25 09:04:51.879262+00	19	2
76	2026-09-25 09:04:51.880609+00	90	2
77	2026-09-25 09:04:51.881914+00	37	2
78	2026-09-25 09:04:51.884567+00	28	3
79	2026-09-25 09:04:51.885897+00	52	3
80	2026-09-25 09:04:51.887212+00	33	3
81	2026-09-25 09:04:51.888592+00	48	3
82	2026-09-25 09:04:51.889886+00	92	3
83	2026-09-25 09:04:51.89122+00	93	3
84	2026-09-25 09:04:51.892576+00	54	3
85	2026-09-25 09:04:51.894183+00	27	3
86	2026-09-25 09:04:51.895721+00	74	3
87	2026-09-25 09:04:51.897219+00	49	3
88	2026-09-25 09:04:51.898701+00	50	3
89	2026-09-25 09:04:51.900123+00	25	3
90	2026-09-25 09:04:51.901528+00	58	3
91	2026-09-25 09:04:51.902926+00	17	3
92	2026-09-25 09:04:51.904344+00	78	3
93	2026-09-25 09:04:51.905826+00	51	3
94	2026-09-25 09:04:51.907301+00	21	3
95	2026-09-25 09:04:51.9089+00	62	3
96	2026-09-25 09:04:51.91062+00	42	3
97	2026-09-25 09:04:51.912135+00	47	3
98	2026-09-25 09:04:51.913649+00	66	3
99	2026-09-25 09:04:51.915298+00	91	3
100	2026-09-25 09:04:51.917018+00	70	3
101	2026-09-25 09:04:51.918643+00	46	3
102	2026-09-25 09:04:51.920248+00	26	3
103	2026-09-25 09:04:51.921746+00	90	3
104	2026-09-25 09:04:51.923348+00	53	3
105	2026-09-25 09:04:51.924954+00	37	3
106	2026-09-25 09:04:51.928684+00	50	4
107	2026-09-25 09:04:51.930216+00	46	4
108	2026-09-25 09:04:51.931735+00	52	4
109	2026-09-25 09:04:51.933315+00	53	4
110	2026-09-25 09:04:51.934865+00	51	4
111	2026-09-25 09:04:51.93773+00	46	5
112	2026-09-25 09:04:51.939253+00	58	5
113	2026-09-25 09:04:51.940709+00	57	5
114	2026-09-25 09:04:51.942288+00	21	5
115	2026-09-25 09:04:51.943721+00	59	5
116	2026-09-25 09:04:51.945082+00	63	5
117	2026-09-25 09:04:51.946382+00	62	5
118	2026-09-25 09:04:51.94769+00	90	5
119	2026-09-25 09:04:51.949028+00	60	5
120	2026-09-25 09:04:51.950306+00	55	5
121	2026-09-25 09:04:51.951615+00	61	5
122	2026-09-25 09:04:51.952889+00	64	5
123	2026-09-25 09:04:51.954175+00	54	5
124	2026-09-25 09:04:51.955497+00	56	5
125	2026-09-25 09:04:51.956772+00	65	5
126	2026-09-25 09:04:51.961117+00	74	6
127	2026-09-25 09:04:51.963248+00	25	6
128	2026-09-25 09:04:51.965862+00	46	6
129	2026-09-25 09:04:51.968011+00	71	6
130	2026-09-25 09:04:51.970531+00	73	6
131	2026-09-25 09:04:51.973189+00	76	6
132	2026-09-25 09:04:51.976004+00	75	6
133	2026-09-25 09:04:51.978821+00	67	6
134	2026-09-25 09:04:51.981467+00	90	6
135	2026-09-25 09:04:51.984278+00	69	6
136	2026-09-25 09:04:51.986805+00	66	6
137	2026-09-25 09:04:51.989407+00	72	6
138	2026-09-25 09:04:51.991592+00	70	6
139	2026-09-25 09:04:51.9936+00	77	6
140	2026-09-25 09:04:51.995709+00	68	6
\.


--
-- Data for Name: solicitud_especificacion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitud_especificacion (id, valor, id_parametro, id_solicitud) FROM stdin;
1	100	11	4
2	23	12	4
3	400	13	4
4	Dyn11	14	4
5	ONAN	15	4
6	250	11	5
7	23	12	5
8	Dyn5	14	6
9	50	11	6
10	ONAF	15	6
11	5000	12	6
12	5000	13	6
13	Dyn11	14	7
14	50	11	7
15	ONAN	15	7
16	50001	12	7
17	50001	13	7
18	Dyn5	14	8
19	50	11	8
20	ONAN	15	8
21	2	12	8
22	2	13	8
23	Dyn11	14	9
24	100	11	9
25	ONAF	15	9
26	121	12	9
27	212	13	9
28	Dyn5	14	10
29	100	11	10
30	ONAN	15	10
31	12222	12	10
32	122	13	10
33	Dyn5	14	11
34	500	11	11
35	ONAN	15	11
36	100000	12	11
37	95000	13	11
38	Yzn11	14	12
39	500	11	12
40	ONAN	15	12
41	333	12	12
42	333	13	12
43	Dyn5	14	13
44	100	11	13
45	ONAN	15	13
46	22	12	13
47	22	13	13
\.


--
-- Data for Name: solicitud_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitud_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, estado_anterior_id, estado_nuevo_id, usuario_id, id_solicitud) FROM stdin;
2026-09-23 10:12:28.806252+00	2026-09-23 10:12:28.806267+00	2026-09-23 10:12:28.80628+00	Solicitud recibida desde la aplicacion web.	1	\N	1	2	1
2026-09-24 10:01:03.373667+00	2026-09-24 10:01:03.373683+00	2026-09-24 10:01:03.373698+00	Asignada a benjaadb.	2	1	2	1	1
2026-09-25 02:13:36.627939+00	2026-09-25 02:13:36.627948+00	2026-09-25 02:13:36.627958+00	Solicitud recibida desde la aplicacion web.	3	\N	1	8	4
2026-09-25 07:28:10.853139+00	2026-09-25 07:28:10.853155+00	2026-09-25 07:28:10.853171+00	Solicitud recibida desde la aplicacion web.	4	\N	1	8	6
2026-09-25 07:38:01.079969+00	2026-09-25 07:38:01.079981+00	2026-09-25 07:38:01.079992+00	Solicitud recibida desde la aplicacion web.	5	\N	1	8	7
2026-09-25 07:47:40.634621+00	2026-09-25 07:47:40.634633+00	2026-09-25 07:47:40.634643+00	Solicitud recibida desde la aplicacion web.	6	\N	1	8	8
2026-09-25 07:48:31.034053+00	2026-09-25 07:48:31.034065+00	2026-09-25 07:48:31.034077+00	Asignada a ejecutivo.	7	1	2	7	8
2026-09-25 08:18:13.754399+00	2026-09-25 08:18:13.754409+00	2026-09-25 08:18:13.75442+00	Solicitud recibida desde la aplicacion web.	8	\N	1	8	9
2026-09-25 08:18:38.429969+00	2026-09-25 08:18:38.429978+00	2026-09-25 08:18:38.429988+00	Cotizada en COT-2026-0003.	9	1	3	7	9
2026-09-25 18:04:12.429821+00	2026-09-25 18:04:12.429834+00	2026-09-25 18:04:12.429846+00	Solicitud recibida desde la aplicacion web.	10	\N	1	8	10
2026-09-25 18:04:31.400448+00	2026-09-25 18:04:31.400456+00	2026-09-25 18:04:31.400467+00	Cotizada en COT-2026-0004.	11	1	3	10	10
2026-09-25 18:32:09.859368+00	2026-09-25 18:32:09.85938+00	2026-09-25 18:32:09.85939+00	Solicitud recibida desde la aplicacion web.	12	\N	1	8	11
2026-09-25 20:09:44.022913+00	2026-09-25 20:09:44.022924+00	2026-09-25 20:09:44.022935+00	Asignada a comercial.	13	2	2	10	1
2026-09-25 20:09:55.200245+00	2026-09-25 20:09:55.200257+00	2026-09-25 20:09:55.200267+00	Asignada a comercial.	14	1	2	10	11
2026-09-25 20:10:25.957465+00	2026-09-25 20:10:25.957472+00	2026-09-25 20:10:25.957481+00	Cotizada en COT-2026-0005.	15	2	3	10	11
2026-09-25 20:33:19.691677+00	2026-09-25 20:33:19.691688+00	2026-09-25 20:33:19.691698+00	Solicitud recibida desde la aplicacion web.	16	\N	1	8	12
2026-09-25 20:34:03.508282+00	2026-09-25 20:34:03.508295+00	2026-09-25 20:34:03.508307+00	Asignada a comercial.	17	1	2	10	12
2026-09-25 20:34:33.521878+00	2026-09-25 20:34:33.521889+00	2026-09-25 20:34:33.521899+00	Cotizada en COT-2026-0006.	18	2	3	10	12
2026-09-25 20:44:42.99107+00	2026-09-25 20:44:42.991084+00	2026-09-25 20:44:42.991094+00	Solicitud recibida desde la aplicacion web.	19	\N	1	8	13
2026-09-25 20:45:20.673637+00	2026-09-25 20:45:20.67365+00	2026-09-25 20:45:20.673663+00	Asignada a comercial.	20	1	2	10	13
2026-09-25 20:45:51.994296+00	2026-09-25 20:45:51.994305+00	2026-09-25 20:45:51.994315+00	Cotizada en COT-2026-0007.	21	2	3	10	13
2026-09-29 12:42:20.541741+00	2026-09-29 12:42:20.54175+00	2026-09-29 12:42:20.541761+00	Cotizada en COT-2026-0008.	22	1	3	10	5
2026-09-29 12:44:20.279369+00	2026-09-29 12:44:20.27938+00	2026-09-29 12:44:20.279392+00	Cotizacion COT-2026-0008 anulada.	23	3	2	10	5
\.


--
-- Data for Name: tarea_estandar_modelo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarea_estandar_modelo (id_tarea_estandar, nombre, secuencia, horas_estimadas, id_modelo) FROM stdin;
20	Ensayos de rutina	5	1.40	12
1	Corte y armado de nucleo	1	2.00	9
2	Bobinado de baja tension	2	2.00	9
3	Bobinado de alta tension	3	2.00	9
4	Ensamble y llenado de aceite	4	2.00	9
5	Ensayos de rutina	5	2.00	9
6	Corte y armado de nucleo	1	2.00	10
7	Bobinado de baja tension	2	2.00	10
8	Bobinado de alta tension	3	2.00	10
9	Ensamble y llenado de aceite	4	2.00	10
10	Ensayos de rutina	5	2.00	10
11	Corte y armado de nucleo	1	2.00	11
12	Bobinado de baja tension	2	2.00	11
13	Bobinado de alta tension	3	2.00	11
14	Ensamble y llenado de aceite	4	2.00	11
15	Ensayos de rutina	5	2.00	11
16	Corte y armado de nucleo	1	2.00	12
17	Bobinado de baja tension	2	2.00	12
18	Bobinado de alta tension	3	2.00	12
19	Ensamble y llenado de aceite	4	2.00	12
21	Instalacion de materiales	1	1.00	14
22	Fijacion Componentes	2	1.00	14
23	Ensamblaje Completo	3	0.25	14
\.


--
-- Data for Name: tarifa_hora_hombre; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarifa_hora_hombre (id_tarifa, valor_hora_uf, vigente_desde, vigente_hasta, id_empleado) FROM stdin;
1	0.5000	2026-01-01	\N	1
2	0.4500	2026-01-01	\N	2
3	0.5500	2026-01-01	\N	3
4	10.0000	2026-09-29	\N	4
\.


--
-- Data for Name: token_blacklist_outstandingtoken; Type: TABLE DATA; Schema: public; Owner: -
--

-- Datos de token_blacklist_outstandingtoken omitidos (sesiones, tokens o historial del admin)


--
-- Data for Name: token_blacklist_blacklistedtoken; Type: TABLE DATA; Schema: public; Owner: -
--

-- Datos de token_blacklist_blacklistedtoken omitidos (sesiones, tokens o historial del admin)


--
-- Data for Name: transaccion_pago; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transaccion_pago (id_transaccion, id_externo, pasarela, monto, moneda, estado, iniciada_en, resuelta_en, respuesta, id_documento_cobro) FROM stdin;
1	1L788415FP4935615	paypal	2532.58	USD	cancelada	2026-09-25 02:17:34.85579+00	2026-09-25 02:18:29.965841+00	{"orden": {"id": "1L788415FP4935615", "estado": "PAYER_ACTION_REQUIRED"}, "conversion": {"monto_clp": "2429730.00", "monto_usd": "2532.58", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "60b2ee19-26db-497b-98cc-d41a24cf6a86"}	1
2	4WH06751CA454654C	paypal	2532.58	USD	cancelada	2026-09-25 02:18:32.835004+00	2026-09-25 02:23:39.35231+00	{"orden": {"id": "4WH06751CA454654C", "estado": "PAYER_ACTION_REQUIRED"}, "conversion": {"monto_clp": "2429730.00", "monto_usd": "2532.58", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "c780526f-f9f2-4704-bf4b-9aaba52d3050"}	1
3	0Y583175JU6545513	paypal	2532.58	USD	cancelada	2026-09-25 02:23:45.543551+00	2026-09-25 02:24:17.616495+00	{"orden": {"id": "0Y583175JU6545513", "estado": "PAYER_ACTION_REQUIRED"}, "conversion": {"monto_clp": "2429730.00", "monto_usd": "2532.58", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "aac343c5-89af-4912-9162-8797e96d9856"}	1
4	4CR36449UT0785529	paypal	2532.58	USD	cancelada	2026-09-25 02:26:43.452845+00	2026-09-25 02:30:13.231095+00	{"orden": {"id": "4CR36449UT0785529", "estado": "PAYER_ACTION_REQUIRED"}, "conversion": {"monto_clp": "2429730.00", "monto_usd": "2532.58", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "4f75bd62-ded8-4c87-b5f7-442bbd5234d2"}	1
5	2WF72195YD9756041	paypal	2532.58	USD	aprobada	2026-09-25 02:32:41.541752+00	2026-09-25 02:33:35.011568+00	{"orden": {"id": "2WF72195YD9756041", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "8VS28230N7249813S", "monto": {"valor": "2532.58", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "2429730.00", "monto_usd": "2532.58", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "b6563253-81da-468a-b1eb-03dc920e560a"}	1
6	6MP02347FF579830B	paypal	6411.59	USD	aprobada	2026-09-25 07:59:08.667211+00	2026-09-25 07:59:30.136231+00	{"orden": {"id": "6MP02347FF579830B", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "2DK27173YK539453C", "monto": {"valor": "6411.59", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "6151215.00", "monto_usd": "6411.59", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "df8cbc3d-71cc-4422-89c5-3e7021c8c249"}	2
7	2CG96871FV821860R	paypal	25325.78	USD	aprobada	2026-09-25 08:21:52.035983+00	2026-09-25 08:22:11.294548+00	{"orden": {"id": "2CG96871FV821860R", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "09E59441A3417602G", "monto": {"valor": "25325.78", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "24297299.00", "monto_usd": "25325.78", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "979a3179-1152-4d13-85b5-e366ece8da04"}	3
8	167871419F152234B	paypal	28531.57	USD	aprobada	2026-09-25 18:06:58.840423+00	2026-09-25 18:07:12.043357+00	{"orden": {"id": "167871419F152234B", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "7VN857755A843994R", "monto": {"valor": "28531.57", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "27372907.00", "monto_usd": "28531.57", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "e8f516cc-a494-484d-a6c4-df0276fa2caf"}	4
9	06N30997C8643492G	paypal	8818.07	USD	aprobada	2026-09-25 20:08:05.612918+00	2026-09-25 20:08:20.640319+00	{"orden": {"id": "06N30997C8643492G", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "5BU49624CS0618013", "monto": {"valor": "8818.07", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "8459971.00", "monto_usd": "8818.07", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "5e552506-e6ea-4139-ae08-db4efa37d306"}	5
10	5ME23869JX4590734	paypal	1942.71	USD	aprobada	2026-09-25 20:11:28.538982+00	2026-09-25 20:11:35.171572+00	{"orden": {"id": "5ME23869JX4590734", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "4FD711744M9040727", "monto": {"valor": "1942.71", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "1863818.00", "monto_usd": "1942.71", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "e36ba1f6-d691-48f7-8066-e81974762bed"}	6
11	26V21497HC984222R	paypal	4274.39	USD	aprobada	2026-09-25 20:36:22.102693+00	2026-09-25 20:36:36.220156+00	{"orden": {"id": "26V21497HC984222R", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "88A26113JV496493C", "monto": {"valor": "4274.39", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "4100810.00", "monto_usd": "4274.39", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "290ff1be-caed-483e-91ed-991e2133dde2"}	8
12	1Y261100CC6822530	paypal	7832.83	USD	aprobada	2026-09-25 20:47:59.347091+00	2026-09-25 20:48:07.477039+00	{"orden": {"id": "1Y261100CC6822530", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "368585144K726684V", "monto": {"valor": "7832.83", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "7514734.00", "monto_usd": "7832.83", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "9cbf63d6-805c-4a86-825b-0bab0e997f71"}	9
13	0G245954Y94744203	paypal	7832.83	USD	aprobada	2026-09-25 20:57:17.504943+00	2026-09-25 20:57:23.653718+00	{"orden": {"id": "0G245954Y94744203", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "0S268464LL999270X", "monto": {"valor": "7832.83", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "7514734.00", "monto_usd": "7832.83", "fecha_dolar": "2026-09-24", "dolar_observado": "959.3900"}, "clave_idempotencia": "2d5204a8-c382-4a2e-be68-8612d3a46a64"}	10
\.


--
-- Data for Name: usuario_rol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_rol (id, asignado_en, id_rol, id_usuario) FROM stdin;
1	2026-09-25 09:04:52.407555+00	1	9
2	2026-09-25 09:04:52.788761+00	2	10
3	2026-09-25 09:04:53.188545+00	2	11
4	2026-09-25 09:04:53.569897+00	3	12
5	2026-09-25 09:04:53.940694+00	4	13
6	2026-09-25 09:04:54.327117+00	5	14
7	2026-09-25 09:04:54.715569+00	6	15
8	2026-09-25 18:47:01.238905+00	4	16
\.


--
-- Data for Name: valor_parametro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.valor_parametro (activo, id_valor, valor, orden, id_parametro) FROM stdin;
t	21	50	0	11
t	22	100	1	11
t	23	150	2	11
t	24	250	3	11
t	25	500	4	11
t	26	Dyn11	0	14
t	27	Dyn5	1	14
t	28	Yzn11	2	14
t	29	ONAN	0	15
t	30	ONAF	1	15
\.


--
-- Name: auditoria_id_auditoria_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auditoria_id_auditoria_seq', 58, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 244, true);


--
-- Name: aviso_sitio_id_aviso_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.aviso_sitio_id_aviso_seq', 4, true);


--
-- Name: bodega_id_bodega_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bodega_id_bodega_seq', 1, true);


--
-- Name: bom_modelo_id_bom_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bom_modelo_id_bom_seq', 27, true);


--
-- Name: categoria_material_id_categoria_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.categoria_material_id_categoria_seq', 5, true);


--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cliente_id_cliente_seq', 4, true);


--
-- Name: comuna_id_comuna_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.comuna_id_comuna_seq', 3, true);


--
-- Name: consumo_material_id_consumo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.consumo_material_id_consumo_seq', 7, true);


--
-- Name: contacto_cliente_id_contacto_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contacto_cliente_id_contacto_seq', 1, false);


--
-- Name: control_calidad_id_control_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.control_calidad_id_control_seq', 2, true);


--
-- Name: cotizacion_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotizacion_historial_id_historial_seq', 26, true);


--
-- Name: cotizacion_id_cotizacion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotizacion_id_cotizacion_seq', 10, true);


--
-- Name: cotizacion_linea_id_linea_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotizacion_linea_id_linea_seq', 13, true);


--
-- Name: direccion_cliente_id_direccion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.direccion_cliente_id_direccion_seq', 3, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 8, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 61, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 42, true);


--
-- Name: documento_cobro_id_documento_cobro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documento_cobro_id_documento_cobro_seq', 10, true);


--
-- Name: empleado_id_empleado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.empleado_id_empleado_seq', 4, true);


--
-- Name: estado_documento_id_estado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estado_documento_id_estado_seq', 21, true);


--
-- Name: familia_producto_id_familia_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.familia_producto_id_familia_seq', 6, true);


--
-- Name: feriado_id_feriado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.feriado_id_feriado_seq', 32, true);


--
-- Name: indicador_economico_id_indicador_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.indicador_economico_id_indicador_seq', 5, true);


--
-- Name: log_integracion_id_log_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.log_integracion_id_log_seq', 69, true);


--
-- Name: material_id_material_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.material_id_material_seq', 6, true);


--
-- Name: modelo_parametro_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modelo_parametro_id_seq', 69, true);


--
-- Name: modelo_producto_id_modelo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modelo_producto_id_modelo_seq', 14, true);


--
-- Name: movimiento_inventario_id_movimiento_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.movimiento_inventario_id_movimiento_seq', 15, true);


--
-- Name: no_conformidad_id_no_conformidad_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.no_conformidad_id_no_conformidad_seq', 4, true);


--
-- Name: orden_compra_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_compra_historial_id_historial_seq', 22, true);


--
-- Name: orden_compra_id_orden_compra_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_compra_id_orden_compra_seq', 8, true);


--
-- Name: orden_compra_linea_id_linea_oc_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_compra_linea_id_linea_oc_seq', 8, true);


--
-- Name: orden_trabajo_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_trabajo_historial_id_historial_seq', 19, true);


--
-- Name: orden_trabajo_id_orden_trabajo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_trabajo_id_orden_trabajo_seq', 8, true);


--
-- Name: parametro_sistema_id_parametro_sistema_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.parametro_sistema_id_parametro_sistema_seq', 14, true);


--
-- Name: parametro_tecnico_id_parametro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.parametro_tecnico_id_parametro_seq', 15, true);


--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.permiso_id_permiso_seq', 93, true);


--
-- Name: precio_base_modelo_id_precio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.precio_base_modelo_id_precio_seq', 12, true);


--
-- Name: precio_material_id_precio_material_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.precio_material_id_precio_material_seq', 6, true);


--
-- Name: protocolo_calidad_id_protocolo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.protocolo_calidad_id_protocolo_seq', 5, true);


--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proveedor_id_proveedor_seq', 2, true);


--
-- Name: punto_control_id_punto_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.punto_control_id_punto_seq', 48, true);


--
-- Name: region_id_region_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.region_id_region_seq', 3, true);


--
-- Name: registro_hora_hombre_id_registro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.registro_hora_hombre_id_registro_seq', 31, true);


--
-- Name: resultado_control_id_resultado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resultado_control_id_resultado_seq', 24, true);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_id_rol_seq', 6, true);


--
-- Name: rol_permiso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_permiso_id_seq', 142, true);


--
-- Name: solicitud_especificacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_especificacion_id_seq', 47, true);


--
-- Name: solicitud_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_historial_id_historial_seq', 23, true);


--
-- Name: solicitud_presupuesto_id_solicitud_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_presupuesto_id_solicitud_seq', 13, true);


--
-- Name: tarea_estandar_modelo_id_tarea_estandar_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarea_estandar_modelo_id_tarea_estandar_seq', 23, true);


--
-- Name: tarea_ot_id_tarea_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarea_ot_id_tarea_seq', 31, true);


--
-- Name: tarifa_hora_hombre_id_tarifa_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarifa_hora_hombre_id_tarifa_seq', 4, true);


--
-- Name: token_blacklist_blacklistedtoken_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.token_blacklist_blacklistedtoken_id_seq', 6, true);


--
-- Name: token_blacklist_outstandingtoken_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.token_blacklist_outstandingtoken_id_seq', 8, true);


--
-- Name: transaccion_pago_id_transaccion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.transaccion_pago_id_transaccion_seq', 13, true);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_id_usuario_seq', 16, true);


--
-- Name: usuario_rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_rol_id_seq', 8, true);


--
-- Name: valor_parametro_id_valor_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.valor_parametro_id_valor_seq', 30, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 2h5fweI90gBZT6fnwBIe5jRrNApeVCUqzrQScsVcPmYsubYm98iQqrcut5FHNSy

