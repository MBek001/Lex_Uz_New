# How to Use the Chat API

## Understanding the Response

### Response Fields

The chat API returns these fields:

```json
{
  "response": "The AI's answer",
  "language": "ru" or "uz",
  "source": "dataset" | "ai_knowledge" | "error",
  "documents_found": 0,
  "metadata": [...]
}
```

**Key Field: `source`**
- `"dataset"` - Response is based on YOUR documents (documents_found > 0)
- `"ai_knowledge"` - Response is from AI's training data (documents_found = 0)
- `"error"` - An error occurred

## Request Format

### Simple Message (Recommended)

```json
{
  "message": "prokratura tizimi haqida malumot ber"
}
```

That's it! Just send your question in the `message` field.

### With Conversation History (Optional)

```json
{
  "message": "prokratura tizimi haqida malumot ber",
  "conversation_history": [
    {"role": "user", "content": "previous user message"},
    {"role": "assistant", "content": "previous AI response"}
  ]
}
```

**Important:** The `"content": "string"` in conversation_history is just a placeholder.
- Either **remove it completely** (recommended)
- Or replace `"string"` with actual previous messages

## Example Responses

### 1. Response from YOUR Dataset

When documents are found in your database:

```json
{
  "response": "According to document X...",
  "language": "uz",
  "source": "dataset",  ← FROM YOUR DATA!
  "documents_found": 2,
  "metadata": [
    {
      "title": "O'zbekiston Respublikasi Prokurorlik to'g'risidagi qonun",
      "doc_type": "Qonun",
      "number": "ORQ-940-son",
      "date": "2023-12-14",
      "link_rus": "https://lex.uz/ru/docs/7630588",
      "link_uz_latin": "https://lex.uz/docs/7630588",
      "link_uz_cyrillic": "https://lex.uz/uz/docs/7630588"
    }
  ]
}
```

**How to verify:** Check the `metadata` array for document links!

### 2. Response from AI's Knowledge

When NO documents found in your database:

```json
{
  "response": "Based on general knowledge...",
  "language": "uz",
  "source": "ai_knowledge",  ← NOT from your data
  "documents_found": 0,
  "metadata": []
}
```

**This means:** Either:
- You haven't uploaded Excel metadata yet
- Your search query didn't match any documents
- The matched metadata doesn't have corresponding DOC files

## Next Steps

### Upload Excel Metadata (Required!)

To get responses from YOUR dataset, you must first upload metadata:

```bash
curl -X POST "http://localhost:8000/api/metadata/upload/excel" \
  -F "file=@/path/to/your/metadata.xlsx"
```

Your Excel should have these columns:
- doc_type
- registration_date
- number
- effective_date
- link_rus
- link_uz_latin
- link_uz_cyrillic
- status
- title
- category

### Verify Metadata

Check how many metadata records you have:

```bash
curl http://localhost:8000/api/metadata/stats
```

### Test with Known Document

Try searching for a document you know exists in your metadata:

```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "qonun 940"}'
```

## Troubleshooting

**Q: Why is `documents_found` always 0?**
A: You need to upload Excel metadata first. The system searches metadata to find relevant documents.

**Q: What if metadata is uploaded but still 0 results?**
A: Your search query might not match document titles/types/categories. Try:
- More specific terms (document numbers, exact titles)
- Different keywords
- Check if your metadata has the right content

**Q: Can I see which exact documents were used?**
A: Yes! Check the `metadata` array in the response. It includes links to each document.

**Q: What to put in `conversation_history`?**
A: Only include it if you want multi-turn conversation. Otherwise, omit it completely.
