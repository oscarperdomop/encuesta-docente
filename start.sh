#!/bin/bash

# Script para iniciar el proyecto Encuesta Docente

echo "🚀 Iniciando Encuesta Docente..."

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
fi

# Iniciar la base de datos
echo "📦 Iniciando base de datos PostgreSQL..."
docker compose up -d db

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que la base de datos esté lista..."
sleep 10

# Verificar que la base de datos esté funcionando
if docker ps | grep -q "encuesta_db"; then
    echo "✅ Base de datos iniciada correctamente"
else
    echo "❌ Error al iniciar la base de datos"
    exit 1
fi

# Navegar al directorio de la API
cd api

# Verificar si el entorno virtual existe
if [ ! -d ".venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python -m venv .venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Verificar si existe el archivo .env
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo .env..."
    cat > .env << EOF
DATABASE_URL=postgresql://encuesta:encuesta@localhost:5432/encuesta
APP_NAME=Encuesta Docente API
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
EOF
    echo "✅ Archivo .env creado"
fi

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
alembic upgrade head

# Iniciar la API
echo "🚀 Iniciando API..."
echo "📚 Documentación disponible en: http://localhost:8000/docs"
echo "🔍 Health check en: http://localhost:8000/health"
echo ""
echo "Presiona Ctrl+C para detener la API"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



