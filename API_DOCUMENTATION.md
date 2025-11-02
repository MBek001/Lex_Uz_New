# API Documentation for Frontend Development

Base URL: `http://localhost:8000` (or your server URL)

---

## 📚 Table of Contents

1. [Document Upload APIs](#1-document-upload-apis)
2. [Metadata Management APIs](#2-metadata-management-apis)
3. [AI Chat API](#3-ai-chat-api)
4. [Statistics APIs](#4-statistics-apis)

---

## 1. Document Upload APIs

### 1.1 Upload Russian Documents

**Endpoint:** `POST /api/upload/russian`

**Description:** Upload a ZIP file containing Russian DOC/DOCX files

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with file

**Request Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/upload/russian" \
  -F "file=@/path/to/russian_documents.zip"
```

**Request Example (JavaScript/Axios):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

axios.post('http://localhost:8000/api/upload/russian', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

**Request Example (JavaScript/Fetch):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/upload/russian', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error(error));
```

**Response (Success):**
```json
{
  "message": "Successfully uploaded and processed 1523 Russian documents",
  "total_documents": 1523,
  "successful": 1520,
  "failed": 3
}
```

**Response Fields:**
- `message` (string): Success message
- `total_documents` (integer): Total number of documents in ZIP
- `successful` (integer): Number of successfully processed documents
- `failed` (integer): Number of failed documents

**Status Codes:**
- `200 OK`: Upload successful
- `400 Bad Request`: Invalid file format or missing file
- `500 Internal Server Error`: Processing error

---

### 1.2 Upload Uzbek Documents

**Endpoint:** `POST /api/upload/uzbek`

**Description:** Upload a ZIP file containing Uzbek DOC/DOCX files

**Request:** Same format as Russian documents upload

**Response:** Same format as Russian documents upload

---

## 2. Metadata Management APIs

### 2.1 Upload Excel Metadata

**Endpoint:** `POST /api/metadata/upload/excel`

**Description:** Upload Excel file with document metadata

**Required Excel Columns:**
- `doc_type`: Document type (e.g., "Qonun", "Farmon")
- `registration_date`: Registration date
- `number`: Document number
- `effective_date`: Effective date
- `link_rus`: Russian language link
- `link_uz_latin`: Uzbek Latin link
- `link_uz_cyrillic`: Uzbek Cyrillic link
- `status`: Document status ("0" = active, "1" = inactive)
- `title`: Document title
- `category`: Document category

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Excel file (.xlsx or .xls)

**Request Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/metadata/upload/excel" \
  -F "file=@/path/to/metadata.xlsx"
```

**Request Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', excelFile);

fetch('http://localhost:8000/api/metadata/upload/excel', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error(error));
```

**Response (Success):**
```json
{
  "message": "Successfully uploaded 5420 metadata records",
  "total_records": 5420,
  "successful": 5420,
  "failed": 0,
  "errors": []
}
```

**Response Fields:**
- `message` (string): Success message
- `total_records` (integer): Total records in Excel
- `successful` (integer): Successfully inserted records
- `failed` (integer): Failed records
- `errors` (array): List of error messages (if any)

**Status Codes:**
- `200 OK`: Upload successful
- `400 Bad Request`: Invalid file format
- `500 Internal Server Error`: Processing error

---

### 2.2 Search Metadata

**Endpoint:** `GET /api/metadata/search`

**Description:** Search document metadata by query

**Request:**
- Method: `GET`
- Query Parameters:
  - `q` (required): Search query string
  - `limit` (optional): Maximum results (default: 10)

**Request Example (cURL):**
```bash
curl "http://localhost:8000/api/metadata/search?q=prokurorlik&limit=5"
```

**Request Example (JavaScript):**
```javascript
const query = 'prokurorlik';
const limit = 5;

fetch(`http://localhost:8000/api/metadata/search?q=${encodeURIComponent(query)}&limit=${limit}`)
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

**Response (Success):**
```json
{
  "query": "prokurorlik",
  "results_count": 3,
  "results": [
    {
      "id": 1234,
      "doc_type": "Qonun",
      "registration_date": "2023-12-14",
      "number": "ORQ-940",
      "effective_date": "2024-01-01",
      "link_rus": "https://lex.uz/ru/docs/7630588",
      "link_uz_latin": "https://lex.uz/docs/7630588",
      "link_uz_cyrillic": "https://lex.uz/uz/docs/7630588",
      "status": "0",
      "title": "O'zbekiston Respublikasi Prokurorlik to'g'risida qonun",
      "category": "Huquq tizimi"
    }
  ]
}
```

**Response Fields:**
- `query` (string): The search query used
- `results_count` (integer): Number of results found
- `results` (array): Array of metadata objects

**Status Codes:**
- `200 OK`: Search successful
- `400 Bad Request`: Missing query parameter

---

### 2.3 Get Metadata Statistics

**Endpoint:** `GET /api/metadata/stats`

**Description:** Get statistics about metadata records

**Request:**
- Method: `GET`
- No parameters required

**Request Example (cURL):**
```bash
curl "http://localhost:8000/api/metadata/stats"
```

**Request Example (JavaScript):**
```javascript
fetch('http://localhost:8000/api/metadata/stats')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

**Response (Success):**
```json
{
  "total_metadata": 5420,
  "by_doc_type": {
    "Qonun": 1234,
    "Farmon": 856,
    "Qaror": 2145,
    "O'zgartirishlar": 1185
  },
  "by_status": {
    "active": 4890,
    "inactive": 530
  },
  "by_category": {
    "Huquq tizimi": 345,
    "Soliq": 678,
    "Fuqarolik huquqi": 890
  }
}
```

**Response Fields:**
- `total_metadata` (integer): Total metadata records
- `by_doc_type` (object): Count by document type
- `by_status` (object): Count by status (active/inactive)
- `by_category` (object): Count by category

**Status Codes:**
- `200 OK`: Success

---

## 3. AI Chat API

### 3.1 Send Chat Message

**Endpoint:** `POST /api/chat/message`

**Description:** Send a message to AI and get response with RAG (Retrieval-Augmented Generation)

**How it works:**
1. Detects message language (Russian/Uzbek)
2. Searches metadata for relevant documents
3. Retrieves full document content
4. Sends context + message to AI
5. Returns AI response with document links

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body: JSON object

**Request Body Schema:**
```typescript
{
  message: string;              // Required: User's message/question
  conversation_history?: Array<{  // Optional: Previous conversation
    role: "user" | "assistant";
    content: string;
  }>;
}
```

**Request Example (Simple Message):**
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "prokurorlik tizimi haqida malumot ber"
  }'
```

**Request Example (With Conversation History):**
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "va sudlar haqida-chi?",
    "conversation_history": [
      {"role": "user", "content": "prokurorlik tizimi haqida malumot ber"},
      {"role": "assistant", "content": "Prokurorlik tizimi..."}
    ]
  }'
```

**Request Example (JavaScript - Simple):**
```javascript
const message = "prokurorlik tizimi haqida malumot ber";

fetch('http://localhost:8000/api/chat/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ message })
})
.then(response => response.json())
.then(data => {
  console.log('AI Response:', data.response);
  console.log('Source:', data.source);
  console.log('Documents:', data.metadata);
})
.catch(error => console.error(error));
```

**Request Example (JavaScript - With History):**
```javascript
const conversationHistory = [
  { role: "user", content: "prokurorlik tizimi haqida malumot ber" },
  { role: "assistant", content: "Prokurorlik tizimi..." }
];

fetch('http://localhost:8000/api/chat/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "va sudlar haqida-chi?",
    conversation_history: conversationHistory
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error(error));
```

**Request Example (React Component):**
```jsx
import { useState } from 'react';

function ChatComponent() {
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]);
  const [response, setResponse] = useState(null);

  const sendMessage = async () => {
    const res = await fetch('http://localhost:8000/api/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_history: history
      })
    });

    const data = await res.json();
    setResponse(data);

    // Add to history
    setHistory([
      ...history,
      { role: 'user', content: message },
      { role: 'assistant', content: data.response }
    ]);
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <button onClick={sendMessage}>Send</button>

      {response && (
        <div>
          <p>Source: {response.source}</p>
          <p>{response.response}</p>
          {response.metadata.map((doc, i) => (
            <a key={i} href={doc.link_uz_latin}>{doc.title}</a>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Response (From Dataset):**
```json
{
  "response": "O'zbekistonda prokurorlik tizimi - davlat hukumatining mustaqil organlaridan biri bo'lib...",
  "language": "uz",
  "source": "dataset",
  "documents_found": 2,
  "metadata": [
    {
      "title": "O'zbekiston Respublikasi Prokurorlik to'g'risida qonun",
      "doc_type": "Qonun",
      "number": "ORQ-940",
      "date": "2023-12-14",
      "status": "0",
      "category": "Huquq tizimi",
      "link_rus": "https://lex.uz/ru/docs/7630588",
      "link_uz_latin": "https://lex.uz/docs/7630588",
      "link_uz_cyrillic": "https://lex.uz/uz/docs/7630588"
    },
    {
      "title": "Prokurorlik organlari faoliyati to'g'risida",
      "doc_type": "Farmon",
      "number": "PF-234",
      "date": "2023-06-10",
      "status": "0",
      "category": "Huquq tizimi",
      "link_rus": "https://lex.uz/ru/docs/7645123",
      "link_uz_latin": "https://lex.uz/docs/7645123",
      "link_uz_cyrillic": "https://lex.uz/uz/docs/7645123"
    }
  ]
}
```

**Response (From AI Knowledge):**
```json
{
  "response": "Prokurorlik tizimi - bu davlat organlaridan biri...",
  "language": "uz",
  "source": "ai_knowledge",
  "documents_found": 0,
  "metadata": []
}
```

**Response Fields:**
- `response` (string): AI's answer to the user's question
- `language` (string): Detected language ("ru" or "uz")
- `source` (string): Source of response
  - `"dataset"`: Response based on your uploaded documents
  - `"ai_knowledge"`: Response from AI's training data
  - `"error"`: An error occurred
- `documents_found` (integer): Number of documents used for response
- `metadata` (array): Array of document metadata objects (with links)

**Understanding the Response:**

**When `source = "dataset"`:**
- ✅ Response is based on YOUR documents
- ✅ `metadata` array contains the documents used
- ✅ Each document has links you can display to user
- ✅ Response is accurate to your legal documents

**When `source = "ai_knowledge"`:**
- ⚠️ Response is from AI's general knowledge
- ⚠️ NOT from your specific documents
- ⚠️ May be correct but not verified against your data
- ⚠️ Happens when: metadata not uploaded OR no matching documents found

**Status Codes:**
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request body
- `500 Internal Server Error`: AI service error

---

## 4. Statistics APIs

### 4.1 Get Document Upload Statistics

**Endpoint:** `GET /api/upload/stats`

**Description:** Get statistics about uploaded documents

**Request:**
- Method: `GET`
- No parameters required

**Request Example (cURL):**
```bash
curl "http://localhost:8000/api/upload/stats"
```

**Request Example (JavaScript):**
```javascript
fetch('http://localhost:8000/api/upload/stats')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

**Response (Success):**
```json
{
  "russian_documents": 16025,
  "uzbek_documents": 16014,
  "total_documents": 32039,
  "database_size_mb": 1547.8
}
```

**Response Fields:**
- `russian_documents` (integer): Number of Russian documents
- `uzbek_documents` (integer): Number of Uzbek documents
- `total_documents` (integer): Total documents in database
- `database_size_mb` (float): Database size in megabytes

**Status Codes:**
- `200 OK`: Success

---

## 📋 Common Response Patterns

### Error Response Format

All APIs return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example Error Responses:**

**400 Bad Request:**
```json
{
  "detail": "No file provided"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Database connection failed"
}
```

---

## 🔐 Authentication

**Current Status:** No authentication required

**Future Implementation:** If you add authentication later, all requests will need:
```
Authorization: Bearer YOUR_TOKEN
```

---

## 🌐 CORS Configuration

If your frontend is on a different domain/port, ensure CORS is enabled on the backend.

**Example Frontend on Different Port:**
```javascript
// Frontend on http://localhost:3000
// Backend on http://localhost:8000

fetch('http://localhost:8000/api/chat/message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ message: 'test' })
})
```

---

## 📱 Example Frontend Workflows

### Workflow 1: Complete Chat Interface

```javascript
class ChatService {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.history = [];
  }

  async sendMessage(message) {
    const response = await fetch(`${this.baseUrl}/api/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_history: this.history
      })
    });

    const data = await response.json();

    // Update history
    this.history.push({ role: 'user', content: message });
    this.history.push({ role: 'assistant', content: data.response });

    return data;
  }

  clearHistory() {
    this.history = [];
  }
}

// Usage
const chat = new ChatService();
const response = await chat.sendMessage('prokurorlik haqida');
console.log(response.response);
console.log('Documents used:', response.documents_found);
```

### Workflow 2: Document Upload with Progress

```javascript
async function uploadDocuments(file, language) {
  const formData = new FormData();
  formData.append('file', file);

  const endpoint = language === 'ru'
    ? '/api/upload/russian'
    : '/api/upload/uzbek';

  const response = await fetch(`http://localhost:8000${endpoint}`, {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

// Usage
const fileInput = document.getElementById('file-input');
const result = await uploadDocuments(fileInput.files[0], 'uz');
console.log(`Uploaded ${result.successful} documents`);
```

### Workflow 3: Search and Display

```javascript
async function searchDocuments(query) {
  const response = await fetch(
    `http://localhost:8000/api/metadata/search?q=${encodeURIComponent(query)}&limit=10`
  );
  return await response.json();
}

async function displayResults(query) {
  const data = await searchDocuments(query);

  data.results.forEach(doc => {
    console.log(`${doc.title} - ${doc.link_uz_latin}`);
  });
}
```

---

## 🎯 Quick Reference

| API | Method | Purpose |
|-----|--------|---------|
| `/api/upload/russian` | POST | Upload Russian documents ZIP |
| `/api/upload/uzbek` | POST | Upload Uzbek documents ZIP |
| `/api/upload/stats` | GET | Get document statistics |
| `/api/metadata/upload/excel` | POST | Upload metadata Excel file |
| `/api/metadata/search` | GET | Search metadata |
| `/api/metadata/stats` | GET | Get metadata statistics |
| `/api/chat/message` | POST | Send message to AI chat |

---

## ✅ Testing Checklist for Frontend Developers

- [ ] Can upload Russian documents
- [ ] Can upload Uzbek documents
- [ ] Can upload Excel metadata
- [ ] Can search metadata
- [ ] Can send simple chat message
- [ ] Can send chat message with history
- [ ] Can display document links from chat response
- [ ] Can distinguish between `dataset` and `ai_knowledge` responses
- [ ] Can handle error responses properly
- [ ] Can display statistics

---

## 📞 Need Help?

1. Check that backend is running: `http://localhost:8000/docs`
2. View interactive API docs (Swagger UI): `http://localhost:8000/docs`
3. View alternative API docs (ReDoc): `http://localhost:8000/redoc`

---

**Last Updated:** 2025-11-02
**API Version:** 1.0
