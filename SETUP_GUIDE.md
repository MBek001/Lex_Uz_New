# Setup Guide - Lex Uz Bulk Document Import

This guide will help you set up and run the bulk document import system.

## Prerequisites

Choose one of the following:

### Option A: Docker (Easiest)
- Docker Desktop or Docker Engine
- Docker Compose

### Option B: Local Installation
- Python 3.11 or higher
- PostgreSQL 13 or higher
- System packages: `antiword`, `python3-dev`, `libpq-dev`

## Installation Steps

### Using Docker (Recommended)

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd Lex_Uz_New
```

2. **Start the system**:
```bash
./start.sh
```

That's it! The script will:
- Create `.env` file
- Start PostgreSQL and the application
- Initialize database tables

3. **Verify it's running**:
```bash
# Check services
docker-compose ps

# View logs
docker-compose logs -f app

# Test API
curl http://localhost:8000/health
```

### Using Local Installation

1. **Install system dependencies**:

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv postgresql antiword python3-dev libpq-dev
```

**macOS**:
```bash
brew install python@3.11 postgresql antiword
```

**CentOS/RHEL**:
```bash
sudo yum install -y python3.11 postgresql-server antiword python3-devel postgresql-devel
```

2. **Set up PostgreSQL**:
```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database
sudo -u postgres createdb lex_uz_db

# Or with custom user
createdb -U your_user lex_uz_db
```

3. **Clone and setup**:
```bash
git clone <your-repo-url>
cd Lex_Uz_New

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env

# Edit .env with your database credentials
nano .env  # or vim, code, etc.
```

Example `.env`:
```env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/lex_uz_db
```

5. **Initialize database**:
```bash
python init_db.py
```

6. **Start the application**:
```bash
python main.py
```

## Verification

### 1. Check API is running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Check database connection

```bash
# Using Docker
docker-compose exec db psql -U postgres -d lex_uz_db -c "\dt"

# Using local PostgreSQL
psql -U postgres -d lex_uz_db -c "\dt"
```

Expected output:
```
             List of relations
 Schema |      Name      | Type  |  Owner
--------+----------------+-------+----------
 public | ru_documents   | table | postgres
 public | uz_documents   | table | postgres
```

### 3. Access documentation

Open in browser: http://localhost:8000/docs

You should see the Swagger UI with all available endpoints.

## First Upload Test

### 1. Prepare test data

Create a small ZIP file with a few DOC/DOCX files:

```bash
# Create test directory
mkdir -p test_docs
cd test_docs

# Create a sample DOCX (or copy your existing ones)
# Then create ZIP
cd ..
zip -r test_documents.zip test_docs/
```

### 2. Upload via cURL

```bash
# Russian documents
curl -X POST "http://localhost:8000/api/upload/russian" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_documents.zip"
```

### 3. Upload via Python script

```bash
python test_upload.py test_documents.zip russian
```

### 4. Upload via Web UI

1. Open http://localhost:8000/docs
2. Find `POST /api/upload/russian`
3. Click "Try it out"
4. Upload your ZIP file
5. Click "Execute"

### 5. Check results

```bash
# Get statistics
curl http://localhost:8000/api/stats/russian

# Or using Python script
python test_upload.py stats russian
```

## Production Deployment

### 1. Security Configuration

**Update `.env` with strong credentials**:
```env
DATABASE_URL=postgresql://prod_user:strong_password_here@db:5432/lex_uz_db
```

**Update CORS in `main.py`**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 2. Use Production Server

Instead of `python main.py`, use Gunicorn:

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Set Up Nginx Reverse Proxy

**Install Nginx**:
```bash
sudo apt-get install nginx
```

**Configure** (`/etc/nginx/sites-available/lex-uz`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 5G;  # Allow large uploads

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600;  # 1 hour timeout for large uploads
    }
}
```

**Enable and restart**:
```bash
sudo ln -s /etc/nginx/sites-available/lex-uz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Set Up SSL with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 5. Configure Systemd Service

Create `/etc/systemd/system/lex-uz.service`:
```ini
[Unit]
Description=Lex Uz Bulk Document Import API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/lex-uz
Environment="PATH=/opt/lex-uz/venv/bin"
ExecStart=/opt/lex-uz/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl enable lex-uz
sudo systemctl start lex-uz
sudo systemctl status lex-uz
```

## Troubleshooting

### Database Connection Errors

**Error**: `could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Check connection
psql -U postgres -h localhost -d lex_uz_db

# Verify .env DATABASE_URL is correct
cat .env
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find what's using port 8000
lsof -i :8000
sudo kill <PID>

# Or use different port
python main.py --port 8001
```

### Docker Issues

**Error**: `Cannot connect to Docker daemon`

**Solution**:
```bash
# Start Docker
sudo systemctl start docker  # Linux
open -a Docker              # macOS

# Check Docker status
docker info
```

### Upload Fails

**Error**: File upload times out

**Solution**:
1. Check file size limits in `main.py`
2. Increase nginx timeout
3. Verify disk space: `df -h`

### Memory Issues

**Error**: Out of memory during processing

**Solution**:
1. Process smaller batches
2. Increase Docker memory limit
3. Reduce `BATCH_SIZE` in `database_service.py`

## Monitoring

### View Logs

**Docker**:
```bash
docker-compose logs -f app
```

**Local**:
```bash
tail -f app.log
```

### Monitor Database

```bash
# Connection count
psql -U postgres -d lex_uz_db -c "SELECT count(*) FROM pg_stat_activity;"

# Table sizes
psql -U postgres -d lex_uz_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public';
"
```

### Check System Resources

```bash
# CPU and Memory
top

# Disk space
df -h

# Docker stats
docker stats
```

## Getting Help

1. **Check logs**: Most errors are logged with detailed messages
2. **Review README**: Comprehensive guide with examples
3. **Test with small files first**: Verify setup before large uploads
4. **Check GitHub issues**: Search for similar problems

## Next Steps

After successful setup:

1. ✅ Upload your first batch of documents
2. ✅ Verify data in database
3. ✅ Set up automated backups
4. ✅ Configure monitoring
5. ✅ Plan your data migration strategy

Congratulations! Your bulk document import system is ready to handle large-scale uploads. 🎉
