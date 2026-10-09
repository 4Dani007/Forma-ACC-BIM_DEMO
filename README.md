# Senda — permisos de obra

Demostración para administrar usuarios y permisos de carpetas en proyectos de construcción: asignación masiva, tabla de permisos por carpeta y rol, y un comparador que muestra las diferencias entre dos obras.

Los datos son ficticios. Un servicio simulado imita el comportamiento de una API de gestión documental. No contiene código, credenciales ni información de ningún cliente, y no tiene relación con Autodesk. La interfaz no usa marcas ni logotipos de terceros.

**Demo en línea:** `[pendiente: enlace]`

## Qué problema resuelve

Configurar permisos a mano, obra por obra y carpeta por carpeta, es lento y fácil de equivocar. Senda permite revisar el cambio antes de aplicarlo, exportar la matriz y ver de un vistazo en qué se parecen dos proyectos.

## Funcionalidades

- Asignación masiva de usuarios desde un CSV, con vista previa y confirmación.
- Tabla de permisos por carpeta y rol, con exportación a CSV y Excel.
- Cambio masivo de permisos, también con vista previa.
- Descarga de metadatos del proyecto.
- Comparador de estructuras. Las carpetas se emparejan por ruta.
- Registro de cada acción masiva.
- Restauración de los datos de ejemplo.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | React, JavaScript, Vite |
| Backend | Python, FastAPI |
| Datos | SQLite en local y Docker; PostgreSQL (Neon) en la demo pública |
| Contenedores | Docker, Docker Compose |
| Despliegue | Vercel, un proyecto para la interfaz y otro para la API |

## Arquitectura

```
┌────────────┐   HTTP/JSON   ┌──────────────────────┐
│  React     │ ────────────► │  FastAPI             │
│            │ ◄──────────── │  validación y reglas │
└────────────┘               └──────────┬───────────┘
                                        │
                               ┌────────▼────────┐
                               │ ProjectProvider │
                               │  MockProvider   │
                               └────────┬────────┘
                                        │
                                   SQLite / Postgres
```

La lógica de asignación, permisos y comparación habla con `ProjectProvider`, no con la base ni con un servicio externo. `MockProvider` es la implementación de la demo. Otra implementación podría cumplir la misma interfaz sin tocar los servicios.

## Modelo

| Entidad | Campos principales |
|---|---|
| `Project` | id, nombre, código, estado, cliente, fase |
| `User` | id, nombre, correo, empresa |
| `Role` | Coordinador, Residente, Contratista, Visor |
| `Folder` | proyecto, padre, nombre, ruta |
| `Membership` | usuario, proyecto, rol |
| `FolderPermission` | carpeta, rol, nivel (`ver`, `descargar`, `editar`, `administrar`) |
| `AuditLog` | acción, detalle, fecha |

Entre Torre Andina etapa 1 y etapa 2 hay diferencias sembradas: un permiso distinto en `03 Construcción/Planos`, otro en `02 Diseño/MEP`, el rol Residente sin permiso en `04 Calidad/Ensayos`, y la carpeta `05 Seguridad/Incidentes` solo en la etapa 1.

## API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/projects` | Lista de proyectos |
| `GET` | `/api/projects/{id}` | Ficha y miembros |
| `GET` | `/api/projects/{id}/metadata` | Metadatos descargables |
| `GET` | `/api/projects/{id}/permissions` | Matriz de permisos |
| `GET` | `/api/projects/{id}/permissions/export?format=csv\|xlsx` | Exportación |
| `POST` | `/api/memberships/bulk/preview` | Vista previa de asignación |
| `POST` | `/api/memberships/bulk/apply` | Aplica la asignación |
| `POST` | `/api/permissions/bulk/preview` | Vista previa de permisos |
| `POST` | `/api/permissions/bulk/apply` | Aplica los permisos |
| `GET` | `/api/compare?a={id}&b={id}` | Diferencias entre dos proyectos |
| `GET` | `/api/audit` | Registro |
| `POST` | `/api/demo/reset` | Restaura los datos de ejemplo |

La documentación interactiva queda en `/docs`.

Una fila inválida no bloquea al resto. Las filas válidas de una misma operación se confirman en una sola transacción. El correo `falla@demo.example` simula un rechazo del proveedor, siempre, para poder mostrarlo en la vista previa.

## Cómo ejecutarlo

### Con Docker

```bash
docker compose up --build
```

- Aplicación: http://localhost:3000
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs

```bash
docker compose exec backend pytest
```

### Sin Docker

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

El CSV de ejemplo está en `sample-data/usuarios_ejemplo.csv` y también se descarga desde la pantalla de asignación. Trae 30 personas e incluye filas que la vista previa debe rechazar o marcar.

## Despliegue en Vercel

Son dos proyectos del mismo repositorio.

1. Crea una base en [Neon](https://neon.tech) y copia la URL `postgresql://...`.
2. Proyecto API: Root Directory `backend`. Vercel detecta FastAPI por `pyproject.toml`. Variables:
   - `DATABASE_URL`: la URL de Neon
   - `CORS_ORIGINS`: la URL del frontend, por ejemplo `https://senda.vercel.app`
3. Proyecto frontend: Root Directory `frontend`, framework Vite. Variable:
   - `VITE_API_URL`: la URL del API, sin barra final
4. Vuelve a desplegar el frontend después de definir `VITE_API_URL`, porque Vite la incluye en el build.
5. Si un visitante modifica los datos, el botón «Restaurar datos de ejemplo» los regenera.

Sin `DATABASE_URL`, la API arranca con SQLite. En Vercel ese archivo no se conserva entre instancias; Neon es lo que hace que todos los visitantes vean los mismos datos.

## Decisiones

- El proveedor separa las reglas de la fuente de datos. Cambiar SQLite por Postgres es un cambio de `DATABASE_URL`, no de la asignación ni del comparador.
- El comparador identifica carpetas por ruta (`03 Construcción/Planos`), porque cada obra tiene sus propios ids. Clasifica permiso distinto, rol sin permiso y carpeta faltante. Si una fila tiene los dos primeros, prevalece «permiso distinto» y el detalle lista ambos.
- La vista previa no escribe. Al confirmar, cada fila se vuelve a validar. Las rechazadas quedan en el reporte y las válidas entran en una sola transacción: un fallo de base no deja la carga a medias. El registro guarda aplicadas, omitidas y rechazadas.

## Pruebas

`backend/tests/test_api.py` cubre el comparador con las diferencias sembradas, la vista previa que no persiste, la carga parcial, el permiso masivo, la exportación y el reinicio de la demo. El workflow de GitHub Actions corre esa suite y el build del frontend.

## Posibles mejoras

- Autenticación y permisos dentro de la propia herramienta.
- Un segundo `ProjectProvider` contra una API real de gestión documental.
- Cola de tareas para lotes muy grandes.
- Pruebas de interfaz con Playwright.

## Autor

**Daniel Bonilla Mosquera** · Desarrollador de Software
[LinkedIn](https://linkedin.com/in/daniel-bonilla-a0b98831b/) · [GitHub](https://github.com/4Dani007)
