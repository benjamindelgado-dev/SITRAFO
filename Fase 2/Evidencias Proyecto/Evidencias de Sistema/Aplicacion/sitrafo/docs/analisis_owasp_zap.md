# Analisis de seguridad con OWASP ZAP (RNF-03)

El analisis se ejecuta sobre el sistema levantado (local o desplegado) con la
imagen oficial de ZAP en Docker. No requiere instalar nada mas.

## 1. Analisis pasivo (baseline) del portal web

```powershell
docker run --rm -v "${PWD}:/zap/wrk" ghcr.io/zaproxy/zaproxy:stable `
  zap-baseline.py -t http://host.docker.internal:8000 -r reporte_zap_web.html
```

Contra el sistema desplegado, reemplazar la URL por la publica
(por ejemplo `https://sitrafo.onrender.com`).

## 2. Analisis de la API REST

```powershell
docker run --rm -v "${PWD}:/zap/wrk" ghcr.io/zaproxy/zaproxy:stable `
  zap-api-scan.py -t http://host.docker.internal:8000/api/v1/ -f openapi `
  -r reporte_zap_api.html
```

Si la API no publica un esquema OpenAPI, usar el analisis baseline sobre
`/api/v1/`.

## 3. Criterio de aceptacion

- Sin alertas de riesgo **Alto**.
- Las alertas **Medias** se corrigen o se justifican en el informe.
- Las alertas **Bajas** e **Informativas** se registran.

## 4. Controles ya implementados que ZAP verifica

| Control | Donde |
|---|---|
| Proteccion CSRF en formularios | Middleware de Django |
| Cabeceras anti clickjacking (X-Frame-Options) | `XFrameOptionsMiddleware` |
| Cookies de sesion seguras y HTTPS obligatorio | `config/settings/prod.py` |
| Contrasenas con hash y politica de complejidad | Validadores de Django |
| Bloqueo por intentos fallidos | `apps/seguridad/views.py` |
| Autorizacion por rol y denegacion por defecto | `apps/common/permissions.py` |

Los reportes `reporte_zap_*.html` se adjuntan como evidencia en el informe.
