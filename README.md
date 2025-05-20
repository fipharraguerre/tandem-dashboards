### ✅ `README.md`

```markdown
# Flask Veeam Dashboard

Aplicación web escrita en Flask para visualizar el estado de backups y otras métricas de Veeam, basada en datos de una base MariaDB.

## 📦 Estructura del Proyecto

```

.
├── app.py                # Punto de entrada principal, registra los Blueprints
├── .env                  # Variables de entorno (no se sube a Git)
├── routes/               # Rutas agrupadas por funcionalidad
│   ├── **init**.py
│   ├── index.py
│   ├── admin.py
│   ├── status.py
│   └── unsuccessful.py
├── auth.py               # Lógica de autenticación y manejo de login
├── core.py               # Lógica de negocio (estado de clientes)
├── db.py                 # Conexión a la base de datos usando variables de entorno
├── logger.py             # Configuración de logging con rotación
├── templates/            # Archivos HTML para Flask
└── static/               # Archivos estáticos (CSS, JS, imágenes)

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

## 🐳 Contenerización (a futuro)

El proyecto está preparado para correr en contenedores (Docker, Azure Container Instances, etc.), leyendo configuración desde variables de entorno externas.
