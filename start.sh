#!/bin/bash
# Quick start script for Lex Uz Bulk Document Import System

set -e

echo "🚀 Starting Lex Uz Bulk Document Import System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please update DATABASE_URL if needed."
    echo ""
fi

# Check if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Docker Compose detected. Starting with Docker..."
    docker-compose up -d

    echo ""
    echo "⏳ Waiting for services to be ready..."
    sleep 5

    echo ""
    echo "✅ Services started!"
    echo ""
    echo "📍 Access points:"
    echo "   API: http://localhost:8000"
    echo "   Docs: http://localhost:8000/docs"
    echo "   Database: localhost:5432"
    echo ""
    echo "📊 Check status:"
    echo "   docker-compose ps"
    echo "   docker-compose logs -f app"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose down"

elif command -v python3 &> /dev/null; then
    echo "🐍 Python detected. Starting locally..."

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi

    echo "📦 Activating virtual environment..."
    source venv/bin/activate

    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt

    echo "🗄️  Initializing database..."
    python3 init_db.py

    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 Starting application..."
    python3 main.py

else
    echo "❌ Error: Neither Docker nor Python 3 found!"
    echo "   Please install Docker or Python 3.11+"
    exit 1
fi
