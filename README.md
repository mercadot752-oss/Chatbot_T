# Asistente virtual institucional UdeM

Chatbot institucional de la Universidad de Medellín. La aplicación permite hacer consultas generales en lenguaje natural y, cuando la identificación existe en la base de datos, añadir información de perfil al contexto. Las conversaciones del chat principal se guardan en PostgreSQL.

## Tecnologías

- **Frontend:** React 18.3.1, React DOM 18.3.1, React Router 7.9.3 y Vite 5.4.20; servido por Nginx (`stable-alpine`).
- **Backend:** Python 3.12, FastAPI 0.117.1, Uvicorn 0.37.0 y SQLAlchemy 2.0.44.
- **Base de datos:** PostgreSQL 16 (`postgres:16-alpine`) con Psycopg2 2.9.11.
- **Proveedor de IA:** Groq SDK 0.33.0.
- **Contenedores:** Docker Compose; imagen de construcción del frontend `node:22-alpine`.

Las versiones de los paquetes del backend están fijadas en `backend/requirements.txt`. Las versiones instaladas del frontend se pueden consultar con `npm list --depth=0` desde `frontend/`.

## Requisitos

- Docker Desktop con Docker Compose habilitado.
- Una clave de API de Groq para generar respuestas con IA.

## Descargar el proyecto

El repositorio principal contiene frontend y backend como submódulos. Clónalo incluyendo ambos proyectos:

```powershell
git clone --recurse-submodules https://github.com/mercadot752-oss/Chatbot_T.git
cd Chatbot_T
```

Si ya clonaste el repositorio principal sin los submódulos, inicialízalos desde su carpeta:

```powershell
git submodule update --init --recursive
```

## Configuración y ejecución en Windows

Abre PowerShell en la carpeta raíz del proyecto, donde está `docker-compose.yml`.

1. Crea `.env` a partir del ejemplo si todavía no existe:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

2. Edita `.env` y asigna tu clave de Groq a `GROQ_API_KEY`. No compartas ni publiques este archivo.

3. Construye e inicia los servicios:

   ```powershell
   docker compose up --build -d
   ```

4. Revisa su estado:

   ```powershell
   docker compose ps
   ```

Cuando frontend y backend estén activos, abre:

- Aplicación: <http://localhost:5173>
- Bienvenida del backend: <http://localhost:8000/> (debe responder con “Hola mundo”).
- Documentación interactiva de FastAPI (Swagger): <http://localhost:8000/docs>

El frontend envía las solicitudes del chatbot al backend a través del proxy de Nginx. Docker Compose configura `DATABASE_URL` para que el backend use el PostgreSQL del servicio `db`.

## Base de datos

PostgreSQL se ejecuta en un contenedor local y guarda sus archivos en el volumen de Docker `postgres_data`. El backend registra los modelos SQLAlchemy y crea las tablas faltantes al iniciar. La estructura de los modelos está en `backend/app/controller/models.py`.

Para conectarse desde pgAdmin en el mismo equipo, usa el host `127.0.0.1`, el puerto `5433`, la base de mantenimiento `chatbot` y el usuario configurado en `.env` (`POSTGRES_USER`). Usa la contraseña de `.env` (`POSTGRES_PASSWORD`). El puerto externo `5433` evita conflictos con otras instalaciones locales de PostgreSQL; dentro de Docker, el backend se conecta al servicio `db` por el puerto interno `5432`.

Para revisar el estado de PostgreSQL:

```powershell
docker compose exec db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Para listar las tablas:

```powershell
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() ORDER BY table_name;"'
```

Para revisar los últimos intercambios guardados por el chat:

```powershell
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, numero_documento, mensaje, estado, created_at FROM chat_history ORDER BY id DESC LIMIT 5;"'
```

Los datos se conservan al detener o reconstruir los contenedores. Para detener los servicios sin eliminar el volumen:

```powershell
docker compose down
```

`docker compose down -v` elimina también el volumen de PostgreSQL y sus datos. Úsalo solo si quieres borrar la base local.

> La validación actual comprueba que el número de identificación exista en la base de datos. No reemplaza un inicio de sesión institucional ni demuestra por sí sola la identidad de quien lo escribe.

## Registros y solución de problemas

Ver los registros del backend:

```powershell
docker compose logs -f backend
```

Si aparece un error indicando que falta `GROQ_API_KEY`, revisa que la clave esté asignada en `.env` y vuelve a crear el backend:

```powershell
docker compose up -d --build backend
```

Si cambias código del frontend o backend, reconstruye el servicio correspondiente con `docker compose up -d --build frontend` o `docker compose up -d --build backend`.

## Pruebas unitarias del backend

Se incluyen pruebas iniciales de identificación y de protección del contexto personalizado. Con el entorno virtual activo, desde `backend/app/` ejecuta:

```powershell
python -m unittest discover -s tests -v
```

También puedes ejecutarlas dentro del contenedor después de construirlo:

```powershell
docker compose exec backend python -m unittest discover -s tests -v
```

Las historias y su tabla de asignación están en [`docs/historias_usuario.md`](docs/historias_usuario.md). Los responsables se deben acordar y completar por el equipo.

## Pruebas iniciales de Playwright

Las pruebas E2E verifican la navegación al chat y el reconocimiento de identificaciones de prueba para los roles `usuario` y `profesor`, además del manejo de una identificación inexistente. Usan el backend y PostgreSQL locales; no llaman a Groq.

Con Docker Compose activo, desde la raíz del proyecto carga o restaura los perfiles sintéticos:

```powershell
Get-Content .\backend\database\seed_demo.sql | docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Después, desde `frontend/`, instala dependencias, instala el navegador de Playwright y ejecuta las pruebas:

```powershell
npm install
npx playwright install chromium
npm run test:e2e
```

Los perfiles usados por las pruebas tienen identificaciones ficticias `999000001` a `999000006` y no representan personas reales.

## Imágenes DockerHub

Las imágenes del proyecto se publican bajo la cuenta `juan778`:

```powershell
docker pull juan778/chatbot-frontend:latest
docker pull juan778/chatbot-backend:latest
```
link imagenes
https://hub.docker.com/repository/docker/juan778/chatbot-backend/general
https://hub.docker.com/repository/docker/juan778/chatbot-frontend/general

El archivo Compose incluye estos nombres y puede construir las imágenes localmente desde los Dockerfiles. Para publicarlas después de iniciar sesión en DockerHub:

```powershell
docker compose build frontend backend
docker compose push frontend backend
```

## Estructura del proyecto

```text
.
├── backend/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

## Integrantes

- Juan José Cano Giraldo
- Tomás Mercado Ramos
- Christofer
