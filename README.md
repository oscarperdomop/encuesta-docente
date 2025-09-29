# Encuesta Docente

Sistema de encuestas para docentes desarrollado con FastAPI y PostgreSQL.

## 🚀 Características

- **API REST** con FastAPI
- **Base de datos PostgreSQL** con SQLModel
- **Autenticación** de usuarios
- **Gestión de encuestas** y docentes
- **Migraciones** con Alembic
- **Docker** para desarrollo

## 📁 Estructura del Proyecto

```
encuesta-docente/
├── api/                    # Backend API
│   ├── app/
│   │   ├── api/           # Rutas de la API
│   │   ├── core/          # Configuración
│   │   ├── db/            # Base de datos
│   │   ├── models/        # Modelos de datos
│   │   └── main.py        # Aplicación principal
│   ├── alembic/           # Migraciones
│   ├── scripts/           # Scripts de utilidad
│   └── requirements.txt   # Dependencias
├── data/                  # Datos de ejemplo
├── docs/                  # Documentación
├── web/                   # Frontend (futuro)
└── docker-compose.yml     # Configuración Docker
```

## 🛠️ Instalación

### Requisitos

- Python 3.11+
- Docker y Docker Compose
- Git

### Pasos

1. **Clonar el repositorio**

   ```bash
   git clone <repository-url>
   cd encuesta-docente
   ```

2. **Iniciar la base de datos**

   ```bash
   docker compose up -d db
   ```

3. **Configurar el entorno**

   ```bash
   cd api
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**

   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Ejecutar migraciones**

   ```bash
   alembic upgrade head
   ```

6. **Iniciar la API**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📚 Uso

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Desarrollo

### Comandos útiles

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1

# Ejecutar tests
pytest

# Formatear código
black .
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.
