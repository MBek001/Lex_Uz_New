# Python 3.13 Compatibility Fix

If you're using Python 3.13 (like on Kali Linux), you may encounter build errors. Here's how to fix them:

## Issues

1. **psycopg2-binary**: Missing PostgreSQL development headers
2. **pydantic-core**: Old version incompatible with Python 3.13

## Quick Fix

### Step 1: Install System Dependencies

```bash
# On Kali/Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y postgresql-server-dev-all libpq-dev python3-dev

# On other Debian-based systems
sudo apt-get install -y libpq-dev python3-dev build-essential

# On macOS
brew install postgresql
```

### Step 2: Pull Latest Requirements

```bash
cd ~/PycharmProjects/Lex_Uz_New
git pull origin claude/bulk-document-import-postgres-011CUikGCjDzfVQ7NgKZJbPL
```

### Step 3: Install Python Packages

```bash
# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

## What Changed

### Updated Versions (Python 3.13 Compatible)

| Package | Old Version | New Version | Reason |
|---------|-------------|-------------|--------|
| fastapi | 0.109.0 | 0.115.6 | Latest stable |
| uvicorn | 0.27.0 | 0.34.0 | Latest stable |
| pydantic | 2.5.3 | 2.10.6 | Python 3.13 support |
| pydantic-core | 2.14.6 | 2.27.x | Python 3.13 support |
| sqlalchemy | 2.0.25 | 2.0.36 | Bug fixes |
| psycopg2-binary | 2.9.9 | 2.9.10 | Latest stable |
| pytest | 7.4.4 | 8.3.4 | Python 3.13 support |

## Alternative: Use Python 3.11 or 3.12

If you prefer not to deal with Python 3.13 issues, you can use Python 3.11 or 3.12:

```bash
# Install Python 3.11 on Kali
sudo apt-get install python3.11 python3.11-venv

# Create new virtual environment with Python 3.11
python3.11 -m venv .venv311
source .venv311/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Troubleshooting

### Issue: "libpq-fe.h: No such file or directory"

**Solution**: Install PostgreSQL development libraries
```bash
sudo apt-get install -y postgresql-server-dev-all libpq-dev
```

### Issue: "pydantic-core build failed"

**Solution**: Use updated requirements.txt with Python 3.13 compatible versions
```bash
git pull origin claude/bulk-document-import-postgres-011CUikGCjDzfVQ7NgKZJbPL
pip install -r requirements.txt
```

### Issue: "Failed building wheel"

**Solution**: Install build tools
```bash
sudo apt-get install -y build-essential python3-dev
pip install --upgrade pip setuptools wheel
```

## Verification

After successful installation, verify everything works:

```bash
# Check imports
python -c "import fastapi, sqlalchemy, psycopg2, docx; print('✅ All imports successful')"

# Check database connection (if PostgreSQL is running)
python -c "from app.config.database import engine; engine.connect(); print('✅ Database connection successful')"

# Start the application
python main.py
```

## Full Installation Script

Here's a complete script to fix everything:

```bash
#!/bin/bash
# Complete Python 3.13 fix script

echo "🔧 Fixing Python 3.13 compatibility issues..."

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    postgresql-server-dev-all \
    libpq-dev \
    python3-dev \
    build-essential \
    antiword \
    libreoffice

# Navigate to project
cd ~/PycharmProjects/Lex_Uz_New

# Activate virtual environment
source .venv/bin/activate

# Pull latest changes
echo "📥 Pulling latest code..."
git pull origin claude/bulk-document-import-postgres-011CUikGCjDzfVQ7NgKZJbPL

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Verify installation
echo "✅ Verifying installation..."
python -c "import fastapi, sqlalchemy, psycopg2, docx; print('✅ All imports successful')"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure database: cp .env.example .env"
echo "2. Initialize database: python init_db.py"
echo "3. Start application: python main.py"
```

Save this as `fix_python313.sh` and run:
```bash
chmod +x fix_python313.sh
./fix_python313.sh
```

## Why These Errors Happened

1. **psycopg2-binary**: Tries to compile C extensions, needs PostgreSQL headers
2. **pydantic-core**: Old version (2.14.6) was built before Python 3.13 release
3. **Python 3.13**: Released recently (October 2024), some packages need updates

## Summary

✅ **Fixed**: Updated all packages to Python 3.13 compatible versions
✅ **Required**: PostgreSQL development libraries
✅ **Works with**: Python 3.11, 3.12, and 3.13

Your installation should work perfectly now!
