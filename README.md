# SITRAFO

**Sistema Integral de Gestión Comercial y Productiva para Fabricación de Transformadores Eléctricos**

Proyecto Capstone (APT122 · PTY4614) de Ingeniería en Informática, Duoc UC Sede Puente Alto.

- Sistema publicado: https://sitrafo.onrender.com
- Documentación de la API pública (Swagger): https://sitrafo.onrender.com/api/publica/v1/docs/

## Descripción

Las pymes chilenas que fabrican transformadores eléctricos a pedido cotizan en planillas, reciben las órdenes de compra por correo y siguen la fabricación en papel. Eso se traduce en falta de trazabilidad, costeo impreciso y clientes que no saben en qué estado está su pedido.

SITRAFO conecta todo el ciclo en un solo flujo trazable:

1. El cliente solicita un presupuesto con la especificación técnica del transformador.
2. El área comercial cotiza con el costo calculado desde la receta del modelo y la UF del día.
3. El cliente acepta en el portal: la orden de compra se genera sola.
4. El cliente paga el anticipo con PayPal: la orden se confirma y se generan las órdenes de trabajo.
5. El taller registra horas y materiales; el sistema compara el costo real con el estimado.
6. Calidad ejecuta los ensayos del protocolo y aprueba la orden para que se pueda cerrar.
7. Se cobra el saldo y se registra la entrega.

## Arquitectura

Tres componentes sobre un backend común:

| Componente | Tecnología | Para quién |
|---|---|---|
| API REST | Django, Django REST Framework, PostgreSQL | Único punto de acceso a los datos |
| Aplicación web | Django, Bootstrap 5, htmx | Clientes |
| Aplicación de escritorio | PySide6 (SITRAFO.exe) | Personal interno, por rol |

**Regla de arquitectura:** la aplicación de escritorio nunca accede directo a la base de datos; toda operación pasa por la API REST autenticada, igual que la web.

### APIs

| Tipo | API | Uso |
|---|---|---|
| Propia | Seguimiento de pedidos | Estado, avance y fecha estimada de entrega, también sin iniciar sesión |
| Propia | Cotizador | Precio referencial de uno o más modelos, con plazo de entrega |
| Propia | Disponibilidad de materiales | Materiales bajo el stock mínimo para proveedores autorizados |
| Externa | PayPal (Sandbox) | Pago del anticipo y del saldo |
| Externa | mindicador.cl | UF y dólar del día |
| Externa | Nager.Date | Feriados de Chile para los plazos en días hábiles |
| Externa | Brevo | Correo transaccional (cotizaciones, cobros y avisos) |
| Externa | Nominatim (OpenStreetMap) | Validación de direcciones |

Las APIs propias se consumen con una clave en el encabezado `X-API-Key`, cada clave tiene solo los servicios que se le asignan y un límite de consultas por minuto, y cada consulta queda registrada. El detalle está en el manual técnico TEC-01, sección 10.

## Estructura del repositorio

```
Fase 1/   Definición del proyecto (evidencias individuales y grupales)
Fase 2/
  Evidencias Individuales/   Diarios de reflexión
  Evidencias Grupales/       Guías 2.4 y 2.6
  Evidencias Proyecto/
    Evidencias de documentación/
      1. Inicio del proyecto/         Acta de constitución, ERS-01, visión del producto VIS-01
      2. Metodología Scrum/           MET-01, backlogs, burndown, historias, actas y dailies
      3. Análisis y diseño/           CU-01, MER-01, ARQ-01, SEC-01, MOC-01 y diagramas
      4. Evidencias de funcionamiento/ EVI-01 y capturas
      5. Manual de usuario/           MAN-01
      6. Manual técnico/              TEC-01
    Evidencias de Sistema/
      Aplicacion/sitrafo/   Código de la aplicación (API, web y escritorio)
      Base de Datos/        Esquema, datos de demostración y diccionario de datos
      Pruebas de Calidad/   Plan de pruebas PPR-01, informes PRU-01 y QA-01 y sus evidencias
Fase 3/   Cierre y defensa
render.yaml   Despliegue en Render (web, tareas diarias y base de datos)
```

## Cómo ejecutarlo en local

Requisitos: Git y Docker Desktop.

```powershell
git clone https://github.com/benjamindelgado-dev/SITRAFO.git
cd "SITRAFO\Fase 2\Evidencias Proyecto\Evidencias de Sistema\Aplicacion\sitrafo"
copy .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py cargar_estados
docker compose exec web python manage.py cargar_parametros
docker compose exec web python manage.py cargar_roles --usuarios-demo
docker compose exec web python manage.py cargar_demo
docker compose exec web python manage.py cargar_demo_produccion
```

La web queda en http://localhost:8000 y la API pública en http://localhost:8000/api/publica/v1/docs/. La aplicación de escritorio, la configuración completa y el despliegue en Render están en el manual técnico TEC-01 y en el [README de la aplicación](Fase%202/Evidencias%20Proyecto/Evidencias%20de%20Sistema/Aplicacion/sitrafo/README.md).

## Pruebas

- 291 pruebas automatizadas (pytest), 55 de ellas de las APIs propias, con 93 % de cobertura.
- GitHub Actions ejecuta ruff, la revisión de migraciones y las pruebas en cada cambio; Render publica una versión solo si la integración continua termina en verde.
- Seguridad con OWASP ZAP, prueba de carga y pruebas de interfaz con Selenium: informes PRU-01 (producción) y QA-01 (réplica local).

```powershell
docker compose exec web pytest
```

## Metodología

Scrum, en cuatro sprints:

| Sprint | Período | Objetivo |
|---|---|---|
| 0 | Fase 1 | Análisis, arquitectura, backlog y preparación técnica |
| 1 | 14 al 26 de septiembre | Las 14 historias del sistema |
| 2 | 29 de septiembre al 15 de octubre | Despliegue, documentación y pruebas de calidad |
| 3 | 16 al 31 de octubre | APIs propias, verificación y cierre de la Fase 2 |

Los artefactos (Product Backlog, Sprint Backlog, Burndown, actas y registro de dailies) están en `Fase 2/Evidencias Proyecto/Evidencias de documentación/2. Metodología Scrum`.

## Equipo

| Integrante | Rol |
|---|---|
| Benjamín Delgado Bravo | Líder de Proyecto · Product Owner |
| Camila Olivares | Scrum Master |
| Milko Soto | Desarrollador · Responsable de Calidad del Producto |
