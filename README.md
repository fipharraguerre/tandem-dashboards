### ✅ `README.md`

# Flask Veeam Dashboard

Aplicación web escrita en Flask para visualizar el estado de backups y otras métricas de Veeam, basada en datos de una base MariaDB.

## 📦 Estructura del Proyecto

```
├── app.py                # main / blueprints
├── .env                  # envvars (.gitignore)
├── routes/               # rutas por funcionalidad
│   ├── **init**.py
│   ├── index.py
│   ├── admin.py
│   ├── status.py
│   └── unsuccessful.py
├── auth.py               # lógica de autenticación y login
├── core.py               # lógica de las tarjetas de estado de clientes
├── db.py                 # conexión a la base
├── logger.py             # logs
├── templates/            # HTMLs
└── static/               # archivos estáticos

```

---

## 🔐 Variables de Entorno

Se cargan desde `.env` en desarrollo, o directamente como environment variables en producción (Docker, Azure, etc).

Ejemplo de `.env`:

```

DB\_USER=facundo
DB\_PASSWORD=miPassword
DB\_HOST=vps-tandem.facundoitest.space
DB\_NAME=VeeamReports
FLASK\_SECRET\_KEY=clave-muy-secreta

````

---

## 📈 Diagrama de componentes (Mermaid)

```mermaid
graph TD
    A[app.py] -->|Registra| B[routes/]
    B --> B1[index.py]
    B --> B2[admin.py]
    B --> B3[status.py]
    B --> B4[unsuccessful.py]
    B --> B5[__init__.py]

    A --> C[.env]
    A --> D[auth.py]
    A --> E[core.py]
    A --> F[db.py]
    A --> G[logger.py]

    subgraph "routes/"
        B1 --> R1["/"]
        B2 --> R2["/admin"]
        B2 --> R3["/admin/add_client"]
        B2 --> R4["/admin/delete_client"]
        B3 --> R5["/status/<client_name>"]
        B4 --> R6["/unsuccessful_tasks"]
    end

    subgraph helpers/
        D
        E
        F
        G
    end

    style A fill:#f9f,stroke:#333,stroke-width:1px
    style B fill:#bbf,stroke:#333,stroke-width:1px
    style C fill:#eee,stroke:#aaa,stroke-dasharray: 5 5
    style D,E,F,G fill:#cfc,stroke:#333,stroke-width:1px
````

---

## Descripción de la aplicación `core.py`

Este dashboard web proporciona una vista centralizada del estado de los backups de todos los clientes de TandemStudio. La aplicación monitorea automáticamente los trabajos de backup desde múltiples fuentes (servidores Veeam y Azure Recovery Vault) y presenta el estado de cada cliente en tarjetas codificadas por colores.

## Cómo funciona

### Flujo de la aplicación

1. **Solicitud del navegador**: Cuando un usuario accede al dashboard desde el navegador, la aplicación web ejecuta la función principal de actualización.

2. **Procesamiento de datos (`update_client_status()`)**: 
   - Se conecta a la base de datos y obtiene la lista completa de clientes
   - Para cada cliente, identifica todos los hostnames asociados (servidores/servicios de backup)
   - Cada hostname en la base de datos representa:
     - Un servidor Veeam
     - Un RecoveryVault de Azure
     - Otro servicio de backup configurado

3. **Análisis por cliente**:
   - **Trabajos de Backup**: Cuenta los trabajos exitosos, con advertencias y fallidos en las últimas 24 horas
   - **Trabajos de Tiering/Offload**: Analiza los procesos de migración de datos a almacenamiento secundario
   - **Backup de Configuración**: Verifica el estado del último backup de configuración de Veeam
   - **Última actividad**: Registra el timestamp más reciente de cualquier actividad

4. **Determinación del estado**:
   - 🔴 **Rojo (Fail)**: Si hay trabajos de backup fallidos
   - 🟡 **Amarillo (Warning)**: Si hay advertencias en backups o fallos en offloads
   - 🟢 **Verde (OK)**: Si todos los trabajos fueron exitosos

5. **Actualización de la base de datos**: Guarda el estado calculado y los mensajes de resumen para cada cliente.

6. **Presentación web**: Muestra una tarjeta por cada cliente con:
   - Estado visual (color de la tarjeta)
   - Resumen de trabajos de backup
   - Estado de trabajos de tiering
   - Última actividad registrada
   - Estado del backup de configuración

### Estructura de datos

- **Tabla `clientes`**: Contiene la información básica de cada cliente y su estado actual
- **Tabla `client_hosts`**: Relaciona cada cliente con sus hostnames/servicios
- **Tablas dinámicas**: Una tabla por cada hostname que almacena el historial de trabajos de backup

### Características adicionales

- **Monitoreo en tiempo real**: Detección automática de servicios inactivos (más de 24 horas sin actividad)
- **Navegación detallada**: Cada tarjeta es clickeable para ver detalles específicos del cliente
- **Alertas visuales**: Indicadores de advertencia para servicios que no han reportado actividad reciente
- **Zona horaria local**: Conversión automática de timestamps a GMT-3 (Argentina)

## Tecnologías utilizadas

- **Backend**: Python con Flask
- **Base de datos**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Monitoreo**: Integración con Veeam Backup & Replication y Azure Recovery Services

---

## 🐳 Contenerización (a futuro)

El proyecto está preparado para correr en contenedores (Docker, Azure Container Instances, etc.), leyendo configuración desde variables de entorno externas.
