# SITRAFO — Aplicacion de escritorio

Aplicacion de administracion interna, construida con Python y PySide6.

## Regla de arquitectura

Esta aplicacion **nunca accede directamente a la base de datos**. Toda lectura
y escritura se realiza a traves de la API REST, igual que la aplicacion web
(RNF-05). No existe ninguna dependencia de Django ni de psycopg en este
directorio: la unica forma de llegar a los datos es `cliente_api.py`.

## Requisitos

- Python 3.12 o superior instalado en el equipo (no en Docker: es una
  interfaz grafica).
- El backend corriendo en `http://localhost:8000`.

## Instalacion

```bash
cd escritorio
python -m venv .venv
```

### Windows

PowerShell bloquea por defecto la ejecucion de scripts, por lo que el comando
`activate` puede fallar. La forma mas simple de evitarlo es invocar
directamente el interprete del entorno virtual, sin activarlo:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Si se prefiere activar el entorno, primero hay que habilitar los scripts para
el usuario actual (no requiere privilegios de administrador):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\activate
```

### Linux o macOS

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Compatibilidad

PySide6 requiere version 6.10.1 o superior para funcionar con Python 3.14.
El archivo `requirements.txt` declara un rango y no una version fija, de modo
que la instalacion funcione en equipos con distintas versiones de Python.

## Ejecucion

```bash
python main.py
```

Si el backend corre en otra direccion:

```bash
python main.py --api http://192.168.1.10:8000/api/v1
```

## Acceso

Se ingresa con una cuenta interna del sistema, la misma que se usa en el
panel de administracion. Las cuentas web de cliente no pueden ingresar aqui:
la API responde 403 a las operaciones internas.

## Modulos

| Modulo | Funcion | Requerimiento |
|---|---|---|
| Catalogo | Publicar y retirar modelos del catalogo web | RF-ADM-06 |
| Clientes | Consulta de clientes y sus documentos | RF-CLI-01 |
| Solicitudes | Bandeja de solicitudes y asignacion | RF-COM-02 |
| Canal web | Modo mantencion, pago en linea, avisos | RF-ADM-01 a RF-ADM-05 |
| Integraciones | Log de llamadas a servicios externos | RF-INT-01 |
