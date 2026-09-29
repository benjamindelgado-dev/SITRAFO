"""
Prueba de carga (RNF-06, RNF-07).

Simula usuarios concurrentes navegando el portal y la API y reporta tiempos
de respuesta (mediana y percentil 95) y tasa de error. No requiere librerias
adicionales: usa hilos y requests.

Uso (con el sistema levantado):
    python scripts/prueba_carga.py --url http://localhost:8000 --usuarios 30 --peticiones 20

Contra el sistema desplegado:
    python scripts/prueba_carga.py --url https://sitrafo.onrender.com --usuarios 30

El resultado se guarda tambien en reporte_carga.txt como evidencia.
"""
import argparse
import statistics
import threading
import time
from datetime import datetime

import requests

RUTAS_PUBLICAS = ["/acceso/", "/privacidad/"]
RUTAS_CLIENTE = ["/", "/catalogo/", "/mis-cotizaciones/", "/mis-pedidos/"]
RUTAS_API = ["/api/v1/modelos/", "/api/v1/cotizaciones/", "/api/v1/ordenes-compra/"]


def usuario_virtual(base, peticiones, usuario, clave, tiempos, errores, candado):
    sesion = requests.Session()
    token = None
    try:
        r = sesion.post(f"{base}/api/v1/auth/token/",
                        json={"username": usuario, "password": clave}, timeout=30)
        token = r.json().get("access") if r.ok else None
    except requests.RequestException:
        pass
    rutas = RUTAS_PUBLICAS + RUTAS_API
    for i in range(peticiones):
        ruta = rutas[i % len(rutas)]
        cabeceras = {"Authorization": f"Bearer {token}"} if token and "/api/" in ruta else {}
        inicio = time.perf_counter()
        try:
            r = sesion.get(f"{base}{ruta}", headers=cabeceras, timeout=30)
            ok = r.status_code < 500
        except requests.RequestException:
            ok = False
        duracion = time.perf_counter() - inicio
        with candado:
            tiempos.append(duracion)
            if not ok:
                errores.append(ruta)


def main():
    parser = argparse.ArgumentParser(description="Prueba de carga de SITRAFO")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--usuarios", type=int, default=30)
    parser.add_argument("--peticiones", type=int, default=20)
    parser.add_argument("--usuario", default="comercial")
    parser.add_argument("--clave", default="Clave123456")
    parser.add_argument("--umbral", type=float, default=2.0,
                        help="Segundos maximos para el percentil 95")
    args = parser.parse_args()

    tiempos, errores, candado = [], [], threading.Lock()
    hilos = [threading.Thread(target=usuario_virtual, args=(
        args.url.rstrip("/"), args.peticiones, args.usuario, args.clave,
        tiempos, errores, candado)) for _ in range(args.usuarios)]
    inicio = time.perf_counter()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    total = time.perf_counter() - inicio

    tiempos.sort()
    p95 = tiempos[int(len(tiempos) * 0.95) - 1] if tiempos else 0
    lineas = [
        f"Prueba de carga SITRAFO — {datetime.now():%d-%m-%Y %H:%M}",
        f"Destino: {args.url}",
        f"Usuarios concurrentes: {args.usuarios} · peticiones por usuario: {args.peticiones}",
        f"Peticiones totales: {len(tiempos)} en {total:.1f} s "
        f"({len(tiempos) / total:.1f} por segundo)",
        f"Mediana: {statistics.median(tiempos):.3f} s · Percentil 95: {p95:.3f} s · "
        f"Maximo: {tiempos[-1]:.3f} s",
        f"Errores (5xx o sin respuesta): {len(errores)} "
        f"({len(errores) / max(len(tiempos), 1) * 100:.1f} %)",
        f"Resultado: {'CUMPLE' if p95 <= args.umbral and not errores else 'NO CUMPLE'} "
        f"(percentil 95 <= {args.umbral} s y sin errores)",
    ]
    texto = "\n".join(lineas)
    print(texto)
    with open("reporte_carga.txt", "w", encoding="utf-8") as archivo:
        archivo.write(texto + "\n")


if __name__ == "__main__":
    main()
