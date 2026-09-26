"""
Cliente de la API REST de SITRAFO.

Unico punto de acceso a los datos desde la aplicacion de escritorio
(RNF-05). Ninguna otra parte de esta aplicacion debe hablar con la base de
datos ni construir peticiones HTTP por su cuenta.
"""
from __future__ import annotations

import requests


class ErrorAPI(Exception):
    """Error devuelto por la API, con su codigo y su mensaje."""

    def __init__(self, mensaje: str, codigo: int = 0):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class ClienteAPI:
    """Envoltorio de la API REST con autenticacion por token."""

    def __init__(self, url_base: str = "http://localhost:8000/api/v1"):
        self.url_base = url_base.rstrip("/")
        self.sesion = requests.Session()
        self.token: str | None = None
        self.refresh: str | None = None
        self.usuario: str | None = None
        self.identidad: dict = {}

    # -- Autenticacion ------------------------------------------------------
    def autenticar(self, username: str, password: str) -> None:
        respuesta = self.sesion.post(
            f"{self.url_base}/auth/token/",
            json={"username": username, "password": password},
            timeout=10,
        )
        if respuesta.status_code == 401:
            raise ErrorAPI("Usuario o contrasena incorrectos.", 401)
        self._verificar(respuesta)

        datos = respuesta.json()
        self.token = datos["access"]
        self.refresh = datos.get("refresh")
        self.usuario = username
        self.sesion.headers["Authorization"] = f"Bearer {self.token}"

    def cargar_identidad(self) -> dict:
        """Roles y permisos efectivos del usuario (GET /auth/yo/)."""
        self.identidad = self.obtener("auth/yo/")
        return self.identidad

    def puede(self, permiso: str) -> bool:
        """
        Si el rol del usuario autoriza el permiso.

        Solo decide que se muestra en pantalla: la API vuelve a verificar
        cada operacion y rechaza lo no autorizado aunque la interfaz fallara.
        """
        if self.identidad.get("es_superusuario"):
            return True
        return permiso in self.identidad.get("permisos", [])

    @property
    def roles(self) -> list[str]:
        if self.identidad.get("es_superusuario"):
            return ["Superusuario"]
        return self.identidad.get("roles", [])

    def cerrar_sesion(self) -> None:
        self.token = None
        self.refresh = None
        self.usuario = None
        self.identidad = {}
        self.sesion.headers.pop("Authorization", None)

    def renovar_token(self) -> bool:
        """Renueva el token vencido. Devuelve si lo consiguio."""
        if not self.refresh:
            return False
        respuesta = self.sesion.post(
            f"{self.url_base}/auth/token/refresh/",
            json={"refresh": self.refresh},
            timeout=10,
        )
        if not respuesta.ok:
            return False
        self.token = respuesta.json()["access"]
        self.sesion.headers["Authorization"] = f"Bearer {self.token}"
        return True

    # -- Verbos -------------------------------------------------------------
    def obtener(self, ruta: str, params: dict | None = None):
        return self._peticion("GET", ruta, params=params)

    def crear(self, ruta: str, datos: dict):
        return self._peticion("POST", ruta, json=datos)

    def actualizar(self, ruta: str, datos: dict):
        return self._peticion("PATCH", ruta, json=datos)

    def accion(self, ruta: str, datos: dict | None = None):
        return self._peticion("POST", ruta, json=datos or {})

    # -- Interno ------------------------------------------------------------
    def _peticion(self, metodo: str, ruta: str, reintentado: bool = False, **kwargs):
        url = f"{self.url_base}/{ruta.lstrip('/')}"
        try:
            respuesta = self.sesion.request(metodo, url, timeout=15, **kwargs)
        except requests.exceptions.ConnectionError as exc:
            raise ErrorAPI(
                "No se pudo conectar con el servidor. Verifique que el "
                "backend este en ejecucion."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise ErrorAPI("El servidor no respondio a tiempo.") from exc

        # Token vencido: se renueva una vez y se reintenta
        if respuesta.status_code == 401 and not reintentado and self.renovar_token():
            return self._peticion(metodo, ruta, reintentado=True, **kwargs)

        self._verificar(respuesta)
        if respuesta.status_code == 204 or not respuesta.content:
            return None
        return respuesta.json()

    @staticmethod
    def _verificar(respuesta) -> None:
        if respuesta.ok:
            return

        try:
            cuerpo = respuesta.json()
        except ValueError:
            raise ErrorAPI(
                f"Error {respuesta.status_code} del servidor.",
                respuesta.status_code,
            ) from None

        if isinstance(cuerpo, dict):
            mensaje = cuerpo.get("detalle") or cuerpo.get("detail")
            if not mensaje:
                partes = []
                for campo, errores in cuerpo.items():
                    texto = errores if isinstance(errores, str) else ", ".join(map(str, errores))
                    partes.append(f"{campo}: {texto}")
                mensaje = " | ".join(partes)
        else:
            mensaje = str(cuerpo)

        raise ErrorAPI(mensaje or "Error desconocido.", respuesta.status_code)

    # -- Atajos por dominio -------------------------------------------------
    def modelos(self, params=None):
        return self.obtener("modelos/", params)

    def modelo(self, id_modelo: int):
        return self.obtener(f"modelos/{id_modelo}/")

    def crear_modelo(self, datos: dict):
        return self.crear("modelos/", datos)

    def actualizar_modelo(self, id_modelo: int, datos: dict):
        return self.actualizar(f"modelos/{id_modelo}/", datos)

    def familias(self):
        respuesta = self.obtener("familias/", {"page_size": 200})
        return respuesta.get("results", respuesta)

    def crear_familia(self, nombre: str):
        return self.crear("familias/", {"nombre": nombre})

    def parametros_tecnicos(self):
        respuesta = self.obtener("parametros-tecnicos/", {"page_size": 200})
        return respuesta.get("results", respuesta)

    def alternar_publicacion(self, id_modelo: int):
        return self.accion(f"modelos/{id_modelo}/publicar/")

    def clientes(self, params=None):
        return self.obtener("clientes/", params)

    def solicitudes(self, params=None):
        return self.obtener("solicitudes/", params)

    def asignar_solicitud(self, id_solicitud: int):
        return self.accion(f"solicitudes/{id_solicitud}/asignar/")

    def costeo_solicitud(self, id_solicitud: int, margen=None):
        params = {"margen": margen} if margen is not None else None
        return self.obtener(f"solicitudes/{id_solicitud}/costeo/", params)

    def cotizar_solicitud(self, id_solicitud: int, datos: dict):
        return self.accion(f"solicitudes/{id_solicitud}/cotizar/", datos)

    def cotizaciones(self, params=None):
        return self.obtener("cotizaciones/", params)

    def devolver_cotizacion(self, id_cotizacion: int, motivo: str):
        return self.accion(f"cotizaciones/{id_cotizacion}/devolver/", {"motivo": motivo})

    def emitir_cotizacion(self, id_cotizacion: int):
        return self.accion(f"cotizaciones/{id_cotizacion}/emitir/")

    def solicitar_aprobacion(self, id_cotizacion: int):
        return self.accion(f"cotizaciones/{id_cotizacion}/solicitar_aprobacion/")

    def enviar_cotizacion(self, id_cotizacion: int):
        return self.accion(f"cotizaciones/{id_cotizacion}/enviar_correo/")

    def generar_orden_compra(self, id_cotizacion: int):
        return self.accion(f"cotizaciones/{id_cotizacion}/generar_orden_compra/")

    def ordenes_compra(self, params=None):
        return self.obtener("ordenes-compra/", params)

    def confirmar_orden_compra(self, id_orden: int):
        return self.accion(f"ordenes-compra/{id_orden}/confirmar/")

    def generar_ordenes_trabajo(self, id_orden_compra: int):
        return self.accion(f"ordenes-compra/{id_orden_compra}/generar_ordenes_trabajo/")

    # -- Produccion -------------------------------------------------------
    def ordenes_trabajo(self, params=None):
        return self.obtener("ordenes-trabajo/", params)

    def orden_trabajo(self, id_ot: int):
        return self.obtener(f"ordenes-trabajo/{id_ot}/")

    def iniciar_ot(self, id_ot: int):
        return self.accion(f"ordenes-trabajo/{id_ot}/iniciar/")

    def enviar_ot_a_calidad(self, id_ot: int):
        return self.accion(f"ordenes-trabajo/{id_ot}/enviar_calidad/")

    def cerrar_ot(self, id_ot: int, justificacion: str = ""):
        return self.accion(f"ordenes-trabajo/{id_ot}/cerrar/",
                           {"justificacion": justificacion})

    def tareas(self, params=None):
        return self.obtener("tareas/", params)

    def asignar_tarea(self, id_tarea: int, id_empleado: int):
        return self.accion(f"tareas/{id_tarea}/asignar/", {"empleado": id_empleado})

    def registrar_horas(self, id_tarea: int, horas, empleado=None, fecha=None):
        datos = {"horas": str(horas)}
        if empleado:
            datos["empleado"] = empleado
        if fecha:
            datos["fecha"] = fecha
        return self.accion(f"tareas/{id_tarea}/registrar_horas/", datos)

    def registrar_consumo(self, id_tarea: int, material: int, bodega: int, cantidad,
                          empleado=None):
        datos = {"material": material, "bodega": bodega, "cantidad": str(cantidad)}
        if empleado:
            datos["empleado"] = empleado
        return self.accion(f"tareas/{id_tarea}/registrar_consumo/", datos)

    def anular_horas(self, id_tarea: int, id_registro: int, motivo: str):
        return self.accion(f"tareas/{id_tarea}/anular_horas/",
                           {"registro": id_registro, "motivo": motivo})

    def terminar_tarea(self, id_tarea: int):
        return self.accion(f"tareas/{id_tarea}/terminar/")

    def empleados(self):
        return self.obtener("empleados/")

    # -- Calidad ---------------------------------------------------------------
    def protocolos(self, params=None):
        return self.obtener("protocolos/", params)

    def crear_protocolo(self, datos: dict):
        return self.crear("protocolos/", datos)

    def actualizar_protocolo(self, id_protocolo: int, datos: dict):
        return self._peticion("PUT", f"protocolos/{id_protocolo}/", json=datos)

    def controles_calidad(self, params=None):
        return self.obtener("controles-calidad/", params)

    def iniciar_control(self, id_ot: int, id_protocolo: int):
        return self.crear("controles-calidad/", {"orden_trabajo": id_ot,
                                                 "protocolo": id_protocolo})

    def registrar_resultado(self, id_control: int, datos: dict):
        return self.accion(f"controles-calidad/{id_control}/registrar_resultado/", datos)

    def no_conformidades(self, params=None):
        return self.obtener("no-conformidades/", params)

    def cerrar_no_conformidad(self, id_nc: int, accion: str):
        return self.accion(f"no-conformidades/{id_nc}/cerrar/",
                           {"accion_correctiva": accion})

    # -- Usuarios y roles --------------------------------------------------
    def usuarios(self):
        return self.obtener("usuarios/")

    def roles_disponibles(self):
        return self.obtener("roles/")

    def crear_usuario(self, datos: dict):
        return self.crear("usuarios/", datos)

    def actualizar_usuario(self, id_usuario: int, datos: dict):
        return self.actualizar(f"usuarios/{id_usuario}/", datos)

    def suspender_usuario(self, id_usuario: int):
        return self.accion(f"usuarios/{id_usuario}/suspender/")

    def reactivar_usuario(self, id_usuario: int):
        return self.accion(f"usuarios/{id_usuario}/reactivar/")

    def restablecer_clave(self, id_usuario: int):
        return self.accion(f"usuarios/{id_usuario}/restablecer_clave/")

    def materiales(self):
        return self.obtener("materiales/")

    def bodegas(self):
        return self.obtener("bodegas/")

    def parametros(self, ambito: str | None = None):
        params = {"ambito": ambito} if ambito else None
        return self.obtener("parametros/", params)

    def alternar_parametro(self, clave: str):
        return self.accion(f"parametros/{clave}/alternar/")

    def actualizar_parametro(self, clave: str, valor: str):
        return self.actualizar(f"parametros/{clave}/", {"valor": valor})

    def log_integraciones(self, params=None):
        return self.obtener("log-integraciones/", params)
