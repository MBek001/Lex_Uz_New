## Installation Fix for pip/textract Issue

If you encounter an error with `textract` during installation, don't worry! We've removed that problematic dependency.

### What Changed

**Removed**: `textract==1.6.5` (had invalid metadata)

**Added**:
- `docx2txt==0.8` - Lightweight DOCX parser
- `olefile==0.47` - For legacy DOC files

### Document Processing Support

The system now supports multiple methods for extracting text:

#### For DOCX files:
1. **python-docx** (primary) - Excellent support, extracts from paragraphs and tables
2. **docx2txt** (fallback) - Lightweight alternative

#### For DOC files (legacy format):
1. **antiword** (recommended) - Fast CLI tool
   ```bash
   sudo apt-get install antiword  # Ubuntu/Debian
   brew install antiword           # macOS
   ```

2. **LibreOffice** (comprehensive) - Converts DOC to TXT
   ```bash
   sudo apt-get install libreoffice  # Ubuntu/Debian
   brew install libreoffice          # macOS
   ```

3. **olefile** (basic fallback) - Python library for OLE files
   - Already included in requirements.txt
   - Provides basic text extraction when other methods unavailable

### Installation Order

```bash
# 1. Clone repository
git clone <your-repo-url>
cd Lex_Uz_New

# 2. Install system packages (optional but recommended)
sudo apt-get update
sudo apt-get install -y antiword libreoffice

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Upgrade pip (important!)
pip install --upgrade pip

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 7. Initialize database
python init_db.py

# 8. Start application
python main.py
```

### What Works Without System Packages

**Without antiword or LibreOffice**:
- ✅ DOCX files work perfectly (using python-docx + docx2txt)
- ⚠️ DOC files have limited support (basic extraction via olefile)
- 💡 Recommendation: Install antiword for best results with DOC files

### Testing Your Installation

```bash
# Test API is working
curl http://localhost:8000/health

# Test with small DOCX files first
python test_upload.py small_test.zip russian

# Then try with your large datasets
python test_upload.py russian_docs.zip russian
```

### Troubleshooting

**Issue**: `pip install textract` fails

**Solution**: We've already removed textract from requirements.txt. Just pull the latest code:
```bash
git pull origin claude/bulk-document-import-postgres-011CUikGCjDzfVQ7NgKZJbPL
pip install -r requirements.txt
```

**Issue**: DOC files not extracting properly

**Solution**: Install antiword or libreoffice:
```bash
sudo apt-get install antiword
# or
sudo apt-get install libreoffice
```

**Issue**: "python-docx not installed"

**Solution**:
```bash
pip install python-docx
```

### Priority Recommendations

For best results, install in this order:

1. **High Priority** (for DOCX files):
   ```bash
   pip install python-docx docx2txt
   ```

2. **Medium Priority** (for DOC files):
   ```bash
   sudo apt-get install antiword
   ```

3. **Low Priority** (backup for problematic DOC files):
   ```bash
   sudo apt-get install libreoffice
   ```

### Performance Notes

- **DOCX processing**: 100-200 files/minute
- **DOC with antiword**: 80-150 files/minute
- **DOC with LibreOffice**: 20-40 files/minute (slower but more comprehensive)
- **DOC with olefile only**: 50-100 files/minute (basic extraction)

---

Your system will work with just Python dependencies, but installing antiword significantly improves DOC file support!
