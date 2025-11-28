# Quick Start Guide - Fixing "0 Documents Found" Issue

## 🔍 Problem
Your application is running but searches always return 0 documents.

## ✅ Solution
Your database is empty. You need to upload data first.

---

## Step 1: Check Current Database Status

### Option A: Use API endpoint
```bash
curl http://localhost:8000/api/diagnostics
```

### Option B: Use shell script
```bash
./check_db_simple.sh
```

### Expected Output (Empty Database)
```json
{
  "database": {
    "metadata_count": 0,
    "russian_documents": 0,
    "uzbek_documents": 0
  },
  "diagnosis": {
    "ready_for_search": false
  }
}
```

---

## Step 2: Upload Your Data

### 2.1 Upload Metadata (Excel File)
The Excel file should have these columns:
- `doc_type` - Document type (Закон, Указ, etc.)
- `registration_date` - Registration date
- `number` - Document number
- `effective_date` - Effective date
- `link_rus` - Link to Russian version
- `link_uz-latin` - Link to Uzbek Latin
- `link_uz-cyrillic` - Link to Uzbek Cyrillic
- `status` - Status ("0" for active)
- `title` - Document title
- `category` - Document category

```bash
curl -X POST "http://localhost:8000/api/metadata/upload/excel" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/metadata.xlsx"
```

**Response Example:**
```json
{
  "status": "success",
  "filename": "metadata.xlsx",
  "processed": 1500,
  "inserted": 1500,
  "errors": 0,
  "total_in_database": 1500
}
```

### 2.2 Upload Russian Documents (ZIP)
ZIP file should contain .doc or .docx files.
Filenames should match the doc_ids from metadata links.

Example: If metadata link is `https://lex.uz/ru/docs/7630588`, the ZIP should contain a file like `7630588.doc` or `-7630588.doc`.

```bash
curl -X POST "http://localhost:8000/api/upload/russian" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/russian_docs.zip"
```

**Response Example:**
```json
{
  "status": "success",
  "processing": {
    "total_files": 800,
    "processed": 800,
    "errors": 0
  },
  "database": {
    "total": 800,
    "inserted": 800,
    "errors": 0
  },
  "total_records_in_db": 800
}
```

### 2.3 Upload Uzbek Documents (ZIP)
Same as Russian documents, but for Uzbek language.

```bash
curl -X POST "http://localhost:8000/api/upload/uzbek" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/uzbek_docs.zip"
```

---

## Step 3: Verify Data Loaded

```bash
curl http://localhost:8000/api/diagnostics
```

**Expected Output (After Upload):**
```json
{
  "database": {
    "metadata_count": 1500,
    "russian_documents": 800,
    "uzbek_documents": 700,
    "active_metadata": 1450,
    "total_documents": 3000
  },
  "diagnosis": {
    "has_metadata": true,
    "has_documents": true,
    "ready_for_search": true  // ✅ READY!
  }
}
```

---

## Step 4: Test Search

### Russian Query
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "прокуратура"
  }'
```

### Uzbek Query
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "prokuratura haqida"
  }'
```

### Expected Response
```json
{
  "response": "Прокуратура Республики Узбекистан...",
  "language": "ru",
  "documents_found": 3,
  "metadata": [
    {
      "title": "Закон о прокуратуре",
      "doc_type": "Закон",
      "number": "940",
      "link": "https://lex.uz/ru/docs/7630588"
    }
  ]
}
```

If `documents_found` > 0, your system is working! 🎉

---

## Troubleshooting

### Issue: Still Getting 0 Documents

**Check 1: Verify metadata exists**
```bash
curl "http://localhost:8000/api/metadata/search?query=закон"
```

If this returns 0 results, metadata wasn't uploaded correctly.

**Check 2: Verify documents exist**
```bash
curl http://localhost:8000/api/stats/russian
curl http://localhost:8000/api/stats/uzbek
```

**Check 3: Check document matching**
The system matches documents by extracting ID from metadata link and searching in document filenames.

Example flow:
1. Metadata link: `https://lex.uz/ru/docs/7630588`
2. Extracted ID: `7630588`
3. Searches for document with title containing `7630588`
4. Match found: `7630588.doc` or `-7630588.doc`

Make sure your document filenames contain the IDs from metadata links!

---

### Issue: AI Timeout Errors

If you see errors like:
```
[AI TIMEOUT] All 3 attempts failed
```

**Possible causes:**
1. AI service is down or slow
2. API key is invalid
3. Network issues

**Check .env file:**
```bash
# Create .env from .env.example
cp .env.example .env

# Edit with your actual values
nano .env
```

Required variables:
```env
LLM_URL=https://p950-w003-runai-p950.runai-inference.dc.uz/v1/chat/completions
API_KEY=your_actual_api_key_here
MODEL_NAME=Qwen/Qwen3-Next-80B-A3B-Instruct-FP8
```

**Test AI service directly:**
```bash
curl -X POST "$LLM_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 100
  }'
```

If this fails, contact your AI service provider.

---

## Summary Checklist

- [ ] Check database status with `/api/diagnostics`
- [ ] Upload metadata Excel file
- [ ] Upload Russian documents ZIP
- [ ] Upload Uzbek documents ZIP
- [ ] Verify data loaded correctly
- [ ] Test search with sample query
- [ ] Ensure `documents_found` > 0

If all steps complete successfully, your system is ready to use! 🚀
