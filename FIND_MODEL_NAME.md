# Finding the Correct Model Name

If you're getting a 404 error "The model `qwen` does not exist", you need to find the correct model name.

## Method 1: Ask Your AI Service Administrator

Contact whoever provides your AI service and ask:
- "What is the exact model name for chat completions?"
- "What is the exact model name for embeddings?"

## Method 2: Test the Endpoint

Try different common Qwen model names:

```bash
# Test with full model path
curl -X POST https://p950-w003-runai-r01-p950.runai-inference.dc.uz/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'

# If that fails, try:
curl -X POST https://p950-w003-runai-r01-p950.runai-inference.dc.uz/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-72B-Instruct",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'

# Or try listing models:
curl -X GET https://p950-w003-runai-r01-p950.runai-inference.dc.uz/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Common Qwen Model Names

Try these in your `.env`:

```bash
# Option 1: With vendor prefix
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

# Option 2: Without prefix
MODEL_NAME=Qwen2.5-72B-Instruct

# Option 3: Older version
MODEL_NAME=Qwen/Qwen2-7B-Instruct

# Option 4: Just model family
MODEL_NAME=qwen2.5

# Option 5: Simple name
MODEL_NAME=qwen-turbo
```

## Common Embedding Models

```bash
# Option 1: BGE
EMBEDDING_MODEL=BAAI/bge-m3

# Option 2: Simple
EMBEDDING_MODEL=bge-m3

# Option 3: Text embedding
EMBEDDING_MODEL=text-embedding-ada-002
```

## How to Find Out

Run this command to try to list available models:

```bash
curl -X GET https://p950-w003-runai-r01-p950.runai-inference.dc.uz/v1/models \
  -H "Authorization: Bearer 5df1454b1e95b2648fd89d"
```

If it returns a list of models, use the exact name from there!

## After Finding the Correct Name

Update your `.env`:

```bash
MODEL_NAME=TheCorrectModelName
EMBEDDING_MODEL=TheCorrectEmbeddingModel
```

Then restart the server:

```bash
uvicorn main:app --reload
```
