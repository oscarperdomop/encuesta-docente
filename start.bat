@echo off
REM Script para iniciar el proyecto Encuesta Docente en Windows

echo 🚀 Iniciando Encuesta Docente...

REM Verificar si Docker está corriendo
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no está corriendo. Por favor inicia Docker Desktop.
    pause
    exit /b 1
)

REM Iniciar la base de datos
echo 📦 Iniciando base de datos PostgreSQL...
docker compose up -d db

REM Esperar a que la base de datos esté lista
echo ⏳ Esperando a que la base de datos esté lista...
timeout /t 10 /nobreak >nul

REM Verificar que la base de datos esté funcionando
docker ps | findstr "encuesta_db" >nul
if %errorlevel% neq 0 (
    echo ❌ Error al iniciar la base de datos
    pause
    exit /b 1
) else (
    echo ✅ Base de datos iniciada correctamente
)

REM Navegar al directorio de la API
cd api

REM Verificar si el entorno virtual existe
if not exist ".venv" (
    echo 🔧 Creando entorno virtual...
    python -m venv .venv
)

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Instalar dependencias
echo 📦 Instalando dependencias...
pip install -r requirements.txt

REM Verificar si existe el archivo .env
if not exist ".env" (
    echo ⚙️ Creando archivo .env...
    (
        echo DATABASE_URL=postgresql://encuesta:encuesta@localhost:5432/encuesta
        echo APP_NAME=Encuesta Docente API
        echo DEBUG=True
        echo SECRET_KEY=your-secret-key-change-in-production
    ) > .env
    echo ✅ Archivo .env creado
)

REM Ejecutar migraciones
echo 🗄️ Ejecutando migraciones...
alembic upgrade head

REM Iniciar la API
echo 🚀 Iniciando API...
echo 📚 Documentación disponible en: http://localhost:8000/docs
echo 🔍 Health check en: http://localhost:8000/health
echo.
echo Presiona Ctrl+C para detener la API
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



