# ms-job

## Descripción del Proyecto

**ms-job** es un servicio encargado de gestionar las ofertas de empleo scrapeadas desde diversas plataformas. Este microservicio se integra con bases de datos SQL para almacenar, consultar y actualizar información, y utiliza Kafka para recibir y publicar eventos relacionados con ofertas de trabajo.

## Funcionalidades Principales

- **Gestión de Ofertas de Empleo**:
  - Creación, actualización y eliminación de ofertas.
  - Almacenamiento eficiente de los datos procesados en una base de datos PostgreSQL.

- **Integración con Kafka**:
  - Escucha eventos de creación y actualización de ofertas de empleo desde otros servicios.
  - Publicación de eventos para mantener sincronizados otros componentes del sistema.

- **API RESTful**:
  - Endpoints para interactuar con las ofertas de empleo.
  - Soporte para operaciones CRUD y búsqueda.

- **Validación de Datos**:
  - Uso de modelos Pydantic para garantizar la calidad de los datos.

## Arquitectura

- **Base de Datos**:
  - Uso de SQLAlchemy para la interacción con PostgreSQL.
  - Modelo de datos normalizado definido en `job_offer.py`.

- **Mensajería**:
  - Kafka se utiliza como principal sistema de mensajería para eventos.

- **Capas de Servicio**:
  - `JobCRUD` para la lógica de acceso a datos.
  - `JobSyncService` para la sincronización de ofertas y el procesamiento de eventos.

## Configuración

### Variables de Entorno

El proyecto requiere las siguientes variables de entorno, configuradas en un archivo `.env`:

- `DB_HOST`: Host de la base de datos.
- `DB_PORT`: Puerto de la base de datos.
- `DB_NAME`: Nombre de la base de datos.
- `DB_USER`: Usuario de la base de datos.
- `DB_PASSWORD`: Contraseña de la base de datos.
- `KAFKA_BOOTSTRAP_SERVERS`: Dirección del servidor Kafka.
- Otras variables específicas definidas en `settings.py`.

### Instalación

1. Clona este repositorio:
   ```bash
   git clone <repositorio>
   cd ms-job
