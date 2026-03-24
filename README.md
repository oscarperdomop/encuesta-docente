# 🎓 Encuesta Docente USCO

Sistema de evaluación docente desarrollado para la Universidad Surcolombiana (USCO) con arquitectura **Backend API (FastAPI)** + **Frontend PWA (React + TypeScript)**.

---

## 🚀 Características Principales

### ✅ Implementadas

- ✅ **Autenticación por correo institucional** (@usco.edu.co) con JWT
- ✅ **Sistema de turnos** con límite configurable (máx. 2 por usuario)
- ✅ **Cola de docentes** por evaluar con selección múltiple
- ✅ **Encuesta de 16 preguntas** en 2 pasos:
  - Q1-Q9: Primer paso (escala Likert 1-5)
  - Q10-Q15: Segundo paso (escala Likert 1-5)
  - Q16: Pregunta abierta con 3 campos de texto opcionales
- ✅ **Control de intentos por usuario**:
  - Máximo 2 intentos fallidos por encuesta
  - Timer de 30 minutos por intento
  - Estados: `en_progreso`, `enviado`, `expirado`, `fallido`
- ✅ **Panel de Administración**:
  - Gestión de pesos por pregunta
  - Asignación de docentes a encuestas
  - Gestión de roles (Administrador, Encuestador Estudiante, Encuestador Docente, Jefe de Programa)
  - Otorgar intentos adicionales a usuarios bloqueados
  - Importación masiva de usuarios y docentes vía CSV
- ✅ **Reportes y Analíticas**:
  - Dashboard con estadísticas globales (enviados, pendientes, promedios)
  - Reportes por pregunta con media, desviación estándar y distribución
  - Reportes por docente con desglose de respuestas
  - Matriz de calor (docentes × preguntas)
  - Progreso diario de respuestas
  - Filtros dinámicos (programas, docentes, secciones, preguntas, fechas)
- ✅ **Exportaciones (CSV y Excel)**:
  - Respuestas completas (formato crudo y legible)
  - Preguntas con estadísticas detalladas (media, mediana, desviación, distribución)
  - Ranking de docentes con promedio y peor pregunta
  - Matriz de calor (docentes × preguntas) para análisis visual
  - Comentarios textuales (Q16) completos
  - **Archivo Excel consolidado** con 6 hojas (Resumen, Secciones, Preguntas, Docentes, Comentarios, Progreso)
- ✅ **Audit Logs** para trazabilidad de acciones administrativas
- ✅ **Resumen de turno** y cierre de sesión al finalizar
- ✅ **Frontend PWA** con React 19, React Router v7 y TailwindCSS

---

## 📁 Estructura del Proyecto

```
encuesta-docente/
├── backend/
│   └── api/                        # Backend FastAPI
│       ├── alembic/                # Migraciones de base de datos
│       │   └── versions/           # Archivos de migración
│       ├── app/
│       │   ├── api/                # Endpoints de la API
│       │   │   └── v1/
│       │   │       └── endpoints/  # Controladores por dominio
│       │   │           ├── admin_attempts.py      # Gestión de intentos (admin)
│       │   │           ├── admin_imports.py       # Importación CSV (admin)
│       │   │           ├── admin_reports.py       # Reportes y analytics (admin)
│       │   │           ├── admin_roles.py         # Gestión de roles (admin)
│       │   │           ├── admin_surveys.py       # Gestión de encuestas (admin)
│       │   │           ├── attempts.py            # CRUD de intentos (usuario)
│       │   │           ├── auth.py                # Login y autenticación
│       │   │           ├── catalogs.py            # Catálogos públicos
│       │   │           ├── health.py              # Health check
│       │   │           ├── queue.py               # Gestión de cola de docentes
│       │   │           └── sessions.py            # Gestión de turnos/sesiones
│       │   ├── core/               # Configuración y seguridad
│       │   │   ├── config.py       # Configuración de la app
│       │   │   └── security.py     # JWT, passwords, auth
│       │   ├── db/                 # Base de datos
│       │   │   ├── base.py
│       │   │   ├── base_class.py
│       │   │   └── session.py      # Sesión de SQLAlchemy
│       │   ├── models/             # Modelos SQLAlchemy
│       │   │   ├── attempt.py      # Intento y respuestas
│       │   │   ├── attempt_limit.py # Límites de intentos
│       │   │   ├── audit.py        # Logs de auditoría
│       │   │   ├── docente.py      # Docentes y asignaciones
│       │   │   ├── encuesta.py     # Encuestas, secciones, preguntas
│       │   │   ├── turno.py        # Turnos/sesiones de usuario
│       │   │   └── user.py         # Usuarios y roles
│       │   ├── schemas/            # Schemas Pydantic
│       │   │   ├── admin.py
│       │   │   ├── admin_attempts.py
│       │   │   ├── admin_reports.py
│       │   │   ├── admin_roles.py
│       │   │   ├── attempts.py
│       │   │   ├── auth.py
│       │   │   ├── imports.py
│       │   │   ├── queue.py
│       │   │   ├── sessions.py
│       │   │   └── teacher.py
│       │   ├── services/           # Lógica de negocio
│       │   │   └── audit.py        # Servicio de auditoría
│       │   └── main.py             # App FastAPI principal
│       ├── scripts/
│       │   └── import_csv.py       # Scripts de importación
│       ├── alembic.ini
│       ├── package.json            # Dependencias de Node (para PostCSS)
│       └── requirements.txt        # Dependencias Python
│
├── web/
│   └── encuesta-docente-ui/       # Frontend React PWA
│       ├── public/
│       ├── src/
│       │   ├── assets/             # Recursos estáticos
│       │   ├── components/         # Componentes reutilizables
│       │   │   ├── ConfirmModal.tsx
│       │   │   ├── LikertSelect.tsx
│       │   │   ├── ProtectedRoute.tsx
│       │   │   ├── RequireAuth.tsx
│       │   │   ├── USCOHeader.tsx
│       │   │   └── USCOPage.tsx
│       │   ├── pages/              # Páginas/Vistas
│       │   │   ├── DocentesSelect.tsx     # Selección de docentes
│       │   │   ├── Intro.tsx              # Introducción
│       │   │   ├── Justificacion.tsx      # Justificación
│       │   │   ├── Login.tsx              # Login
│       │   │   ├── NotFound.tsx           # 404
│       │   │   ├── ResumenTurno.tsx       # Resumen y finalización
│       │   │   ├── SurveyStep1.tsx        # Encuesta paso 1
│       │   │   └── SurveyStep2.tsx        # Encuesta paso 2
│       │   ├── services/           # Servicios API
│       │   │   ├── api.ts          # Cliente Axios
│       │   │   ├── attempts.ts     # API de intentos
│       │   │   ├── auth.ts         # API de autenticación
│       │   │   ├── catalogs.ts     # API de catálogos
│       │   │   └── questions.ts    # API de preguntas
│       │   ├── state/              # Estado global Zustand
│       │   │   └── authStore.ts
│       │   ├── store/              # Stores adicionales
│       │   │   ├── selection.ts    # Estado de selección
│       │   │   └── survey.ts       # Estado de encuesta
│       │   ├── utils/              # Utilidades
│       │   │   └── attemptStorage.ts
│       │   ├── main.tsx            # Entry point
│       │   └── router.tsx          # Configuración de rutas
│       ├── index.html
│       ├── package.json
│       ├── tailwind.config.js
│       ├── tsconfig.json
│       └── vite.config.ts
│
├── data/                           # Archivos CSV para importación
│   ├── asignacion_docentes.csv
│   ├── docentes_import.csv
│   ├── encuestas.csv
│   ├── periodos.csv
│   ├── permisos_finos.csv
│   ├── pesos_preguntas.csv
│   ├── preguntas_import.csv
│   └── usuarios_import.csv
│
├── docs/                           # Documentación
│   ├── CHANGELOG.md
│   └── PRD_v1.0.0.md              # Product Requirements Document
│
├── docker-compose.yml              # PostgreSQL en contenedor
├── requirements.txt                # Dependencias Python (raíz)
└── README.md                       # Este archivo
```

---

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** 0.104+ - Framework web asíncrono Python
- **SQLAlchemy** 2.0 + **SQLModel** - ORM con type hints
- **PostgreSQL** 16 - Base de datos relacional
- **Alembic** - Migraciones de base de datos
- **Pydantic** 2.5+ - Validación de datos
- **JWT (PyJWT)** - Autenticación con tokens
- **Pandas** - Procesamiento de archivos CSV
- **openpyxl** 3.1+ - Generación de archivos Excel (.xlsx)
- **Uvicorn** - Servidor ASGI

### Frontend
- **React** 19.1 - Librería de UI
- **TypeScript** 5.8 - Tipado estático
- **Vite** 7.1 - Build tool y dev server
- **React Router** 7.9 - Enrutamiento
- **Zustand** 5.0 - Gestión de estado global
- **TailwindCSS** 3.4 - Framework de estilos
- **Axios** 1.12 - Cliente HTTP

### Infraestructura
- **Docker** + **Docker Compose** - Contenedores
- **PostgreSQL** 16 - Base de datos
- **Supabase** (opcional) - Hosting de base de datos

---

## 🔧 Instalación y Configuración

### Requisitos Previos

- **Python** 3.11+
- **Node.js** 18+ y npm/yarn
- **PostgreSQL** 16+ (o Docker)
- **Git**

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd encuesta-docente
```

### 2. Configurar Backend

#### 2.1 Iniciar base de datos con Docker

```bash
docker compose up -d db
```

Esto levanta PostgreSQL en `localhost:5432` con:
- Usuario: `encuesta`
- Base de datos: `encuesta`

#### 2.2 Crear entorno virtual e instalar dependencias

```bash
cd backend/api
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

#### 2.3 Configurar variables de entorno

Crea un archivo `.env` en `backend/api/`:

```env
# Base de datos
DATABASE_URL=postgresql://encuesta:encuesta@localhost:5432/encuesta

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Límite de turnos
MAX_TURNOS=2

# CORS (separar por comas si hay varios orígenes)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Entorno
ENV=dev
APP_NAME=Encuesta Docente API
```

#### 2.4 Ejecutar migraciones

```bash
cd backend/api
alembic upgrade head
```

#### 2.5 (Opcional) Importar datos de ejemplo

```bash
# Importar usuarios, docentes, encuestas, preguntas, etc.
python scripts/import_csv.py
```

#### 2.6 Iniciar el servidor backend

```bash
cd backend/api
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Docs (Swagger)**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### 3. Configurar Frontend

#### 3.1 Instalar dependencias

```bash
cd web/encuesta-docente-ui
npm install
```

#### 3.2 Configurar variables de entorno

Crea un archivo `.env` en `web/encuesta-docente-ui/`:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_TIMEOUT=10000
```

#### 3.3 Iniciar el servidor de desarrollo

```bash
npm run dev
```

La aplicación estará disponible en:
- **Frontend**: http://localhost:5173

---

## 📊 Modelo de Datos

### Entidades Principales

- **`users`** - Usuarios del sistema (email, nombre, estado)
- **`roles`** - Roles del sistema (Administrador, Encuestador, etc.)
- **`user_roles`** - Relación muchos a muchos entre usuarios y roles
- **`teachers`** - Docentes evaluables (identificador único, nombre, programa)
- **`periods`** - Periodos académicos (año, semestre)
- **`surveys`** - Encuestas (código, nombre, periodo, estado, fechas)
- **`survey_sections`** - Secciones de encuesta (título, orden)
- **`questions`** - Preguntas (código, enunciado, tipo, peso, orden)
- **`survey_teacher_assignments`** - Asignación de docentes a encuestas
- **`turnos`** - Sesiones de usuario (open/closed)
- **`attempts`** - Intentos de evaluación (usuario, encuesta, docente, estado, timer)
- **`responses`** - Respuestas individuales (valor Likert o texto)
- **`attempt_limits`** - Límites de intentos por usuario/encuesta
- **`audit_logs`** - Trazabilidad de acciones administrativas

### Restricciones Clave

- Email único y dominio `@usco.edu.co` obligatorio
- Identificador de docente único (`identificador`)
- Un usuario solo puede tener un intento `en_progreso` activo por encuesta
- Un usuario solo puede enviar una evaluación por docente (índice único)
- Timer de 30 minutos por intento con expiración automática

---

## 🔐 Autenticación y Roles

### Flujo de Autenticación

1. Usuario ingresa email `@usco.edu.co`
2. Sistema valida que el email existe en BD y estado es `activo`
3. Sistema verifica turnos consumidos (max. 2)
4. Si es válido, se genera token JWT
5. Token se incluye en header `Authorization: Bearer <token>` en todas las peticiones

### Roles Implementados

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **Administrador** | Acceso completo al sistema | Todos los permisos + panel admin |
| **Encuestador Estudiante** | Estudiante evaluador | Solo responder encuestas |
| **Encuestador Docente** | Docente evaluador | Solo responder encuestas |
| **Jefe de Programa** | Coordinador de programa | Solo responder encuestas |

---

## 🌐 API Endpoints

### Autenticación (`/api/v1/auth`)

- `POST /auth/login` - Login con email
- `GET /auth/me` - Obtener usuario actual

### Catálogos (`/api/v1`)

- `GET /surveys/activas` - Listar encuestas activas
- `GET /surveys/{id}/teachers` - Listar docentes de una encuesta
- `GET /surveys/{id}/questions` - Listar preguntas de una encuesta

### Intentos (`/api/v1/attempts`)

- `POST /attempts` - Crear intentos para docentes seleccionados
- `GET /attempts/{id}` - Obtener detalle de intento
- `PATCH /attempts/{id}` - Actualizar progreso (autosave)
- `POST /attempts/{id}/responses` - Guardar respuestas parciales
- `POST /attempts/{id}/submit` - Enviar evaluación final
- `GET /attempts/summary` - Resumen de intentos del usuario

### Cola (`/api/v1/queue`)

- `GET /queue` - Obtener siguiente docente en la cola

### Sesiones/Turnos (`/api/v1/sessions`)

- `POST /sessions/close` - Cerrar turno/sesión actual

### Admin - Importaciones (`/api/v1/admin/imports`)

- `GET /imports/teachers/template.csv` - Descargar plantilla CSV de docentes
- `POST /imports/teachers` - Importar docentes desde CSV (opcionalmente asignarlos a una encuesta activa con `survey_id`)
- `GET /imports/users/template.csv` - Descargar plantilla CSV de usuarios
- `POST /imports/users` - Importar usuarios desde CSV (`email`, `rol` requeridos; `nombre`, `estado` opcionales). Soporta `dry_run` y `replace_roles`

### Admin - Roles (`/api/v1/admin/roles`)

- `POST /roles/grant` - Asignar rol a usuario
- `DELETE /roles/revoke` - Revocar rol de usuario

### Admin - Usuarios (`/api/v1/admin`)

- `GET /usuarios` - Listar usuarios con paginación y búsqueda (`search`, `rol`, `estado`, `page`, `per_page`)

### Admin - Intentos (`/api/v1/admin/attempts`)

- `POST /attempts/extra` - Otorgar intentos adicionales

### Admin - Encuestas (`/api/v1/admin/surveys`)

- `POST /surveys` - Crear encuesta
- `PUT /surveys/{id}/questions/{qid}` - Actualizar peso de pregunta
- `POST /surveys/{id}/teachers/assign` - Asignar docentes a encuesta

### Admin - Reportes (`/api/v1/admin/reports`)

**Estadísticas Generales:**
- `GET /reports/stats/overview` - **Estadísticas generales del sistema** (usuarios activos, encuestas, usuarios que completaron, tasa participación)

**Reportes Detallados:**
- `GET /reports/summary` - Resumen global de encuesta
- `GET /reports/questions` - Listado de preguntas con estadísticas
- `GET /reports/questions/{id}` - Detalle de pregunta
- `GET /reports/teachers` - Listado de docentes con estadísticas
- `GET /reports/teachers/{id}` - Detalle de docente
- `GET /reports/teachers/matrix` - Matriz docentes × preguntas
- `GET /reports/teachers/filters` - Filtros para dashboard
- `GET /reports/comments` - Listado de comentarios textuales
- `GET /reports/progress/daily` - Progreso diario
- `GET /reports/sections/summary` - Resumen por sección
- `GET /reports/questions/top-bottom` - Top/Bottom preguntas

### Admin - Exportaciones (`/api/v1/admin/reports/exports`)

**Respuestas:**
- `GET /exports/survey/{id}/responses.csv` - Exportar respuestas (formato crudo con IDs)
- `GET /exports/survey/{id}/responses-pretty.csv` - Exportar respuestas (formato legible para Excel)

**Preguntas:**
- `GET /exports/survey/{id}/questions.csv` - Exportar preguntas con configuración y estadísticas
- `GET /exports/questions-stats.csv` - Estadísticas detalladas por pregunta (media, mediana, desviación, distribución 1-5)

**Docentes:**
- `GET /exports/survey/{id}/teachers.csv` - Ranking de docentes con promedio global y peor pregunta
- `GET /exports/teachers-stats.csv` - Estadísticas por docente (n respuestas, promedio, peor pregunta)
- `GET /exports/matrix.csv` - Matriz de calor (docentes × preguntas) filtrable por programa

**Comentarios:**
- `GET /exports/survey/{id}/comments.csv` - Exportar todos los comentarios textuales (Q16)

**Consolidado Excel:**
- `GET /exports/survey/{id}.xlsx` - Archivo Excel completo con múltiples hojas (Resumen, Secciones, Preguntas, Docentes, Comentarios, Progreso)

---

## 🎨 Flujo de Usuario

### Para Encuestadores

1. **Login** → Ingresa email @usco.edu.co
2. **Introducción** → Lee la presentación del sistema
3. **Justificación** → Lee el propósito de la evaluación
4. **Selección de docentes** → Selecciona uno o varios docentes de la lista
5. **Encuesta - Paso 1** → Responde Q1-Q9 (30 min timer)
6. **Encuesta - Paso 2** → Responde Q10-Q15 + Q16 (comentarios)
7. **Confirmación** → Confirma envío de evaluación
8. **Siguiente docente** → Repite 5-7 para cada docente en cola
9. **Resumen** → Ve estado de todos los intentos
10. **Finalizar turno** → Cierra sesión y consume 1 turno

### Para Administradores

1. **Login** → Acceso con rol de administrador
2. **Panel Admin** → Acceso a sección administrativa
3. Gestionar:
   - Importar usuarios/docentes masivamente
   - Crear y configurar encuestas
   - Asignar docentes a encuestas
   - Configurar pesos de preguntas
   - Otorgar intentos adicionales
   - Ver reportes y analytics
   - Exportar datos

---

## 🧪 Desarrollo

### Comandos Backend

```bash
# Crear migración
cd backend/api
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Formatear código
black app/

# Linting
flake8 app/
```

### Comandos Frontend

```bash
cd web/encuesta-docente-ui

# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

---

## 📈 Métricas y KPIs

El sistema rastrea:

- **Tasa de finalización** de encuestas
- **Tiempo promedio** por intento
- **Intentos fallidos/expirados** por usuario
- **Promedio global** por pregunta/docente/sección
- **Desviación estándar** por pregunta
- **Distribución de respuestas** (histograma 1-5)
- **Progreso diario** de evaluaciones
- **Top/Bottom preguntas** por score

---

## 📝 Licencia

Este proyecto está bajo Licencia MIT.
