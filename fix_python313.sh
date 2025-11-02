#!/bin/bash
# Complete Python 3.13 fix script for Kali Linux

set -e

echo "🔧 Fixing Python 3.13 compatibility issues..."
echo ""

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    postgresql-server-dev-all \
    libpq-dev \
    python3-dev \
    build-essential \
    antiword

echo ""
echo "✅ System dependencies installed"
echo ""

# Check if in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo ""
echo "📦 Installing Python packages..."
pip install -r requirements.txt

echo ""
echo "✅ Verifying installation..."
python -c "import fastapi, sqlalchemy, psycopg2, docx; print('✅ All imports successful')"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure database: cp .env.example .env"
echo "2. Edit .env with your PostgreSQL credentials"
echo "3. Initialize database: python init_db.py"
echo "4. Start application: python main.py"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Documentation: http://localhost:8000/docs"
