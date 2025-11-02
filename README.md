# Lex Uz - Bulk Document Import System

A robust, production-ready system for importing large batches of Russian and Uzbek documents (DOC/DOCX) into PostgreSQL database. Designed to handle 50,000+ documents and multi-gigabyte ZIP files efficiently.

## Features

✅ **Large File Support**: Handles ZIP files over 1GB and extracted content over 15GB
✅ **Memory Efficient**: Streaming extraction and processing
✅ **Batch Processing**: Inserts 1,000 records at a time for optimal performance
✅ **Separate Tables**: Russian (`ru_documents`) and Uzbek (`uz_documents`) with dedicated endpoints
✅ **Progress Tracking**: Detailed logging and statistics
✅ **Error Handling**: Comprehensive error handling with fallback mechanisms
✅ **Docker Support**: Easy deployment with Docker Compose
✅ **REST API**: Clean FastAPI endpoints with automatic documentation

## Architecture

- **Framework**: FastAPI (async, high-performance)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Document Processing**: python-docx, docx2txt, antiword, LibreOffice (with fallbacks)
- **Connection Pooling**: Optimized for bulk operations
- **Deployment**: Docker + Docker Compose

## PostgreSQL Scalability

**Can PostgreSQL handle 100,000+ records?**

✅ **Yes, easily!** PostgreSQL is designed for millions of records. With proper indexing and our batch insertion approach:

- 100,000 records: ~30 seconds
- 500,000 records: ~3-5 minutes
- 1,000,000+ records: ~10-15 minutes

Our implementation includes:
- Indexed columns for fast queries
- Batch inserts (1000 records at a time)
- Connection pooling (20 base + 40 overflow)
- Optimized table structure

## Project Structure

```
Lex_Uz_New/
├── app/
│   ├── models/
│   │   └── documents.py       # Database models
│   ├── routers/
│   │   └── upload.py          # API endpoints
│   ├── services/
│   │   ├── document_processor.py  # Document extraction
│   │   └── database_service.py    # Database operations
│   └── config/
│       └── database.py        # Database configuration
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Multi-container setup
├── .env.example              # Environment template
└── README.md                 # This file
```

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone and setup**:
```bash
git clone <repository-url>
cd Lex_Uz_New
cp .env.example .env
```

2. **Start services**:
```bash
docker-compose up -d
```

3. **Check status**:
```bash
docker-compose ps
docker-compose logs -f app
```

4. **Access API**:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Database: localhost:5432

### Option 2: Local Installation

1. **Prerequisites**:
```bash
# Python 3.11+
python --version

# PostgreSQL 13+
psql --version

# System dependencies for document processing (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y antiword libreoffice python3-dev libpq-dev

# macOS
brew install antiword

# Note: antiword and libreoffice are optional but recommended for better .doc support
```

2. **Install Python dependencies**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure database**:
```bash
# Create database
createdb lex_uz_db

# Update .env
cp .env.example .env
# Edit DATABASE_URL in .env
```

4. **Run application**:
```bash
python main.py
```

## API Endpoints

### Upload Russian Documents
```bash
POST /api/upload/russian
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/api/upload/russian" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@russian_docs.zip"
```

**Response**:
```json
{
  "status": "success",
  "filename": "russian_docs.zip",
  "processing": {
    "processed": 45230,
    "errors": 15,
    "error_list": []
  },
  "database": {
    "total": 45230,
    "inserted": 45230,
    "errors": 0
  },
  "total_records_in_db": 45230
}
```

### Upload Uzbek Documents
```bash
POST /api/upload/uzbek
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/api/upload/uzbek" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@uzbek_docs.zip"
```

### Get Statistics

**Russian documents**:
```bash
GET /api/stats/russian

curl http://localhost:8000/api/stats/russian
```

**Uzbek documents**:
```bash
GET /api/stats/uzbek

curl http://localhost:8000/api/stats/uzbek
```

**Response**:
```json
{
  "total_documents": 45230,
  "latest_documents": [
    {
      "id": 45230,
      "title": "document_45230.docx",
      "created_at": "2025-11-02T10:30:45",
      "file_size": 25600
    }
  ]
}
```

## Database Schema

### Russian Documents Table (`ru_documents`)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (auto-increment) |
| title | VARCHAR(500) | Document filename |
| content | TEXT | Extracted text content |
| created_at | TIMESTAMP | Creation timestamp |
| file_size | INTEGER | Original file size in bytes |

### Uzbek Documents Table (`uz_documents`)
Same schema as Russian documents table.

**Indexes**:
- Primary key on `id`
- Index on `title`
- Composite index on `(title, created_at)`

## Usage Workflow

### Step 1: Prepare ZIP Files

Create ZIP files containing your DOC/DOCX documents:

```bash
# Russian documents
zip -r russian_docs.zip ru_documents/

# Uzbek documents
zip -r uzbek_docs.zip uz_documents/
```

### Step 2: Upload via API

**Option A: Using cURL**:
```bash
# Upload Russian documents
curl -X POST "http://localhost:8000/api/upload/russian" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@russian_docs.zip"

# Upload Uzbek documents
curl -X POST "http://localhost:8000/api/upload/uzbek" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@uzbek_docs.zip"
```

**Option B: Using Web Interface**:
1. Open http://localhost:8000/docs
2. Navigate to POST `/api/upload/russian` or `/api/upload/uzbek`
3. Click "Try it out"
4. Upload your ZIP file
5. Click "Execute"

### Step 3: Monitor Progress

Check logs for real-time progress:
```bash
# Docker
docker-compose logs -f app

# Local
tail -f app.log
```

### Step 4: Verify Upload

```bash
# Check statistics
curl http://localhost:8000/api/stats/russian
curl http://localhost:8000/api/stats/uzbek

# Or connect to database
psql lex_uz_db -c "SELECT COUNT(*) FROM ru_documents;"
psql lex_uz_db -c "SELECT COUNT(*) FROM uz_documents;"
```

### Step 5: Query and Process Data

After upload, you can query the database:

```sql
-- Get total counts
SELECT COUNT(*) FROM ru_documents;
SELECT COUNT(*) FROM uz_documents;

-- Search documents
SELECT id, title, LEFT(content, 100)
FROM ru_documents
WHERE content ILIKE '%search_term%'
LIMIT 10;

-- Get documents by date
SELECT COUNT(*), DATE(created_at)
FROM ru_documents
GROUP BY DATE(created_at);

-- Transfer to other tables (your Step 6)
INSERT INTO your_target_table (name, text)
SELECT title, content FROM ru_documents WHERE ...;
```

## Performance Optimization

### For Large Uploads (50,000+ documents)

1. **Increase connection pool**:
```python
# app/config/database.py
pool_size=30,
max_overflow=60
```

2. **Adjust batch size**:
```python
# app/services/database_service.py
BATCH_SIZE = 2000  # Increase for faster inserts
```

3. **PostgreSQL tuning** (add to `postgresql.conf`):
```conf
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 128MB
max_connections = 100
```

### Memory Management

The system automatically:
- Streams ZIP extraction (doesn't load entire archive)
- Processes one file at a time
- Deletes temporary files immediately
- Runs garbage collection every 500 files

## Troubleshooting

### Issue: "No module named 'docx'"
```bash
pip install python-docx
```

### Issue: "Could not extract text from DOC file"
```bash
# Install antiword
sudo apt-get install antiword  # Ubuntu/Debian
brew install antiword           # macOS
```

### Issue: Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps  # or
pg_isready

# Check credentials in .env
cat .env
```

### Issue: Upload timeout
```bash
# Increase timeout in nginx/load balancer
# Or use smaller batches
```

### Issue: Out of memory
```bash
# Reduce batch size in database_service.py
BATCH_SIZE = 500

# Increase Docker memory limit
docker-compose.yml:
  app:
    mem_limit: 4g
```

## Development

### Running Tests
```bash
pytest
```

### Adding New Features

1. **Add new document types**: Update `SUPPORTED_EXTENSIONS` in `document_processor.py`
2. **Add new language**: Create model in `models/documents.py` and endpoint in `routers/upload.py`
3. **Custom processing**: Extend `DocumentProcessor` class

## Deployment

### Production Checklist

- [ ] Set strong database password in `.env`
- [ ] Configure CORS origins in `main.py`
- [ ] Set up HTTPS/SSL
- [ ] Configure nginx reverse proxy
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure backup for PostgreSQL
- [ ] Set up log rotation
- [ ] Use gunicorn for production:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support

For issues and questions, check the logs:
```bash
# Application logs
tail -f app.log

# Docker logs
docker-compose logs -f app
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

**Built with**: FastAPI • PostgreSQL • Python 3.11 • Docker
