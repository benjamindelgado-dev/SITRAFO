# SITRAFO - Sistema Integral de Gestión Comercial y Productiva para Transformadores Eléctricos

## 📝 Descripción
SITRAFO es un sistema integral diseñado para solucionar la desconexión existente en la cadena comercial-productiva de las pequeñas y medianas empresas fabricantes de transformadores eléctricos. 

Actualmente, estas empresas gestionan sus cotizaciones en planillas, las órdenes de compra por correo y el avance de fabricación en papel, lo que genera falta de trazabilidad, costeo impreciso y nula visibilidad para el cliente. SITRAFO resuelve este problema conectando todo el flujo: desde el catálogo de productos y la solicitud de presupuesto, pasando por la cotización, orden de compra y orden de trabajo (con captura de materiales y horas hombre), hasta el control de calidad y el pago en línea.

**¿A quién va dirigido?**
A pymes manufactureras chilenas del rubro eléctrico, impactando positivamente a sus áreas comerciales, de producción y a sus clientes finales, quienes ahora tendrán visibilidad completa del estado de sus pedidos.

## 🛠️ Tecnologías utilizadas
*   **Backend & API:** Python, Django, Django REST Framework (DRF)
*   **Base de Datos:** PostgreSQL
*   **Aplicación Web (Cliente):** HTML5, Bootstrap 5, htmx
*   **Aplicación de Escritorio (Administración):** Python, PySide6
*   **Infraestructura & DevOps:** Git, GitHub, Docker, GitHub Actions, Despliegue en Render/Cloud Run
*   **Pruebas & Seguridad:** pytest-django, Selenium, OWASP ZAP
*   **Integraciones Externas (APIs):** PayPal Sandbox, mindicador.cl, Feriados de Chile, Correo transaccional, Geocodificación.

## 🚀 Instrucciones para ejecutar localmente
*(Nota: Estas instrucciones se detallarán durante el Sprint 0 una vez configurado el entorno Docker)*
1. Clonar el repositorio: `git clone https://github.com/benjamindelgado-dev/SITRAFO.git`
2. Navegar a la carpeta del proyecto.
3. Levantar los contenedores: `docker-compose up -d`
4. Aplicar las migraciones de la base de datos.
5. El sistema web estará disponible en `http://localhost:8000` y la API en `http://localhost:8000/api/`.

## 👥 Integrantes del equipo y roles
*   **Benjamín Delgado:** Líder de Proyecto y Product Owner. Responsable de la arquitectura, el núcleo del backend, seguridad, roles, auditoría, integraciones externas y la aplicación de escritorio.
*   **Camila Olivares:** Scrum Master. Responsable del proceso comercial y de la interfaz web orientada al cliente.
*   **Milko Soto:** Desarrollador y Responsable de Calidad. A cargo del proceso productivo, el inventario, los controles de calidad, el entorno Docker y pipeline CI/CD.

## ⚙️ Metodología de trabajo
El proyecto se desarrolla bajo el marco de trabajo **Scrum**, aplicado desde la Fase 1 hasta la Fase 3 del ramo Capstone (18 semanas). 
*   **Gestión:** Trabajo organizado por Sprints con un Product Backlog priorizado, Sprint Backlog y un Tablero Kanban.
*   **Desarrollo:** El reparto de tareas se organiza por módulos verticales (modelo, API, interfaz y pruebas) para asegurar la contribución individual demostrable de cada integrante.
*   **Trazabilidad:** Cada commit en este repositorio estará referenciado a las historias de usuario correspondientes.

## 🏗️ Arquitectura de la solución
SITRAFO utiliza una arquitectura de **tres componentes sobre un backend común**:
1.  **API REST (Núcleo):** Construida con Django REST Framework sobre PostgreSQL. Es el único punto de acceso y manipulación de datos, garantizando la seguridad y centralización de la lógica de negocio.
2.  **Aplicación Web:** Servida por Django (con plantillas HTML, Bootstrap y htmx), orientada a los clientes para la solicitud de presupuestos y seguimiento.
3.  **Aplicación de Escritorio:** Desarrollada en PySide6, orientada a la administración interna. **Regla de negocio estricta:** La app de escritorio administra el sistema consumiendo exclusivamente la API REST, sin conexión directa a la base de datos.
