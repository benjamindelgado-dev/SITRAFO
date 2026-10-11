--
-- PostgreSQL database dump
--

\restrict 5OSbILiaRgkTemGqSZHjcTJh7QwbZf4Ja3WFuYWYrDV5um5dBShntjp8VRZa9MO

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

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
2026-10-10 23:32:37.817098-03	2026-10-10 23:32:37.817113-03	1	76543210-3	Electrica del Maipo SpA		juridica	Distribucion electrica	activo
\.


--
-- Data for Name: usuario; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario (password, last_login, id_usuario, username, email, es_interno, estado, intentos_fallidos, ultimo_acceso, is_staff, is_superuser, is_active, creado_en, id_cliente, bloqueado_hasta) FROM stdin;
!MxaE5S2rPlxu8zKuybDGYfQFKh0dHPKPiMX5litU	\N	1	administrador	administrador@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:35.312481-03	\N	\N
!p7GQMkvW6q8WssUqCCKFYdcemDW5GbQ9Z8WG5vXY	\N	7	bodega	bodega@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:36.645116-03	\N	\N
!6kEc0Pv9lhqE9YV2VaG50rboKnHcM0SvqFeRfqhe	\N	6	calidad	calidad@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:36.424432-03	\N	\N
!xHPzuQINZAUcu4NjtkYpOLcpkVHkvlDp7JojOEkf	\N	2	comercial	comercial@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:35.543263-03	\N	\N
!UJPM9fTxC5YNIjgv26qVrinJAInkt6FmdrBiqEe0	\N	3	comercial2	comercial2@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:35.766432-03	\N	\N
!4e5WgJ2JeUnyCDKttAXTFBn0Qs405DrXDB025SdS	\N	8	ejecutivo	ejecutivo@sitrafo.cl	t	activo	0	\N	t	t	t	2026-10-10 23:32:37.582999-03	\N	\N
!cBjyh1xgnCqTDRFku8TqUPjhf7ANHoGfWH8pIig5	\N	9	maipo	contacto@maipo.cl	f	activo	0	\N	f	f	t	2026-10-10 23:32:37.821884-03	1	\N
!SGftgNoXi1FIKvLlEVk1Ykg9WZrZpvZgts3DlbRy	\N	5	operario	operario@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:36.207678-03	\N	\N
!A2VQkBO6GeC3do89DlblTFO1e0sZHtviTullDHd0	\N	4	produccion	produccion@sitrafo.cl	t	activo	0	\N	f	f	t	2026-10-10 23:32:35.983597-03	\N	\N
\.


--
-- Data for Name: auditoria; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auditoria (id_auditoria, entidad, id_registro, accion, valor_anterior, valor_nuevo, fecha_hora, origen, id_usuario) FROM stdin;
1	documento_cobro	1	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "DEMO-SIM-ORDEN-001"}	2026-10-10 23:32:44.105629-03	web	9
2	no_conformidad	1	modificacion	{"estado": "abierta"}	{"accion": "Se reajusto el apriete del nucleo y se repitio el ensayo.", "estado": "cerrada"}	2026-10-10 23:32:45.093091-03	escritorio	6
3	control_calidad	1	modificacion	{"estado": "conforme"}	{"orden": "OT-2026-0001", "estado": "aprobado"}	2026-10-10 23:32:45.104181-03	escritorio	6
4	documento_cobro	2	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "DEMO-SIM-ORDEN-002"}	2026-10-10 23:32:45.360464-03	web	9
5	documento_cobro	3	modificacion	{"estado": "pendiente"}	{"estado": "pagado", "pasarela": "paypal", "transaccion": "DEMO-SIM-ORDEN-003"}	2026-10-10 23:32:46.435013-03	web	9
6	aviso_sitio	1	modificacion	\N	{"tipo": "informativo", "activo": true, "titulo": "Horario de atencion de fin de año", "vigente_desde": "2026-10-10 00:00:00-03:00", "vigente_hasta": "2026-12-31 23:59:00-03:00"}	2026-10-10 23:32:46.51831-03	escritorio	1
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
6	token_blacklist	blacklistedtoken
7	token_blacklist	outstandingtoken
8	seguridad	permiso
9	seguridad	rol
10	seguridad	usuario
11	seguridad	usuariorol
12	seguridad	auditoria
13	seguridad	rolpermiso
14	clientes	cliente
15	clientes	comuna
16	clientes	region
17	clientes	contactocliente
18	clientes	direccioncliente
19	catalogo	familiaproducto
20	catalogo	parametrotecnico
21	catalogo	modeloproducto
22	catalogo	modeloparametro
23	catalogo	preciobasemodelo
24	catalogo	tareaestandarmodelo
25	catalogo	valorparametro
26	catalogo	bommodelo
27	comercial	cotizacion
28	comercial	cotizacionlinea
29	comercial	estadodocumento
30	comercial	cotizacionhistorial
31	comercial	ordencompra
32	comercial	ordencomprahistorial
33	comercial	ordencompralinea
34	comercial	solicitudpresupuesto
35	comercial	solicitudhistorial
36	comercial	solicitudespecificacion
37	produccion	empleado
38	produccion	ordentrabajo
39	produccion	ordentrabajohistorial
40	produccion	tareaot
41	produccion	registrohorahombre
42	produccion	consumomaterial
43	produccion	tarifahorahombre
44	inventario	bodega
45	inventario	categoriamaterial
46	inventario	proveedor
47	inventario	material
48	inventario	preciomaterial
49	inventario	movimientoinventario
50	calidad	noconformidad
51	calidad	protocolocalidad
52	calidad	puntocontrol
53	calidad	resultadocontrol
54	calidad	controlcalidad
55	pagos	documentocobro
56	pagos	indicadoreconomico
57	pagos	transaccionpago
58	configuracion	feriado
59	configuracion	avisositio
60	configuracion	logintegracion
61	configuracion	parametrosistema
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
21	Can add blacklisted token	6	add_blacklistedtoken
22	Can change blacklisted token	6	change_blacklistedtoken
23	Can delete blacklisted token	6	delete_blacklistedtoken
24	Can view blacklisted token	6	view_blacklistedtoken
25	Can add outstanding token	7	add_outstandingtoken
26	Can change outstanding token	7	change_outstandingtoken
27	Can delete outstanding token	7	delete_outstandingtoken
28	Can view outstanding token	7	view_outstandingtoken
29	Can add permiso	8	add_permiso
30	Can change permiso	8	change_permiso
31	Can delete permiso	8	delete_permiso
32	Can view permiso	8	view_permiso
33	Can add rol	9	add_rol
34	Can change rol	9	change_rol
35	Can delete rol	9	delete_rol
36	Can view rol	9	view_rol
37	Can add usuario	10	add_usuario
38	Can change usuario	10	change_usuario
39	Can delete usuario	10	delete_usuario
40	Can view usuario	10	view_usuario
41	Can add rol de usuario	11	add_usuariorol
42	Can change rol de usuario	11	change_usuariorol
43	Can delete rol de usuario	11	delete_usuariorol
44	Can view rol de usuario	11	view_usuariorol
45	Can add registro de auditoria	12	add_auditoria
46	Can change registro de auditoria	12	change_auditoria
47	Can delete registro de auditoria	12	delete_auditoria
48	Can view registro de auditoria	12	view_auditoria
49	Can add permiso de rol	13	add_rolpermiso
50	Can change permiso de rol	13	change_rolpermiso
51	Can delete permiso de rol	13	delete_rolpermiso
52	Can view permiso de rol	13	view_rolpermiso
53	Can add cliente	14	add_cliente
54	Can change cliente	14	change_cliente
55	Can delete cliente	14	delete_cliente
56	Can view cliente	14	view_cliente
57	Can add comuna	15	add_comuna
58	Can change comuna	15	change_comuna
59	Can delete comuna	15	delete_comuna
60	Can view comuna	15	view_comuna
61	Can add region	16	add_region
62	Can change region	16	change_region
63	Can delete region	16	delete_region
64	Can view region	16	view_region
65	Can add contacto de cliente	17	add_contactocliente
66	Can change contacto de cliente	17	change_contactocliente
67	Can delete contacto de cliente	17	delete_contactocliente
68	Can view contacto de cliente	17	view_contactocliente
69	Can add direccion de cliente	18	add_direccioncliente
70	Can change direccion de cliente	18	change_direccioncliente
71	Can delete direccion de cliente	18	delete_direccioncliente
72	Can view direccion de cliente	18	view_direccioncliente
73	Can add familia de producto	19	add_familiaproducto
74	Can change familia de producto	19	change_familiaproducto
75	Can delete familia de producto	19	delete_familiaproducto
76	Can view familia de producto	19	view_familiaproducto
77	Can add parametro tecnico	20	add_parametrotecnico
78	Can change parametro tecnico	20	change_parametrotecnico
79	Can delete parametro tecnico	20	delete_parametrotecnico
80	Can view parametro tecnico	20	view_parametrotecnico
81	Can add modelo de producto	21	add_modeloproducto
82	Can change modelo de producto	21	change_modeloproducto
83	Can delete modelo de producto	21	delete_modeloproducto
84	Can view modelo de producto	21	view_modeloproducto
85	Can add parametro del modelo	22	add_modeloparametro
86	Can change parametro del modelo	22	change_modeloparametro
87	Can delete parametro del modelo	22	delete_modeloparametro
88	Can view parametro del modelo	22	view_modeloparametro
89	Can add precio base de modelo	23	add_preciobasemodelo
90	Can change precio base de modelo	23	change_preciobasemodelo
91	Can delete precio base de modelo	23	delete_preciobasemodelo
92	Can view precio base de modelo	23	view_preciobasemodelo
93	Can add tarea estandar del modelo	24	add_tareaestandarmodelo
94	Can change tarea estandar del modelo	24	change_tareaestandarmodelo
95	Can delete tarea estandar del modelo	24	delete_tareaestandarmodelo
96	Can view tarea estandar del modelo	24	view_tareaestandarmodelo
97	Can add valor de parametro	25	add_valorparametro
98	Can change valor de parametro	25	change_valorparametro
99	Can delete valor de parametro	25	delete_valorparametro
100	Can view valor de parametro	25	view_valorparametro
101	Can add material del modelo	26	add_bommodelo
102	Can change material del modelo	26	change_bommodelo
103	Can delete material del modelo	26	delete_bommodelo
104	Can view material del modelo	26	view_bommodelo
105	Can add cotizacion	27	add_cotizacion
106	Can change cotizacion	27	change_cotizacion
107	Can delete cotizacion	27	delete_cotizacion
108	Can view cotizacion	27	view_cotizacion
109	Can add linea de cotizacion	28	add_cotizacionlinea
110	Can change linea de cotizacion	28	change_cotizacionlinea
111	Can delete linea de cotizacion	28	delete_cotizacionlinea
112	Can view linea de cotizacion	28	view_cotizacionlinea
113	Can add estado de documento	29	add_estadodocumento
114	Can change estado de documento	29	change_estadodocumento
115	Can delete estado de documento	29	delete_estadodocumento
116	Can view estado de documento	29	view_estadodocumento
117	Can add historial de la cotizacion	30	add_cotizacionhistorial
118	Can change historial de la cotizacion	30	change_cotizacionhistorial
119	Can delete historial de la cotizacion	30	delete_cotizacionhistorial
120	Can view historial de la cotizacion	30	view_cotizacionhistorial
121	Can add orden de compra	31	add_ordencompra
122	Can change orden de compra	31	change_ordencompra
123	Can delete orden de compra	31	delete_ordencompra
124	Can view orden de compra	31	view_ordencompra
125	Can add historial de la orden de compra	32	add_ordencomprahistorial
126	Can change historial de la orden de compra	32	change_ordencomprahistorial
127	Can delete historial de la orden de compra	32	delete_ordencomprahistorial
128	Can view historial de la orden de compra	32	view_ordencomprahistorial
129	Can add linea de orden de compra	33	add_ordencompralinea
130	Can change linea de orden de compra	33	change_ordencompralinea
131	Can delete linea de orden de compra	33	delete_ordencompralinea
132	Can view linea de orden de compra	33	view_ordencompralinea
133	Can add solicitud de presupuesto	34	add_solicitudpresupuesto
134	Can change solicitud de presupuesto	34	change_solicitudpresupuesto
135	Can delete solicitud de presupuesto	34	delete_solicitudpresupuesto
136	Can view solicitud de presupuesto	34	view_solicitudpresupuesto
137	Can add historial de la solicitud	35	add_solicitudhistorial
138	Can change historial de la solicitud	35	change_solicitudhistorial
139	Can delete historial de la solicitud	35	delete_solicitudhistorial
140	Can view historial de la solicitud	35	view_solicitudhistorial
141	Can add especificacion de la solicitud	36	add_solicitudespecificacion
142	Can change especificacion de la solicitud	36	change_solicitudespecificacion
143	Can delete especificacion de la solicitud	36	delete_solicitudespecificacion
144	Can view especificacion de la solicitud	36	view_solicitudespecificacion
145	Can add empleado	37	add_empleado
146	Can change empleado	37	change_empleado
147	Can delete empleado	37	delete_empleado
148	Can view empleado	37	view_empleado
149	Can add orden de trabajo	38	add_ordentrabajo
150	Can change orden de trabajo	38	change_ordentrabajo
151	Can delete orden de trabajo	38	delete_ordentrabajo
152	Can view orden de trabajo	38	view_ordentrabajo
153	Can add historial de la orden de trabajo	39	add_ordentrabajohistorial
154	Can change historial de la orden de trabajo	39	change_ordentrabajohistorial
155	Can delete historial de la orden de trabajo	39	delete_ordentrabajohistorial
156	Can view historial de la orden de trabajo	39	view_ordentrabajohistorial
157	Can add tarea de la orden de trabajo	40	add_tareaot
158	Can change tarea de la orden de trabajo	40	change_tareaot
159	Can delete tarea de la orden de trabajo	40	delete_tareaot
160	Can view tarea de la orden de trabajo	40	view_tareaot
161	Can add registro de horas hombre	41	add_registrohorahombre
162	Can change registro de horas hombre	41	change_registrohorahombre
163	Can delete registro de horas hombre	41	delete_registrohorahombre
164	Can view registro de horas hombre	41	view_registrohorahombre
165	Can add consumo de material	42	add_consumomaterial
166	Can change consumo de material	42	change_consumomaterial
167	Can delete consumo de material	42	delete_consumomaterial
168	Can view consumo de material	42	view_consumomaterial
169	Can add tarifa de hora hombre	43	add_tarifahorahombre
170	Can change tarifa de hora hombre	43	change_tarifahorahombre
171	Can delete tarifa de hora hombre	43	delete_tarifahorahombre
172	Can view tarifa de hora hombre	43	view_tarifahorahombre
173	Can add bodega	44	add_bodega
174	Can change bodega	44	change_bodega
175	Can delete bodega	44	delete_bodega
176	Can view bodega	44	view_bodega
177	Can add categoria de material	45	add_categoriamaterial
178	Can change categoria de material	45	change_categoriamaterial
179	Can delete categoria de material	45	delete_categoriamaterial
180	Can view categoria de material	45	view_categoriamaterial
181	Can add proveedor	46	add_proveedor
182	Can change proveedor	46	change_proveedor
183	Can delete proveedor	46	delete_proveedor
184	Can view proveedor	46	view_proveedor
185	Can add material	47	add_material
186	Can change material	47	change_material
187	Can delete material	47	delete_material
188	Can view material	47	view_material
189	Can add precio de material	48	add_preciomaterial
190	Can change precio de material	48	change_preciomaterial
191	Can delete precio de material	48	delete_preciomaterial
192	Can view precio de material	48	view_preciomaterial
193	Can add movimiento de inventario	49	add_movimientoinventario
194	Can change movimiento de inventario	49	change_movimientoinventario
195	Can delete movimiento de inventario	49	delete_movimientoinventario
196	Can view movimiento de inventario	49	view_movimientoinventario
197	Can add no conformidad	50	add_noconformidad
198	Can change no conformidad	50	change_noconformidad
199	Can delete no conformidad	50	delete_noconformidad
200	Can view no conformidad	50	view_noconformidad
201	Can add protocolo de calidad	51	add_protocolocalidad
202	Can change protocolo de calidad	51	change_protocolocalidad
203	Can delete protocolo de calidad	51	delete_protocolocalidad
204	Can view protocolo de calidad	51	view_protocolocalidad
205	Can add punto de control	52	add_puntocontrol
206	Can change punto de control	52	change_puntocontrol
207	Can delete punto de control	52	delete_puntocontrol
208	Can view punto de control	52	view_puntocontrol
209	Can add resultado de control	53	add_resultadocontrol
210	Can change resultado de control	53	change_resultadocontrol
211	Can delete resultado de control	53	delete_resultadocontrol
212	Can view resultado de control	53	view_resultadocontrol
213	Can add control de calidad	54	add_controlcalidad
214	Can change control de calidad	54	change_controlcalidad
215	Can delete control de calidad	54	delete_controlcalidad
216	Can view control de calidad	54	view_controlcalidad
217	Can add documento de cobro	55	add_documentocobro
218	Can change documento de cobro	55	change_documentocobro
219	Can delete documento de cobro	55	delete_documentocobro
220	Can view documento de cobro	55	view_documentocobro
221	Can add indicador economico	56	add_indicadoreconomico
222	Can change indicador economico	56	change_indicadoreconomico
223	Can delete indicador economico	56	delete_indicadoreconomico
224	Can view indicador economico	56	view_indicadoreconomico
225	Can add transaccion de pago	57	add_transaccionpago
226	Can change transaccion de pago	57	change_transaccionpago
227	Can delete transaccion de pago	57	delete_transaccionpago
228	Can view transaccion de pago	57	view_transaccionpago
229	Can add feriado	58	add_feriado
230	Can change feriado	58	change_feriado
231	Can delete feriado	58	delete_feriado
232	Can view feriado	58	view_feriado
233	Can add aviso del sitio	59	add_avisositio
234	Can change aviso del sitio	59	change_avisositio
235	Can delete aviso del sitio	59	delete_avisositio
236	Can view aviso del sitio	59	view_avisositio
237	Can add llamada a servicio externo	60	add_logintegracion
238	Can change llamada a servicio externo	60	change_logintegracion
239	Can delete llamada a servicio externo	60	delete_logintegracion
240	Can view llamada a servicio externo	60	view_logintegracion
241	Can add parametro del sistema	61	add_parametrosistema
242	Can change parametro del sistema	61	change_parametrosistema
243	Can delete parametro del sistema	61	delete_parametrosistema
244	Can view parametro del sistema	61	view_parametrosistema
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
1	Horario de atencion de fin de año	Entre el 24 y el 31 de diciembre el area comercial atiende de 9:00 a 14:00.	informativo	2026-10-10 00:00:00-03	2026-12-31 23:59:00-03	t	1
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
t	1	Distribucion trifasicos	
t	2	Distribucion monofasicos	
\.


--
-- Data for Name: material; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.material (activo, id_material, codigo, nombre, unidad_medida, stock_minimo, id_categoria) FROM stdin;
t	1	ACE-SI	Acero al silicio grano orientado	kg	500.0000	1
t	2	CU-ESM	Alambre de cobre esmaltado	kg	200.0000	2
t	3	ACT-DIE	Aceite dielectrico mineral	l	400.0000	3
t	4	AIS-BT	Aislador pasatapas BT	un	20.0000	4
t	5	AIS-AT	Aislador pasatapas AT	un	15.0000	4
t	6	TNQ-01	Tanque de acero con radiadores	un	4.0000	5
\.


--
-- Data for Name: modelo_producto; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modelo_producto (activo, id_modelo, codigo, nombre, descripcion, publicado, id_familia) FROM stdin;
t	1	TD-050	Transformador de distribucion 50 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	1
t	2	TD-100	Transformador de distribucion 100 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	1
t	3	TD-250	Transformador de distribucion 250 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	1
t	4	TM-025	Transformador monofasico 25 kVA	Transformador sumergido en aceite mineral, apto para montaje exterior en poste o plataforma. Fabricado segun la especificacion tecnica indicada en la solicitud.	t	2
\.


--
-- Data for Name: bom_modelo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bom_modelo (id_bom, cantidad, observacion, id_material, id_modelo) FROM stdin;
1	108.0000		1	1
2	36.0000		2	1
3	90.0000		3	1
4	2.0000		4	1
5	2.0000		5	1
6	1.0000		6	1
7	180.0000		1	2
8	60.0000		2	2
9	150.0000		3	2
10	4.0000		4	2
11	3.0000		5	2
12	1.0000		6	2
13	360.0000		1	3
14	120.0000		2	3
15	300.0000		3	3
16	8.0000		4	3
17	6.0000		5	3
18	2.0000		6	3
19	63.0000		1	4
20	21.0000		2	4
21	52.5000		3	4
22	1.0000		4	4
23	1.0000		5	4
24	1.0000		6	4
\.


--
-- Data for Name: region; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.region (id_region, nombre, codigo) FROM stdin;
1	Arica y Parinacota	XV
2	Tarapacá	I
3	Antofagasta	II
4	Atacama	III
5	Coquimbo	IV
6	Valparaíso	V
7	Metropolitana de Santiago	RM
8	Libertador General Bernardo O'Higgins	VI
9	Maule	VII
10	Ñuble	XVI
11	Biobío	VIII
12	La Araucanía	IX
13	Los Ríos	XIV
14	Los Lagos	X
15	Aysén del General Carlos Ibáñez del Campo	XI
16	Magallanes y de la Antártica Chilena	XII
\.


--
-- Data for Name: comuna; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.comuna (id_comuna, nombre, id_region) FROM stdin;
1	Arica	1
2	Camarones	1
3	Putre	1
4	General Lagos	1
5	Iquique	2
6	Alto Hospicio	2
7	Pozo Almonte	2
8	Camiña	2
9	Colchane	2
10	Huara	2
11	Pica	2
12	Antofagasta	3
13	Mejillones	3
14	Sierra Gorda	3
15	Taltal	3
16	Calama	3
17	Ollagüe	3
18	San Pedro de Atacama	3
19	Tocopilla	3
20	María Elena	3
21	Copiapó	4
22	Caldera	4
23	Tierra Amarilla	4
24	Chañaral	4
25	Diego de Almagro	4
26	Vallenar	4
27	Alto del Carmen	4
28	Freirina	4
29	Huasco	4
30	La Serena	5
31	Coquimbo	5
32	Andacollo	5
33	La Higuera	5
34	Paiguano	5
35	Vicuña	5
36	Illapel	5
37	Canela	5
38	Los Vilos	5
39	Salamanca	5
40	Ovalle	5
41	Combarbalá	5
42	Monte Patria	5
43	Punitaqui	5
44	Río Hurtado	5
45	Valparaíso	6
46	Casablanca	6
47	Concón	6
48	Juan Fernández	6
49	Puchuncaví	6
50	Quintero	6
51	Viña del Mar	6
52	Isla de Pascua	6
53	Los Andes	6
54	Calle Larga	6
55	Rinconada	6
56	San Esteban	6
57	La Ligua	6
58	Cabildo	6
59	Papudo	6
60	Petorca	6
61	Zapallar	6
62	Quillota	6
63	La Calera	6
64	Hijuelas	6
65	La Cruz	6
66	Nogales	6
67	San Antonio	6
68	Algarrobo	6
69	Cartagena	6
70	El Quisco	6
71	El Tabo	6
72	Santo Domingo	6
73	San Felipe	6
74	Catemu	6
75	Llaillay	6
76	Panquehue	6
77	Putaendo	6
78	Santa María	6
79	Quilpué	6
80	Limache	6
81	Olmué	6
82	Villa Alemana	6
83	Santiago	7
84	Cerrillos	7
85	Cerro Navia	7
86	Conchalí	7
87	El Bosque	7
88	Estación Central	7
89	Huechuraba	7
90	Independencia	7
91	La Cisterna	7
92	La Florida	7
93	La Granja	7
94	La Pintana	7
95	La Reina	7
96	Las Condes	7
97	Lo Barnechea	7
98	Lo Espejo	7
99	Lo Prado	7
100	Macul	7
101	Maipú	7
102	Ñuñoa	7
103	Pedro Aguirre Cerda	7
104	Peñalolén	7
105	Providencia	7
106	Pudahuel	7
107	Quilicura	7
108	Quinta Normal	7
109	Recoleta	7
110	Renca	7
111	San Joaquín	7
112	San Miguel	7
113	San Ramón	7
114	Vitacura	7
115	Puente Alto	7
116	Pirque	7
117	San José de Maipo	7
118	Colina	7
119	Lampa	7
120	Tiltil	7
121	San Bernardo	7
122	Buin	7
123	Calera de Tango	7
124	Paine	7
125	Melipilla	7
126	Alhué	7
127	Curacaví	7
128	María Pinto	7
129	San Pedro	7
130	Talagante	7
131	El Monte	7
132	Isla de Maipo	7
133	Padre Hurtado	7
134	Peñaflor	7
135	Rancagua	8
136	Codegua	8
137	Coinco	8
138	Coltauco	8
139	Doñihue	8
140	Graneros	8
141	Las Cabras	8
142	Machalí	8
143	Malloa	8
144	Mostazal	8
145	Olivar	8
146	Peumo	8
147	Pichidegua	8
148	Quinta de Tilcoco	8
149	Rengo	8
150	Requínoa	8
151	San Vicente	8
152	Pichilemu	8
153	La Estrella	8
154	Litueche	8
155	Marchigüe	8
156	Navidad	8
157	Paredones	8
158	San Fernando	8
159	Chépica	8
160	Chimbarongo	8
161	Lolol	8
162	Nancagua	8
163	Palmilla	8
164	Peralillo	8
165	Placilla	8
166	Pumanque	8
167	Santa Cruz	8
168	Talca	9
169	Constitución	9
170	Curepto	9
171	Empedrado	9
172	Maule	9
173	Pelarco	9
174	Pencahue	9
175	Río Claro	9
176	San Clemente	9
177	San Rafael	9
178	Cauquenes	9
179	Chanco	9
180	Pelluhue	9
181	Curicó	9
182	Hualañé	9
183	Licantén	9
184	Molina	9
185	Rauco	9
186	Romeral	9
187	Sagrada Familia	9
188	Teno	9
189	Vichuquén	9
190	Linares	9
191	Colbún	9
192	Longaví	9
193	Parral	9
194	Retiro	9
195	San Javier	9
196	Villa Alegre	9
197	Yerbas Buenas	9
198	Chillán	10
199	Bulnes	10
200	Chillán Viejo	10
201	El Carmen	10
202	Pemuco	10
203	Pinto	10
204	Quillón	10
205	San Ignacio	10
206	Yungay	10
207	Quirihue	10
208	Cobquecura	10
209	Coelemu	10
210	Ninhue	10
211	Portezuelo	10
212	Ránquil	10
213	Treguaco	10
214	San Carlos	10
215	Coihueco	10
216	Ñiquén	10
217	San Fabián	10
218	San Nicolás	10
219	Concepción	11
220	Coronel	11
221	Chiguayante	11
222	Florida	11
223	Hualqui	11
224	Lota	11
225	Penco	11
226	San Pedro de la Paz	11
227	Santa Juana	11
228	Talcahuano	11
229	Tomé	11
230	Hualpén	11
231	Lebu	11
232	Arauco	11
233	Cañete	11
234	Contulmo	11
235	Curanilahue	11
236	Los Álamos	11
237	Tirúa	11
238	Los Ángeles	11
239	Antuco	11
240	Cabrero	11
241	Laja	11
242	Mulchén	11
243	Nacimiento	11
244	Negrete	11
245	Quilaco	11
246	Quilleco	11
247	San Rosendo	11
248	Santa Bárbara	11
249	Tucapel	11
250	Yumbel	11
251	Alto Biobío	11
252	Temuco	12
253	Carahue	12
254	Cunco	12
255	Curarrehue	12
256	Freire	12
257	Galvarino	12
258	Gorbea	12
259	Lautaro	12
260	Loncoche	12
261	Melipeuco	12
262	Nueva Imperial	12
263	Padre Las Casas	12
264	Perquenco	12
265	Pitrufquén	12
266	Pucón	12
267	Saavedra	12
268	Teodoro Schmidt	12
269	Toltén	12
270	Vilcún	12
271	Villarrica	12
272	Cholchol	12
273	Angol	12
274	Collipulli	12
275	Curacautín	12
276	Ercilla	12
277	Lonquimay	12
278	Los Sauces	12
279	Lumaco	12
280	Purén	12
281	Renaico	12
282	Traiguén	12
283	Victoria	12
284	Valdivia	13
285	Corral	13
286	Lanco	13
287	Los Lagos	13
288	Máfil	13
289	Mariquina	13
290	Paillaco	13
291	Panguipulli	13
292	La Unión	13
293	Futrono	13
294	Lago Ranco	13
295	Río Bueno	13
296	Puerto Montt	14
297	Calbuco	14
298	Cochamó	14
299	Fresia	14
300	Frutillar	14
301	Los Muermos	14
302	Llanquihue	14
303	Maullín	14
304	Puerto Varas	14
305	Castro	14
306	Ancud	14
307	Chonchi	14
308	Curaco de Vélez	14
309	Dalcahue	14
310	Puqueldón	14
311	Queilén	14
312	Quellón	14
313	Quemchi	14
314	Quinchao	14
315	Osorno	14
316	Puerto Octay	14
317	Purranque	14
318	Puyehue	14
319	Río Negro	14
320	San Juan de la Costa	14
321	San Pablo	14
322	Chaitén	14
323	Futaleufú	14
324	Hualaihué	14
325	Palena	14
326	Coyhaique	15
327	Lago Verde	15
328	Aysén	15
329	Cisnes	15
330	Guaitecas	15
331	Cochrane	15
332	O'Higgins	15
333	Tortel	15
334	Chile Chico	15
335	Río Ibáñez	15
336	Punta Arenas	16
337	Laguna Blanca	16
338	Río Verde	16
339	San Gregorio	16
340	Cabo de Hornos	16
341	Antártica	16
342	Porvenir	16
343	Primavera	16
344	Timaukel	16
345	Natales	16
346	Torres del Paine	16
\.


--
-- Data for Name: direccion_cliente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.direccion_cliente (id_direccion, tipo, calle, numero, latitud, longitud, validada, id_cliente, id_comuna) FROM stdin;
1	instalacion	Av. Concha y Toro	2450	\N	\N	f	1	115
\.


--
-- Data for Name: estado_documento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estado_documento (id_estado, tipo_documento, codigo, nombre, es_final) FROM stdin;
1	orden_trabajo	liberada	Liberada por calidad	f
2	solicitud	recibida	Recibida	f
3	solicitud	asignada	Asignada	f
4	solicitud	cotizada	Cotizada	f
5	solicitud	desestimada	Desestimada	t
6	cotizacion	borrador	Borrador	f
7	cotizacion	en_aprobacion	En aprobacion	f
8	cotizacion	emitida	Emitida	f
9	cotizacion	aceptada	Aceptada	t
10	cotizacion	rechazada	Rechazada	t
11	cotizacion	vencida	Vencida	t
12	cotizacion	anulada	Anulada	t
13	orden_compra	pendiente	Pendiente	f
14	orden_compra	confirmada	Confirmada	f
15	orden_compra	en_produccion	En produccion	f
16	orden_compra	entregada	Entregada	t
17	orden_compra	anulada	Anulada	t
18	orden_trabajo	planificada	Planificada	f
19	orden_trabajo	en_ejecucion	En ejecucion	f
20	orden_trabajo	en_calidad	En control de calidad	f
21	orden_trabajo	cerrada	Cerrada	t
22	orden_trabajo	anulada	Anulada	t
\.


--
-- Data for Name: solicitud_presupuesto; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitud_presupuesto (creado_en, modificado_en, id_solicitud, numero, cantidad, fecha_deseada, id_cliente, id_direccion, id_ejecutivo, id_estado, id_modelo) FROM stdin;
2026-10-10 23:32:38.094631-03	2026-10-10 23:32:38.094643-03	1	SP-2026-0001	2	2026-12-01	1	\N	\N	4	2
2026-10-10 23:32:38.101388-03	2026-10-10 23:32:38.101397-03	2	SP-2026-0002	1	\N	1	\N	\N	2	3
2026-10-10 23:32:46.201924-03	2026-10-10 23:32:46.201941-03	3	SP-2026-0003	3	2026-12-15	1	\N	2	4	3
\.


--
-- Data for Name: cotizacion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotizacion (creado_en, modificado_en, id_cotizacion, numero, version, valor_uf, fecha_valor_uf, total_uf, descuento_pct, plazo_dias_habiles, fecha_entrega, vence_el, id_cliente, id_ejecutivo, id_estado, id_solicitud) FROM stdin;
2026-10-10 23:32:38.104437-03	2026-10-10 23:32:38.104445-03	1	COT-2026-0001	1	40125.50	2026-09-20	412.6000	0.00	25	2026-10-28	2026-10-20	1	8	8	1
2026-10-10 23:32:38.109692-03	2026-10-10 23:32:38.1097-03	2	COT-2026-0002	1	39980.00	2026-08-05	118.5000	0.00	\N	\N	2026-09-04	1	8	9	1
2026-10-10 23:32:46.272844-03	2026-10-10 23:32:46.272874-03	3	COT-2026-0003	1	41136.24	2026-10-10	904.9920	12.00	30	2026-11-23	2026-11-09	1	2	9	3
\.


--
-- Data for Name: empleado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empleado (activo, id_empleado, rut, nombre, cargo, id_usuario) FROM stdin;
t	1	15432876-9	Juan Soto	Bobinador	5
t	2	16789234-5	Pedro Rojas	Armador	\N
t	3	17234568-9	Maria Diaz	Tecnica de ensayos	\N
\.


--
-- Data for Name: orden_compra; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_compra (creado_en, modificado_en, id_orden_compra, numero, total_uf, anticipo_pct, id_cliente, id_cotizacion, id_estado) FROM stdin;
2026-10-10 23:32:38.113446-03	2026-10-10 23:32:38.113455-03	1	OC-2026-0001	118.5000	50.00	1	2	16
2026-10-10 23:32:46.407665-03	2026-10-10 23:32:46.407673-03	2	OC-2026-0002	904.9920	50.00	1	3	15
\.


--
-- Data for Name: orden_trabajo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_trabajo (creado_en, modificado_en, id_orden_trabajo, numero, cantidad, costo_estimado_uf, costo_real_uf, avance_pct, fecha_inicio, fecha_cierre, id_estado, id_modelo, id_orden_compra) FROM stdin;
2026-10-10 23:32:38.116974-03	2026-10-10 23:32:38.116983-03	1	OT-2026-0001	1	94.8000	53.7130	100.00	2026-09-08	2026-10-10	21	1	1
2026-10-10 23:32:46.444194-03	2026-10-10 23:32:46.444202-03	2	OT-2026-0002	3	450.4500	0.7425	0.00	2026-10-10	\N	19	3	2
\.


--
-- Data for Name: tarea_ot; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarea_ot (id_tarea, nombre, secuencia, horas_estimadas, estado, fecha_estimada, id_empleado, id_orden_trabajo) FROM stdin;
1	Corte y armado de nucleo	1	2.00	terminada	\N	1	1
2	Bobinado de baja tension	2	2.00	terminada	\N	1	1
3	Bobinado de alta tension	3	2.00	terminada	\N	1	1
4	Ensamble y llenado de aceite	4	2.00	terminada	\N	1	1
5	Ensayos de rutina	5	1.00	terminada	\N	2	1
7	Bobinado de baja tension	2	6.00	pendiente	\N	1	2
8	Bobinado de alta tension	3	6.00	pendiente	\N	1	2
9	Ensamble y llenado de aceite	4	6.00	pendiente	\N	2	2
10	Ensayos de rutina	5	3.00	pendiente	\N	3	2
6	Corte y armado de nucleo	1	6.00	en_ejecucion	\N	2	2
\.


--
-- Data for Name: consumo_material; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.consumo_material (id_consumo, cantidad, costo_unitario_uf, planificado, fecha, id_bodega, id_material, id_empleado, id_tarea) FROM stdin;
1	36.0000	0.3500	t	2026-10-10 23:32:44.874454-03	1	2	1	3
2	108.0000	0.0850	t	2026-10-10 23:32:44.911642-03	1	1	1	4
3	90.0000	0.0800	t	2026-10-10 23:32:44.928836-03	1	3	1	4
4	1.0000	12.0000	t	2026-10-10 23:32:44.944419-03	1	6	1	4
5	2.0000	1.1000	t	2026-10-10 23:32:44.960388-03	1	5	1	4
6	2.0000	0.6000	t	2026-10-10 23:32:44.977071-03	1	4	1	4
\.


--
-- Data for Name: contacto_cliente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contacto_cliente (id_contacto, nombre, cargo, email, telefono, principal, id_cliente) FROM stdin;
1	Rodrigo Perez	Jefe de compras	compras@maipo.cl	+56 2 2345 6789	t	1
\.


--
-- Data for Name: protocolo_calidad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.protocolo_calidad (activo, id_protocolo, nombre, version, norma_referencia, id_modelo) FROM stdin;
t	1	Ensayos de rutina	1	IEC 60076-1	1
t	2	Ensayos de rutina	1	IEC 60076-1	2
t	3	Ensayos de rutina	1	IEC 60076-1	3
t	4	Ensayos de rutina	1	IEC 60076-1	4
\.


--
-- Data for Name: control_calidad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.control_calidad (id_control, fecha_hora, estado, observacion, id_inspector, id_orden_trabajo, id_protocolo, aprobado_en, id_aprobado_por) FROM stdin;
1	2026-10-10 23:32:45.051575-03	aprobado		6	1	1	2026-10-10 23:32:45.103631-03	6
\.


--
-- Data for Name: cotizacion_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotizacion_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, id_cotizacion, usuario_id, estado_anterior_id, estado_nuevo_id) FROM stdin;
2026-10-10 23:32:38.106409-03	2026-10-10 23:32:38.106417-03	2026-10-10 23:32:38.106428-03	Cotizacion elaborada.	1	1	8	\N	6
2026-10-10 23:32:38.108034-03	2026-10-10 23:32:38.108042-03	2026-10-10 23:32:38.108053-03	Emitida al cliente.	2	1	8	6	8
2026-10-10 23:32:38.111066-03	2026-10-10 23:32:38.111075-03	2026-10-10 23:32:38.111084-03	Aceptada por el cliente.	3	2	9	\N	9
2026-10-10 23:32:46.276663-03	2026-10-10 23:32:46.276672-03	2026-10-10 23:32:46.276684-03	Elaborada desde la solicitud SP-2026-0003.	4	3	2	\N	6
2026-10-10 23:32:46.302073-03	2026-10-10 23:32:46.302086-03	2026-10-10 23:32:46.302101-03	Descuento de 12.00% enviado a aprobacion.	5	3	2	6	7
2026-10-10 23:32:46.325958-03	2026-10-10 23:32:46.325971-03	2026-10-10 23:32:46.325987-03	Aprobada y emitida al cliente.	6	3	3	7	8
2026-10-10 23:32:46.404295-03	2026-10-10 23:32:46.404306-03	2026-10-10 23:32:46.404314-03	Aceptada por el cliente.	7	3	9	8	9
\.


--
-- Data for Name: cotizacion_linea; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotizacion_linea (id_linea, cantidad, costo_material_uf, costo_hh_uf, margen_pct, precio_uf, id_cotizacion, id_modelo) FROM stdin;
1	2	108.4000	56.7000	25.00	206.3000	1	2
2	1	0.0000	0.0000	25.00	118.5000	2	1
3	3	132.0000	4.5000	25.00	342.8000	3	3
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	clientes	0001_initial	2026-10-10 23:32:30.680423-03
2	seguridad	0001_initial	2026-10-10 23:32:30.735517-03
3	contenttypes	0001_initial	2026-10-10 23:32:30.740084-03
4	admin	0001_initial	2026-10-10 23:32:30.752237-03
5	admin	0002_logentry_remove_auto_add	2026-10-10 23:32:30.756843-03
6	admin	0003_logentry_add_action_flag_choices	2026-10-10 23:32:30.761398-03
7	contenttypes	0002_remove_content_type_name	2026-10-10 23:32:30.776144-03
8	auth	0001_initial	2026-10-10 23:32:30.81723-03
9	auth	0002_alter_permission_name_max_length	2026-10-10 23:32:30.82696-03
10	auth	0003_alter_user_email_max_length	2026-10-10 23:32:30.831301-03
11	auth	0004_alter_user_username_opts	2026-10-10 23:32:30.83494-03
12	auth	0005_alter_user_last_login_null	2026-10-10 23:32:30.838793-03
13	auth	0006_require_contenttypes_0002	2026-10-10 23:32:30.839751-03
14	auth	0007_alter_validators_add_error_messages	2026-10-10 23:32:30.843519-03
15	auth	0008_alter_user_username_max_length	2026-10-10 23:32:30.846979-03
16	auth	0009_alter_user_last_name_max_length	2026-10-10 23:32:30.850372-03
17	auth	0010_alter_group_name_max_length	2026-10-10 23:32:30.85967-03
18	auth	0011_update_proxy_permissions	2026-10-10 23:32:30.868651-03
19	auth	0012_alter_user_first_name_max_length	2026-10-10 23:32:30.873131-03
20	inventario	0001_initial	2026-10-10 23:32:30.899561-03
21	inventario	0002_movimientoinventario	2026-10-10 23:32:30.90646-03
22	catalogo	0001_initial	2026-10-10 23:32:31.038455-03
23	comercial	0001_initial	2026-10-10 23:32:31.433097-03
24	produccion	0001_initial	2026-10-10 23:32:31.752908-03
25	calidad	0001_initial	2026-10-10 23:32:31.795709-03
26	calidad	0002_initial	2026-10-10 23:32:32.065383-03
27	calidad	0003_aprobacion_del_control	2026-10-10 23:32:32.157347-03
28	catalogo	0002_responsable_habitual	2026-10-10 23:32:32.185587-03
29	catalogo	0003_rangos_parametros_tecnicos	2026-10-10 23:32:32.225492-03
30	clientes	0002_regiones_y_comunas	2026-10-10 23:32:32.593112-03
31	configuracion	0001_initial	2026-10-10 23:32:32.67644-03
32	configuracion	0002_parametro_max_unidades	2026-10-10 23:32:32.708372-03
33	inventario	0003_movimientoinventario_consumo_and_more	2026-10-10 23:32:32.854339-03
34	pagos	0001_initial	2026-10-10 23:32:32.934451-03
35	seguridad	0002_bloqueo_temporal	2026-10-10 23:32:32.954586-03
36	sessions	0001_initial	2026-10-10 23:32:32.960795-03
37	token_blacklist	0001_initial	2026-10-10 23:32:33.14978-03
38	token_blacklist	0002_outstandingtoken_jti_hex	2026-10-10 23:32:33.165247-03
39	token_blacklist	0003_auto_20171017_2007	2026-10-10 23:32:33.202395-03
40	token_blacklist	0004_auto_20171017_2013	2026-10-10 23:32:33.22147-03
41	token_blacklist	0005_remove_outstandingtoken_jti	2026-10-10 23:32:33.241052-03
42	token_blacklist	0006_auto_20171017_2113	2026-10-10 23:32:33.261491-03
43	token_blacklist	0007_auto_20171017_2214	2026-10-10 23:32:33.31834-03
44	token_blacklist	0008_migrate_to_bigautofield	2026-10-10 23:32:33.374393-03
45	token_blacklist	0010_fix_migrate_to_bigautofield	2026-10-10 23:32:33.410428-03
46	token_blacklist	0011_linearizes_history	2026-10-10 23:32:33.411774-03
47	token_blacklist	0012_alter_outstandingtoken_user	2026-10-10 23:32:33.445237-03
\.


--
-- Data for Name: documento_cobro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documento_cobro (id_documento_cobro, numero, tipo, monto_uf, valor_uf, monto_clp, estado, vence_el, creado_en, id_orden_compra) FROM stdin;
1	DC-2026-0001	anticipo	59.2500	41136.24	2437322.00	pagado	2026-10-26	2026-10-10 23:32:44.089131-03	1
2	DC-2026-0002	saldo	59.2500	41136.24	2437322.00	pagado	2026-10-26	2026-10-10 23:32:45.150676-03	1
3	DC-2026-0003	anticipo	452.4960	41136.24	18613984.00	pagado	2026-10-26	2026-10-10 23:32:46.414384-03	2
\.


--
-- Data for Name: feriado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.feriado (id_feriado, fecha, nombre, tipo, obtenido_en) FROM stdin;
1	2026-01-01	Año Nuevo	civil	2026-10-10 23:32:44.059585-03
2	2026-04-03	Viernes Santo	religioso	2026-10-10 23:32:44.061031-03
3	2026-04-04	Sábado Santo	religioso	2026-10-10 23:32:44.062319-03
4	2026-05-01	Día Nacional del Trabajo	civil	2026-10-10 23:32:44.063639-03
5	2026-05-21	Día de las Glorias Navales	civil	2026-10-10 23:32:44.064869-03
6	2026-06-21	Día Nacional de los Pueblos Indígenas	civil	2026-10-10 23:32:44.066014-03
7	2026-06-29	San Pedro y San Pablo	religioso	2026-10-10 23:32:44.067133-03
8	2026-07-16	Día de la Virgen del Carmen	religioso	2026-10-10 23:32:44.06826-03
9	2026-08-15	Asunción de la Virgen	religioso	2026-10-10 23:32:44.069409-03
10	2026-09-18	Independencia Nacional	civil	2026-10-10 23:32:44.070543-03
11	2026-09-19	Día de las Glorias del Ejército	civil	2026-10-10 23:32:44.07164-03
12	2026-10-12	Encuentro de Dos Mundos	civil	2026-10-10 23:32:44.072886-03
13	2026-10-31	Día Nacional de las Iglesias Evangélicas y Protestantes	religioso	2026-10-10 23:32:44.074062-03
14	2026-11-01	Día de Todos los Santos	religioso	2026-10-10 23:32:44.075233-03
15	2026-12-08	Inmaculada Concepción	religioso	2026-10-10 23:32:44.076478-03
16	2026-12-25	Navidad	religioso	2026-10-10 23:32:44.077667-03
\.


--
-- Data for Name: indicador_economico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.indicador_economico (id_indicador, codigo, fecha, valor, obtenido_en) FROM stdin;
1	UF	2026-10-10	41136.2400	2026-10-10 23:32:44.053171-03
2	USD	2026-10-09	981.6100	2026-10-10 23:32:44.056034-03
3	UTM	2026-10-01	72151.0000	2026-10-10 23:32:44.057669-03
\.


--
-- Data for Name: log_integracion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.log_integracion (id_log, servicio, endpoint, metodo, codigo_respuesta, latencia_ms, exitoso, mensaje_error, fecha_hora) FROM stdin;
\.


--
-- Data for Name: parametro_tecnico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.parametro_tecnico (id_parametro, codigo, nombre, unidad, tipo_dato, obligatorio, fija_el_modelo, valor_maximo, valor_minimo) FROM stdin;
1	potencia_kva	Potencia nominal	kVA	lista	t	t	\N	\N
2	tension_prim	Tension primaria	kV	numerico	t	f	66.000	1.000
3	tension_sec	Tension secundaria	V	numerico	t	f	1000.000	100.000
4	grupo_conexion	Grupo de conexion		lista	t	f	\N	\N
5	refrigeracion	Refrigeracion		lista	t	f	\N	\N
\.


--
-- Data for Name: modelo_parametro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modelo_parametro (id, valor_defecto, obligatorio, id_modelo, id_parametro) FROM stdin;
1	50	t	1	1
2	15	t	1	2
3	400	t	1	3
4	Dyn11	t	1	4
5	ONAN	t	1	5
6	100	t	2	1
7	15	t	2	2
8	400	t	2	3
9	Dyn11	t	2	4
10	ONAN	t	2	5
11	250	t	3	1
12	23	t	3	2
13	400	t	3	3
14	Dyn11	t	3	4
15	ONAN	t	3	5
16	50	t	4	1
17	15	t	4	2
18	400	t	4	3
19	Yzn11	t	4	4
20	ONAN	t	4	5
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
1	recepcion	2500.0000	0.0850	2026-10-10 23:32:43.453055-03	Stock inicial de demostracion	1	\N	1	\N	8
2	recepcion	900.0000	0.3500	2026-10-10 23:32:43.456976-03	Stock inicial de demostracion	1	\N	2	\N	8
3	recepcion	1800.0000	0.0800	2026-10-10 23:32:43.460091-03	Stock inicial de demostracion	1	\N	3	\N	8
4	recepcion	80.0000	0.6000	2026-10-10 23:32:43.463594-03	Stock inicial de demostracion	1	\N	4	\N	8
5	recepcion	60.0000	1.1000	2026-10-10 23:32:43.466549-03	Stock inicial de demostracion	1	\N	5	\N	8
6	recepcion	10.0000	12.0000	2026-10-10 23:32:43.469787-03	Stock inicial de demostracion	1	\N	6	\N	8
7	consumo	-36.0000	0.3500	2026-10-10 23:32:44.875924-03	OT-2026-0001 / Bobinado de alta tension	1	1	2	\N	4
8	consumo	-108.0000	0.0850	2026-10-10 23:32:44.912263-03	OT-2026-0001 / Ensamble y llenado de aceite	1	2	1	\N	4
9	consumo	-90.0000	0.0800	2026-10-10 23:32:44.929325-03	OT-2026-0001 / Ensamble y llenado de aceite	1	3	3	\N	4
10	consumo	-1.0000	12.0000	2026-10-10 23:32:44.945004-03	OT-2026-0001 / Ensamble y llenado de aceite	1	4	6	\N	4
11	consumo	-2.0000	1.1000	2026-10-10 23:32:44.960951-03	OT-2026-0001 / Ensamble y llenado de aceite	1	5	5	\N	4
12	consumo	-2.0000	0.6000	2026-10-10 23:32:44.977594-03	OT-2026-0001 / Ensamble y llenado de aceite	1	6	4	\N	4
13	recepcion	300.0000	0.3600	2026-10-10 23:32:46.498993-03	Documento Factura 48211	1	\N	2	2	7
\.


--
-- Data for Name: punto_control; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.punto_control (id_punto, nombre, tipo_ensayo, unidad, valor_esperado, tolerancia_inf, tolerancia_sup, obligatorio, secuencia, id_protocolo) FROM stdin;
1	Resistencia de aislamiento AT-BT y a tierra	Rutina	MOhm	\N	1000.0000	\N	t	1	1
2	Relacion de transformacion (desviacion)	Rutina	%	0.0000	-0.5000	0.5000	t	2	1
3	Resistencia de devanados (desbalance entre fases)	Rutina	%	0.0000	\N	2.0000	t	3	1
4	Tension aplicada durante 60 s	Rutina	kV	34.0000	34.0000	\N	t	4	1
5	Corriente de vacio	Rutina	%	\N	\N	2.5000	t	5	1
6	Perdidas en vacio	Rutina	W	\N	\N	190.0000	t	6	1
7	Rigidez dielectrica del aceite	Rutina	kV	\N	30.0000	\N	t	7	1
8	Nivel de ruido	Rutina	dB	\N	\N	60.0000	f	8	1
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
\.


--
-- Data for Name: resultado_control; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.resultado_control (id_resultado, valor_medido, conforme, observacion, registrado_en, id_control, id_punto) FROM stdin;
1	1250.0000	t		2026-10-10 23:32:45.056151-03	1	1
2	0.1800	t		2026-10-10 23:32:45.061437-03	1	2
3	0.9000	t		2026-10-10 23:32:45.065431-03	1	3
4	34.0000	t		2026-10-10 23:32:45.069967-03	1	4
5	2.9000	f		2026-10-10 23:32:45.07362-03	1	5
6	176.0000	t		2026-10-10 23:32:45.080966-03	1	6
7	52.0000	t		2026-10-10 23:32:45.085114-03	1	7
8	55.0000	t		2026-10-10 23:32:45.088948-03	1	8
9	2.1000	t	Ensayo repetido tras la accion correctiva	2026-10-10 23:32:45.09922-03	1	5
\.


--
-- Data for Name: no_conformidad; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.no_conformidad (id_no_conformidad, descripcion, severidad, accion_correctiva, estado, abierta_en, cerrada_en, id_responsable, id_usuario_cierre, id_resultado) FROM stdin;
1	Corriente de vacio sobre el 2,5 % admitido	mayor	Se reajusto el apriete del nucleo y se repitio el ensayo.	cerrada	2026-10-10 23:32:45.074062-03	2026-10-10 23:32:45.092301-03	6	6	5
\.


--
-- Data for Name: orden_compra_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_compra_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, estado_anterior_id, estado_nuevo_id, id_orden_compra, usuario_id) FROM stdin;
2026-10-10 23:32:45.388877-03	2026-10-10 23:32:45.388887-03	2026-10-10 23:32:45.388897-03	Entregado en la direccion de instalacion.	1	15	16	1	2
2026-10-10 23:32:46.409441-03	2026-10-10 23:32:46.409452-03	2026-10-10 23:32:46.409462-03	Generada automaticamente al aceptar la cotizacion COT-2026-0003.	2	\N	13	2	9
2026-10-10 23:32:46.438264-03	2026-10-10 23:32:46.438273-03	2026-10-10 23:32:46.438283-03	Confirmada automaticamente al pagarse el anticipo.	3	13	14	2	9
2026-10-10 23:32:46.449657-03	2026-10-10 23:32:46.449666-03	2026-10-10 23:32:46.449675-03	1 orden(es) de trabajo generada(s).	4	14	15	2	9
\.


--
-- Data for Name: orden_compra_linea; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_compra_linea (id_linea_oc, cantidad, precio_uf, id_cotizacion_linea, id_orden_compra) FROM stdin;
1	1	118.5000	2	1
2	3	342.8000	3	2
\.


--
-- Data for Name: orden_trabajo_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.orden_trabajo_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, estado_anterior_id, estado_nuevo_id, id_orden_trabajo, usuario_id) FROM stdin;
2026-10-10 23:32:38.121479-03	2026-10-10 23:32:38.121488-03	2026-10-10 23:32:38.121497-03	Generada desde la orden de compra OC-2026-0001.	1	\N	18	1	8
2026-10-10 23:32:38.123506-03	2026-10-10 23:32:38.123515-03	2026-10-10 23:32:38.123526-03	Inicio de fabricacion en taller.	2	18	19	1	8
2026-10-10 23:32:45.035089-03	2026-10-10 23:32:45.035101-03	2026-10-10 23:32:45.035111-03	Fabricacion terminada; pasa a control de calidad.	3	19	20	1	4
2026-10-10 23:32:45.106004-03	2026-10-10 23:32:45.106012-03	2026-10-10 23:32:45.10602-03	Control de calidad aprobado: la orden queda lista para el cierre.	4	20	1	1	6
2026-10-10 23:32:45.14089-03	2026-10-10 23:32:45.1409-03	2026-10-10 23:32:45.14091-03	Orden cerrada. Desviacion justificada: Horas de taller registradas en la marcha blanca; el costo real queda bajo el estimado de la cotizacion.	5	1	21	1	4
2026-10-10 23:32:46.448032-03	2026-10-10 23:32:46.448041-03	2026-10-10 23:32:46.448049-03	Generada desde la orden de compra OC-2026-0002.	6	\N	18	2	9
2026-10-10 23:32:46.46557-03	2026-10-10 23:32:46.465578-03	2026-10-10 23:32:46.465587-03	Inicio de fabricacion en taller.	7	18	19	2	4
\.


--
-- Data for Name: parametro_sistema; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.parametro_sistema (id_parametro_sistema, clave, valor, tipo_dato, ambito, descripcion, modificado_en, id_usuario) FROM stdin;
1	web.modo_mantencion	false	booleano	canal_web	Suspende la operacion de la aplicacion web (RF-ADM-01).	2026-10-10 23:32:42.690696-03	8
2	web.mensaje_mantencion	Sitio en mantencion. Volvemos pronto.	texto	canal_web	Aviso mostrado durante la mantencion.	2026-10-10 23:32:42.693156-03	8
3	web.pago_en_linea_habilitado	true	booleano	canal_web	Habilita el pago en linea en la web (RF-ADM-02).	2026-10-10 23:32:42.69497-03	8
4	web.autorregistro_habilitado	true	booleano	canal_web	Permite que nuevos clientes se registren solos (RF-CLI-06).	2026-10-10 23:32:42.696588-03	8
5	comercial.vigencia_cotizacion_dias	30	numerico	comercial	Dias de vigencia de una cotizacion (RN-04).	2026-10-10 23:32:42.698116-03	8
6	comercial.umbral_descuento_pct	10	numerico	comercial	Descuento sobre el cual se exige aprobacion interna (RN-05).	2026-10-10 23:32:42.699476-03	8
7	comercial.anticipo_pct	50	numerico	comercial	Porcentaje de anticipo por defecto (RN-15).	2026-10-10 23:32:42.701291-03	8
8	comercial.margen_defecto_pct	25	numerico	comercial	Margen aplicado por defecto al costo estimado.	2026-10-10 23:32:42.702778-03	8
9	comercial.max_unidades_solicitud	500	numerico	comercial	Maximo de unidades por solicitud de presupuesto y por linea de cotizacion.	2026-10-10 23:32:42.704132-03	8
10	produccion.max_horas_diarias	12	numerico	produccion	Maximo de horas hombre registrables por empleado y dia.	2026-10-10 23:32:42.705654-03	8
11	produccion.umbral_desviacion_costo_pct	15	numerico	produccion	Desviacion sobre la cual se exige justificacion al cerrar (RN-11).	2026-10-10 23:32:42.707069-03	8
12	sistema.intentos_fallidos_max	5	numerico	sistema	Intentos fallidos antes de bloquear la cuenta (RF-SEG-04).	2026-10-10 23:32:42.70852-03	8
13	sistema.minutos_inactividad	30	numerico	sistema	Minutos de inactividad antes de cerrar sesion (RF-SEG-07).	2026-10-10 23:32:42.709932-03	8
14	sistema.minutos_bloqueo	15	numerico	sistema	Minutos de bloqueo temporal tras superar los intentos fallidos (RF-SEG-04).	2026-10-10 23:32:42.711641-03	8
15	produccion.costo_indirecto_pct	10	numerico	produccion	Recargo por costos indirectos sobre materiales y horas hombre (RN-11).	2026-10-10 23:32:42.712909-03	8
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
2026-01-01	\N	1	118.5000	1	8
2026-01-01	\N	2	185.0000	2	8
2026-01-01	\N	3	342.8000	3	8
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
1	2026-10-09	2.00	0.5000	f	1	8	1
2	2026-10-08	2.00	0.5000	f	1	8	2
3	2026-10-07	2.00	0.5000	f	1	4	3
4	2026-10-08	2.00	0.5000	f	1	4	4
5	2026-10-09	1.00	0.4500	f	2	4	5
6	2026-10-10	1.50	0.4500	f	2	4	6
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
1	2026-10-10 23:32:35.193212-03	15	1
2	2026-10-10 23:32:35.194502-03	30	1
3	2026-10-10 23:32:35.195386-03	78	1
4	2026-10-10 23:32:35.19623-03	87	1
5	2026-10-10 23:32:35.197058-03	13	1
6	2026-10-10 23:32:35.197876-03	14	1
7	2026-10-10 23:32:35.198676-03	90	1
8	2026-10-10 23:32:35.19952-03	8	1
9	2026-10-10 23:32:35.200445-03	23	1
10	2026-10-10 23:32:35.201265-03	7	1
11	2026-10-10 23:32:35.202012-03	22	1
12	2026-10-10 23:32:35.202796-03	46	1
13	2026-10-10 23:32:35.20356-03	83	1
14	2026-10-10 23:32:35.204334-03	9	1
15	2026-10-10 23:32:35.205143-03	2	1
16	2026-10-10 23:32:35.205941-03	25	1
17	2026-10-10 23:32:35.206779-03	4	1
18	2026-10-10 23:32:35.20759-03	81	1
19	2026-10-10 23:32:35.20842-03	16	1
20	2026-10-10 23:32:35.209314-03	74	1
21	2026-10-10 23:32:35.210164-03	86	1
22	2026-10-10 23:32:35.21094-03	33	1
23	2026-10-10 23:32:35.211668-03	5	1
24	2026-10-10 23:32:35.212483-03	17	1
25	2026-10-10 23:32:35.213362-03	21	1
26	2026-10-10 23:32:35.214158-03	79	1
27	2026-10-10 23:32:35.214995-03	31	1
28	2026-10-10 23:32:35.215735-03	32	1
29	2026-10-10 23:32:35.216528-03	62	1
30	2026-10-10 23:32:35.21732-03	80	1
31	2026-10-10 23:32:35.218054-03	89	1
32	2026-10-10 23:32:35.218904-03	42	1
33	2026-10-10 23:32:35.219808-03	54	1
34	2026-10-10 23:32:35.220617-03	93	1
35	2026-10-10 23:32:35.221475-03	6	1
36	2026-10-10 23:32:35.222267-03	1	1
37	2026-10-10 23:32:35.22302-03	24	1
38	2026-10-10 23:32:35.223746-03	82	1
39	2026-10-10 23:32:35.224535-03	91	1
40	2026-10-10 23:32:35.225321-03	3	1
41	2026-10-10 23:32:35.226088-03	85	1
42	2026-10-10 23:32:35.226929-03	84	1
43	2026-10-10 23:32:35.227719-03	66	1
44	2026-10-10 23:32:35.228527-03	92	1
45	2026-10-10 23:32:35.229377-03	88	1
46	2026-10-10 23:32:35.230169-03	29	1
47	2026-10-10 23:32:35.231682-03	39	2
48	2026-10-10 23:32:35.23244-03	87	2
49	2026-10-10 23:32:35.233256-03	20	2
50	2026-10-10 23:32:35.234231-03	43	2
51	2026-10-10 23:32:35.235197-03	37	2
52	2026-10-10 23:32:35.236084-03	90	2
53	2026-10-10 23:32:35.236935-03	35	2
54	2026-10-10 23:32:35.237722-03	44	2
55	2026-10-10 23:32:35.238495-03	45	2
56	2026-10-10 23:32:35.239325-03	46	2
57	2026-10-10 23:32:35.240193-03	25	2
58	2026-10-10 23:32:35.241044-03	86	2
59	2026-10-10 23:32:35.241842-03	33	2
60	2026-10-10 23:32:35.242616-03	19	2
61	2026-10-10 23:32:35.243399-03	17	2
62	2026-10-10 23:32:35.24418-03	21	2
63	2026-10-10 23:32:35.244975-03	40	2
64	2026-10-10 23:32:35.245762-03	18	2
65	2026-10-10 23:32:35.246519-03	62	2
66	2026-10-10 23:32:35.247286-03	89	2
67	2026-10-10 23:32:35.248056-03	42	2
68	2026-10-10 23:32:35.248794-03	93	2
69	2026-10-10 23:32:35.249641-03	34	2
70	2026-10-10 23:32:35.250438-03	82	2
71	2026-10-10 23:32:35.251186-03	91	2
72	2026-10-10 23:32:35.251989-03	41	2
73	2026-10-10 23:32:35.252724-03	36	2
74	2026-10-10 23:32:35.253561-03	38	2
75	2026-10-10 23:32:35.254324-03	92	2
76	2026-10-10 23:32:35.25512-03	88	2
77	2026-10-10 23:32:35.255898-03	29	2
78	2026-10-10 23:32:35.25741-03	53	3
79	2026-10-10 23:32:35.258182-03	78	3
80	2026-10-10 23:32:35.258941-03	51	3
81	2026-10-10 23:32:35.25967-03	37	3
82	2026-10-10 23:32:35.260501-03	90	3
83	2026-10-10 23:32:35.261383-03	50	3
84	2026-10-10 23:32:35.262215-03	46	3
85	2026-10-10 23:32:35.262994-03	48	3
86	2026-10-10 23:32:35.263717-03	52	3
87	2026-10-10 23:32:35.264497-03	25	3
88	2026-10-10 23:32:35.265286-03	28	3
89	2026-10-10 23:32:35.266194-03	74	3
90	2026-10-10 23:32:35.266975-03	33	3
91	2026-10-10 23:32:35.267783-03	49	3
92	2026-10-10 23:32:35.268648-03	66	3
93	2026-10-10 23:32:35.269497-03	17	3
94	2026-10-10 23:32:35.270364-03	70	3
95	2026-10-10 23:32:35.271127-03	21	3
96	2026-10-10 23:32:35.271876-03	62	3
97	2026-10-10 23:32:35.27265-03	92	3
98	2026-10-10 23:32:35.273441-03	42	3
99	2026-10-10 23:32:35.274186-03	93	3
100	2026-10-10 23:32:35.274963-03	27	3
101	2026-10-10 23:32:35.275692-03	91	3
102	2026-10-10 23:32:35.276605-03	26	3
103	2026-10-10 23:32:35.277562-03	47	3
104	2026-10-10 23:32:35.278352-03	58	3
105	2026-10-10 23:32:35.279144-03	54	3
106	2026-10-10 23:32:35.280655-03	53	4
107	2026-10-10 23:32:35.281546-03	51	4
108	2026-10-10 23:32:35.282326-03	50	4
109	2026-10-10 23:32:35.283087-03	46	4
110	2026-10-10 23:32:35.283841-03	52	4
111	2026-10-10 23:32:35.285376-03	60	5
112	2026-10-10 23:32:35.28627-03	57	5
113	2026-10-10 23:32:35.287188-03	90	5
114	2026-10-10 23:32:35.288191-03	65	5
115	2026-10-10 23:32:35.28926-03	64	5
116	2026-10-10 23:32:35.290228-03	55	5
117	2026-10-10 23:32:35.291181-03	21	5
118	2026-10-10 23:32:35.292146-03	61	5
119	2026-10-10 23:32:35.293027-03	46	5
120	2026-10-10 23:32:35.29383-03	62	5
121	2026-10-10 23:32:35.294599-03	59	5
122	2026-10-10 23:32:35.295343-03	63	5
123	2026-10-10 23:32:35.296102-03	56	5
124	2026-10-10 23:32:35.296871-03	58	5
125	2026-10-10 23:32:35.297675-03	54	5
126	2026-10-10 23:32:35.299195-03	68	6
127	2026-10-10 23:32:35.300043-03	74	6
128	2026-10-10 23:32:35.300799-03	69	6
129	2026-10-10 23:32:35.301582-03	76	6
130	2026-10-10 23:32:35.302351-03	66	6
131	2026-10-10 23:32:35.303087-03	73	6
132	2026-10-10 23:32:35.303807-03	70	6
133	2026-10-10 23:32:35.304577-03	77	6
134	2026-10-10 23:32:35.30536-03	67	6
135	2026-10-10 23:32:35.306131-03	46	6
136	2026-10-10 23:32:35.306903-03	75	6
137	2026-10-10 23:32:35.307635-03	25	6
138	2026-10-10 23:32:35.30844-03	72	6
139	2026-10-10 23:32:35.309213-03	90	6
140	2026-10-10 23:32:35.309947-03	71	6
\.


--
-- Data for Name: solicitud_especificacion; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitud_especificacion (id, valor, id_parametro, id_solicitud) FROM stdin;
1	100	1	1
2	23	2	1
3	400	3	1
4	Dyn11	4	1
5	ONAN	5	1
6	250	1	2
7	23	2	2
8	250	1	3
9	23	2	3
\.


--
-- Data for Name: solicitud_historial; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitud_historial (creado_en, modificado_en, fecha_hora, observacion, id_historial, estado_anterior_id, estado_nuevo_id, usuario_id, id_solicitud) FROM stdin;
2026-10-10 23:32:38.098685-03	2026-10-10 23:32:38.098696-03	2026-10-10 23:32:38.098706-03	Solicitud recibida desde la aplicacion web.	1	\N	2	9	1
2026-10-10 23:32:46.205743-03	2026-10-10 23:32:46.205755-03	2026-10-10 23:32:46.205766-03	Solicitud recibida desde la aplicacion web.	2	\N	2	9	3
2026-10-10 23:32:46.237014-03	2026-10-10 23:32:46.237027-03	2026-10-10 23:32:46.237037-03	Asignada a comercial.	3	2	3	2	3
2026-10-10 23:32:46.278871-03	2026-10-10 23:32:46.27888-03	2026-10-10 23:32:46.27889-03	Cotizada en COT-2026-0003.	4	3	4	2	3
\.


--
-- Data for Name: tarea_estandar_modelo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarea_estandar_modelo (id_tarea_estandar, nombre, secuencia, horas_estimadas, id_modelo, id_empleado_sugerido) FROM stdin;
1	Corte y armado de nucleo	1	2.00	1	2
2	Bobinado de baja tension	2	2.00	1	1
3	Bobinado de alta tension	3	2.00	1	1
4	Ensamble y llenado de aceite	4	2.00	1	2
5	Ensayos de rutina	5	1.00	1	3
6	Corte y armado de nucleo	1	2.00	2	2
7	Bobinado de baja tension	2	2.00	2	1
8	Bobinado de alta tension	3	2.00	2	1
9	Ensamble y llenado de aceite	4	2.00	2	2
10	Ensayos de rutina	5	1.00	2	3
11	Corte y armado de nucleo	1	2.00	3	2
12	Bobinado de baja tension	2	2.00	3	1
13	Bobinado de alta tension	3	2.00	3	1
14	Ensamble y llenado de aceite	4	2.00	3	2
15	Ensayos de rutina	5	1.00	3	3
16	Corte y armado de nucleo	1	2.00	4	2
17	Bobinado de baja tension	2	2.00	4	1
18	Bobinado de alta tension	3	2.00	4	1
19	Ensamble y llenado de aceite	4	2.00	4	2
20	Ensayos de rutina	5	1.00	4	3
\.


--
-- Data for Name: tarifa_hora_hombre; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarifa_hora_hombre (id_tarifa, valor_hora_uf, vigente_desde, vigente_hasta, id_empleado) FROM stdin;
1	0.5000	2026-01-01	\N	1
2	0.4500	2026-01-01	\N	2
3	0.5500	2026-01-01	\N	3
\.


--
-- Data for Name: transaccion_pago; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transaccion_pago (id_transaccion, id_externo, pasarela, monto, moneda, estado, iniciada_en, resuelta_en, respuesta, id_documento_cobro) FROM stdin;
1	DEMO-SIM-ORDEN-001	paypal	2482.98	USD	aprobada	2026-10-10 23:32:44.101403-03	2026-10-10 23:32:44.104342-03	{"orden": {"id": "DEMO-SIM-ORDEN-001", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "DEMO-SIM-CAPTURA-001", "monto": {"valor": "2482.98", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "2437322.00", "monto_usd": "2482.98", "fecha_dolar": "2026-10-09", "dolar_observado": "981.6100"}, "clave_idempotencia": "109fd02b-4557-4310-b806-3532a4d51869"}	1
2	DEMO-SIM-ORDEN-002	paypal	2482.98	USD	aprobada	2026-10-10 23:32:45.356753-03	2026-10-10 23:32:45.359332-03	{"orden": {"id": "DEMO-SIM-ORDEN-002", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "DEMO-SIM-CAPTURA-002", "monto": {"valor": "2482.98", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "2437322.00", "monto_usd": "2482.98", "fecha_dolar": "2026-10-09", "dolar_observado": "981.6100"}, "clave_idempotencia": "35b71496-ffc1-4ce1-8543-cd8850875997"}	2
3	DEMO-SIM-ORDEN-003	paypal	18962.71	USD	aprobada	2026-10-10 23:32:46.430445-03	2026-10-10 23:32:46.433746-03	{"orden": {"id": "DEMO-SIM-ORDEN-003", "estado": "PAYER_ACTION_REQUIRED"}, "captura": {"id": "DEMO-SIM-CAPTURA-003", "monto": {"valor": "18962.71", "moneda": "USD"}, "estado": "COMPLETED", "motivo": ""}, "conversion": {"monto_clp": "18613984.00", "monto_usd": "18962.71", "fecha_dolar": "2026-10-09", "dolar_observado": "981.6100"}, "clave_idempotencia": "28647b39-febd-44e2-9bb3-50f3e9c12e98"}	3
\.


--
-- Data for Name: usuario_rol; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_rol (id, asignado_en, id_rol, id_usuario) FROM stdin;
1	2026-10-10 23:32:35.541646-03	1	1
2	2026-10-10 23:32:35.765125-03	2	2
3	2026-10-10 23:32:35.982347-03	2	3
4	2026-10-10 23:32:36.206539-03	3	4
5	2026-10-10 23:32:36.42312-03	4	5
6	2026-10-10 23:32:36.644013-03	5	6
7	2026-10-10 23:32:36.859925-03	6	7
\.


--
-- Data for Name: valor_parametro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.valor_parametro (activo, id_valor, valor, orden, id_parametro) FROM stdin;
t	1	50	0	1
t	2	100	1	1
t	3	150	2	1
t	4	250	3	1
t	5	500	4	1
t	6	Dyn11	0	4
t	7	Dyn5	1	4
t	8	Yzn11	2	4
t	9	ONAN	0	5
t	10	ONAF	1	5
\.


--
-- Name: auditoria_id_auditoria_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auditoria_id_auditoria_seq', 6, true);


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

SELECT pg_catalog.setval('public.aviso_sitio_id_aviso_seq', 1, true);


--
-- Name: bodega_id_bodega_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bodega_id_bodega_seq', 1, true);


--
-- Name: bom_modelo_id_bom_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bom_modelo_id_bom_seq', 24, true);


--
-- Name: categoria_material_id_categoria_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.categoria_material_id_categoria_seq', 5, true);


--
-- Name: cliente_id_cliente_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cliente_id_cliente_seq', 1, true);


--
-- Name: comuna_id_comuna_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.comuna_id_comuna_seq', 346, true);


--
-- Name: consumo_material_id_consumo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.consumo_material_id_consumo_seq', 6, true);


--
-- Name: contacto_cliente_id_contacto_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contacto_cliente_id_contacto_seq', 1, true);


--
-- Name: control_calidad_id_control_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.control_calidad_id_control_seq', 1, true);


--
-- Name: cotizacion_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotizacion_historial_id_historial_seq', 7, true);


--
-- Name: cotizacion_id_cotizacion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotizacion_id_cotizacion_seq', 3, true);


--
-- Name: cotizacion_linea_id_linea_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotizacion_linea_id_linea_seq', 3, true);


--
-- Name: direccion_cliente_id_direccion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.direccion_cliente_id_direccion_seq', 1, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 61, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 47, true);


--
-- Name: documento_cobro_id_documento_cobro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documento_cobro_id_documento_cobro_seq', 3, true);


--
-- Name: empleado_id_empleado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.empleado_id_empleado_seq', 3, true);


--
-- Name: estado_documento_id_estado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estado_documento_id_estado_seq', 22, true);


--
-- Name: familia_producto_id_familia_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.familia_producto_id_familia_seq', 2, true);


--
-- Name: feriado_id_feriado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.feriado_id_feriado_seq', 16, true);


--
-- Name: indicador_economico_id_indicador_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.indicador_economico_id_indicador_seq', 3, true);


--
-- Name: log_integracion_id_log_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.log_integracion_id_log_seq', 12, true);


--
-- Name: material_id_material_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.material_id_material_seq', 6, true);


--
-- Name: modelo_parametro_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modelo_parametro_id_seq', 20, true);


--
-- Name: modelo_producto_id_modelo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modelo_producto_id_modelo_seq', 4, true);


--
-- Name: movimiento_inventario_id_movimiento_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.movimiento_inventario_id_movimiento_seq', 13, true);


--
-- Name: no_conformidad_id_no_conformidad_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.no_conformidad_id_no_conformidad_seq', 1, true);


--
-- Name: orden_compra_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_compra_historial_id_historial_seq', 4, true);


--
-- Name: orden_compra_id_orden_compra_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_compra_id_orden_compra_seq', 2, true);


--
-- Name: orden_compra_linea_id_linea_oc_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_compra_linea_id_linea_oc_seq', 2, true);


--
-- Name: orden_trabajo_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_trabajo_historial_id_historial_seq', 7, true);


--
-- Name: orden_trabajo_id_orden_trabajo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.orden_trabajo_id_orden_trabajo_seq', 2, true);


--
-- Name: parametro_sistema_id_parametro_sistema_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.parametro_sistema_id_parametro_sistema_seq', 15, true);


--
-- Name: parametro_tecnico_id_parametro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.parametro_tecnico_id_parametro_seq', 5, true);


--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.permiso_id_permiso_seq', 93, true);


--
-- Name: precio_base_modelo_id_precio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.precio_base_modelo_id_precio_seq', 3, true);


--
-- Name: precio_material_id_precio_material_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.precio_material_id_precio_material_seq', 6, true);


--
-- Name: protocolo_calidad_id_protocolo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.protocolo_calidad_id_protocolo_seq', 4, true);


--
-- Name: proveedor_id_proveedor_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.proveedor_id_proveedor_seq', 2, true);


--
-- Name: punto_control_id_punto_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.punto_control_id_punto_seq', 32, true);


--
-- Name: region_id_region_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.region_id_region_seq', 16, true);


--
-- Name: registro_hora_hombre_id_registro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.registro_hora_hombre_id_registro_seq', 6, true);


--
-- Name: resultado_control_id_resultado_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.resultado_control_id_resultado_seq', 9, true);


--
-- Name: rol_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_id_rol_seq', 6, true);


--
-- Name: rol_permiso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rol_permiso_id_seq', 140, true);


--
-- Name: solicitud_especificacion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_especificacion_id_seq', 9, true);


--
-- Name: solicitud_historial_id_historial_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_historial_id_historial_seq', 4, true);


--
-- Name: solicitud_presupuesto_id_solicitud_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitud_presupuesto_id_solicitud_seq', 3, true);


--
-- Name: tarea_estandar_modelo_id_tarea_estandar_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarea_estandar_modelo_id_tarea_estandar_seq', 20, true);


--
-- Name: tarea_ot_id_tarea_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarea_ot_id_tarea_seq', 10, true);


--
-- Name: tarifa_hora_hombre_id_tarifa_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarifa_hora_hombre_id_tarifa_seq', 3, true);


--
-- Name: transaccion_pago_id_transaccion_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.transaccion_pago_id_transaccion_seq', 3, true);


--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_id_usuario_seq', 9, true);


--
-- Name: usuario_rol_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_rol_id_seq', 7, true);


--
-- Name: valor_parametro_id_valor_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.valor_parametro_id_valor_seq', 10, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 5OSbILiaRgkTemGqSZHjcTJh7QwbZf4Ja3WFuYWYrDV5um5dBShntjp8VRZa9MO

