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

---  

# Funcionamiento del Dashboard Principal (index.html)

## Flujo de Datos

El dashboard principal funciona mediante un proceso de varios pasos que actualiza y muestra el estado de todos los clientes de backup:

### 1. Actualización de Estados (`core.py`)

Cuando un usuario accede a la página principal (`/`), se ejecuta automáticamente la función `update_client_status()` que:

- **Obtiene la lista de clientes**: Consulta la tabla `clientes` para obtener todos los nombres de clientes registrados.
- **Busca hostnames asociados**: Para cada cliente, consulta la tabla `client_hosts` para obtener todos los servidores/hostnames que pertenecen a ese cliente.
- **Procesa datos por hostname**: Para cada hostname del cliente, ejecuta consultas SQL en las tablas individuales (ej: `VB0003`, `VB0004`, etc.) para contar:
  - **Backups**: Jobs con `type LIKE '%Backup%'`
  - **Replicaciones**: Jobs con `vmname LIKE '%Repl%'`  
  - **Tiering**: Jobs con `type = 'TieringJob'`
  - **Config Backup**: Último estado de `type = 'VeeamConfigurationBackup'`

### 2. Determinación del Estado General

El sistema evalúa el estado del cliente basándose en una jerarquía de prioridades:

1. Si hay **fallos en backups** → Estado: `fail` (tarjeta roja)
2. Si hay **fallos en replicaciones o tiering** (pero backups OK) → Estado: `warn` (tarjeta amarilla)  
3. Si hay **warnings** en cualquier categoría → Estado: `warn` (tarjeta amarilla)
4. Si todo está bien → Estado: `ok` (tarjeta verde)

### 3. Almacenamiento de Mensajes

Los resultados se guardan en la tabla `clientes` con los siguientes campos:
- `msgA`: Estado de backups
- `msgB`: Estado de tiering  
- `msgC`: Estado de config backup
- `msgD`: Estado de replicaciones
- `estado`: Estado general (ok/warn/fail)
- `last_seen`: Última fecha/hora de actividad

### 4. Visualización en las Tarjetas

El template `index.html` recibe un array de datos donde cada fila (`row`) contiene:

```python
row[0] = nombre        # Nombre del cliente
row[1] = estado        # Estado general (ok/warn/fail)
row[2] = msgA          # "X jobs fueron exitosos en las últimas 24 horas"
row[3] = msgB          # "X offload(s) fueron exitosos en las últimas 24 horas"  
row[4] = last_seen     # "2025-09-24 15:30:00"
row[5] = msgC          # "Success" o "Fail" (config backup)
row[6] = msgD          # "X replication(s) fueron exitosos en las últimas 24 horas"
```

### 5. Funcionalidades Adicionales

- **Conversión de zona horaria**: JavaScript convierte automáticamente las fechas UTC a GMT-3 (Argentina)
- **Alertas de inactividad**: Si `last_seen` es mayor a 24 horas, se muestra un ícono de advertencia ⚠️
- **Enlaces dinámicos**: Cada tarjeta es clickeable y redirige a `/status/{cliente}` para ver detalles

## Ejemplo de Flujo Completo

1. Usuario visita `/`
2. Se ejecuta `update_client_status()`
3. Para el cliente "CLIENTE_A":
   - Se buscan hostnames asociados: `["VB0003", "VB0004"]`
   - Se consulta tabla `VB0003`: 5 backups exitosos, 1 replicación exitosa
   - Se consulta tabla `VB0004`: 3 backups exitosos, 0 replicaciones
   - Se determina estado: `ok` (todo exitoso)
   - Se guarda: `msgA="8 jobs exitosos"`, `msgD="1 replication exitosa"`
4. Se renderiza tarjeta verde con toda la información
5. JavaScript ajusta fechas a zona horaria local

Este proceso se repite para todos los clientes cada vez que se carga la página principal.

---  

## Tecnologías utilizadas

- **Backend**: Python con Flask
- **Base de datos**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Monitoreo**: Integración con Veeam Backup & Replication y Azure Recovery Services

---

## 🐳 Contenerización (a futuro)

El proyecto está preparado para correr en contenedores (Docker, Azure Container Instances, etc.), leyendo configuración desde variables de entorno externas.
