# RAG System Improvements

## 🎯 Problem Solved

**Before:** The AI was NOT using your dataset - it always returned `documents_found: 0` and generated responses from its own knowledge instead of your 32,073 legal documents.

**After:** The AI now properly searches your database, finds relevant documents, and returns responses WITH LINKS to source documents.

## 🔧 Key Changes

### 1. **Intelligent Keyword Extraction** (NEW!)

The system now uses AI to extract search keywords from natural language questions.

**Before:**
```
User: "prokratura tizimi haqida malumot ber"
Search: "prokratura tizimi haqida malumot ber" (exact phrase)
Result: No matches ❌
```

**After:**
```
User: "prokratura tizimi haqida malumot ber"
AI extracts: ["prokratura", "prokuratura", "tizim"]
Search: Using these keywords
Result: Finds documents about прокуратура ✅
```

### 2. **Improved Search Algorithm**

- Searches across: title, doc_type, category, number
- Scores results based on keyword relevance
- Handles both Russian and Uzbek keywords
- Removes common words (haqida, о, в, etc.)

### 3. **Complete RAG Flow**

```
User Message
    ↓
1. Detect Language (ru/uz)
    ↓
2. Extract Keywords (using AI)
    ↓
3. Search Metadata (score and rank)
    ↓
4. Get Document IDs from Links
    ↓
5. Fetch Full Content from ru_documents/uz_documents
    ↓
6. Build Context (metadata + content)
    ↓
7. Send to AI with Context
    ↓
8. Return Response + Links
```

### 4. **Environment Variables - No Hardcoded Values**

All configuration now loaded from `.env`:

**Database Config (`app/config/database.py`):**
```python
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "lexuz")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "40"))
```

**AI Config (`app/services/ai_service.py`):**
```python
self.emb_url = os.getenv("EMB_URL", "").strip('"')
self.llm_url = os.getenv("LLM_URL", "").strip('"')
self.api_key = os.getenv("API_KEY", "").strip('"')
self.model_name = os.getenv("MODEL_NAME", "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8").strip('"')
```

## 📊 Response Format (Enhanced)

```json
{
  "response": "AI response based on YOUR documents",
  "language": "uz",
  "source": "dataset",  // ← "dataset" or "ai_knowledge"
  "keywords_used": ["prokratura", "tizim"],  // ← Keywords extracted
  "documents_found": 2,  // ← Number of documents used
  "metadata": [
    {
      "title": "О прокуратуре Республики Узбекистан",
      "doc_type": "Закон",
      "number": "ЗРУ-107",
      "date": "1995-06-12",
      "link_rus": "https://lex.uz/ru/docs/7630588",
      "link_uz_latin": "https://lex.uz/docs/7630588",
      "link_uz_cyrillic": "https://lex.uz/uz/docs/7630588"
    }
  ]
}
```

## 🎨 Features

### Source Indicator

- `"source": "dataset"` - Response from YOUR documents ✅
- `"source": "ai_knowledge"` - Response from AI's training (no docs found) ⚠️
- `"source": "error"` - An error occurred ❌

### Keywords Visibility

- See which keywords were extracted: `"keywords_used": ["prokratura", "tizim"]`
- Debug why documents were/weren't found
- Improve search by understanding keyword extraction

### Document Links

Every response that uses your dataset includes:
- Direct links to lex.uz documents
- Available in Russian, Uzbek Latin, and Uzbek Cyrillic
- Verification that AI is using YOUR data

## 🧪 Testing

### Test 1: Ask about Prokuratura

```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "prokratura tizimi haqida malumot ber"}'
```

**Expected:**
- `"source": "dataset"`
- `"documents_found": 2+`
- Links to documents in metadata array

### Test 2: Check Keywords

Look at the response to see which keywords were extracted:
```json
{
  "keywords_used": ["prokratura", "prokuratura", "tizim", "sistema"]
}
```

### Test 3: Verify Source

If `"source": "ai_knowledge"`:
- Check if metadata table has relevant documents
- Look at `"keywords_used"` to see if extraction worked
- Metadata might not have matching titles

## 🔍 Troubleshooting

### Still Getting `documents_found: 0`?

**Check 1: Is metadata uploaded?**
```bash
curl http://localhost:8000/api/metadata/stats
```
Should show `"total_documents": 32073`

**Check 2: What keywords were extracted?**
Look at `"keywords_used"` in the response

**Check 3: Do document IDs match?**
- Metadata links contain IDs like: `https://lex.uz/ru/docs/7630588`
- Document files should be named like: `-7630588.doc`
- Check with:
```bash
curl http://localhost:8000/api/upload/stats
```

**Check 4: Search manually**
```bash
curl http://localhost:8000/api/metadata/search?query=прокуратура
```

## 📝 Files Changed

1. **`app/services/rag_service.py`** - Complete rewrite
   - Added `extract_search_keywords()` - Uses AI to extract keywords
   - Improved `search_metadata()` - Keyword-based search with scoring
   - Enhanced `chat()` - Better context building
   - Added logging throughout

2. **`app/config/database.py`** - Fixed .env loading
   - Now reads DB_USER, DB_PASSWORD, etc. from .env
   - No hardcoded database URLs
   - Pool sizes configurable

3. **`app/services/ai_service.py`** - Already correct
   - All values from .env
   - No hardcoded URLs or keys

## 🚀 Next Steps

1. **Restart server** to load new code
2. **Test with real questions** about your legal documents
3. **Check logs** to see keyword extraction and search results
4. **Upload Excel metadata** if you haven't already

## 💡 Tips

- Use specific terms in questions (e.g., "Qonun 107" instead of just "qonun")
- Check `keywords_used` in response to understand search
- If too many results, be more specific
- If no results, try different phrasing

## ⚙️ Configuration

All settings in `.env`:

```bash
# Database
DB_NAME=lexuz
DB_USER=postgres
DB_PASSWORD=2005
DB_HOST=localhost
DB_PORT=5432

# AI Service
MODEL_NAME=Qwen/Qwen3-Next-80B-A3B-Instruct-FP8
API_KEY=5df1454b1e95b2648fa402e744
EMB_URL=https://p950-w002-runai-r01-p950.runai-inference.dc.uz/v1/embeddings
LLM_URL=https://p950-w003-runai-r01-p950.runai-inference.dc.uz/v1/chat/completions
```

No hardcoded values anywhere in the code! 🎉
