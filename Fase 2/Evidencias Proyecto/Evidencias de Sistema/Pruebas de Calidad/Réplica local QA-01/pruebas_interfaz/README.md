# Pruebas de interfaz de SITRAFO (Selenium)

Recorren el portal del cliente de extremo a extremo: acceso, catálogo, solicitud
de presupuesto, respuesta a la cotización, orden de compra, documento de cobro,
seguimiento de fabricación, vista móvil y cierre de sesión (16 casos).

## Requisitos

- Python 3.12 o superior y Google Chrome.
- `pip install selenium pytest requests pytest-html`
- El sistema levantado **con una base recién cargada** con los comandos de
  demostración del README (pasos 6 a 11). La prueba 10 acepta la cotización
  `COT-2026-0001` del caso de demostración, así que para repetir la suite hay
  que volver a cargar la base.

> No ejecutar contra el ambiente productivo: las pruebas crean solicitudes y
> aceptan una cotización.

## Ejecución

```powershell
$env:SITRAFO_URL = "http://localhost:8000"
pytest -v --html=reporte_selenium.html --self-contained-html
```

Las capturas de cada paso quedan en `capturas/`. Variables opcionales:
`SITRAFO_CLIENTE`, `SITRAFO_CLAVE`, `HEADLESS=0` (para ver el navegador),
`CHROME_BINARY` y `CHROMEDRIVER`.

Esta carpeta está fuera de `Aplicacion/sitrafo` a propósito: así la integración
continua (que no instala Selenium) no intenta ejecutarlas.
