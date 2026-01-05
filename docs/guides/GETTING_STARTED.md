# Getting Started with AIEco

> From zero to production in 15 minutes

---

## What is AIEco?

AIEco is a **self-hosted AI platform** that gives you:

- 🧠 **Frontier-class AI models** (GLM-4.7 358B, MiniMax M2.1)
- 📏 **2M token context** (10x more than Claude or GPT-4)
- 🔒 **100% data privacy** (runs on your hardware)
- 💰 **90%+ cost savings** vs commercial APIs
- 🔌 **OpenAI-compatible API** (drop-in replacement)

---

## Prerequisites

Before you begin, ensure you have:

- [ ] **Python 3.10+** installed
- [ ] **Git** installed
- [ ] **GPU access** (cloud or local):
  - Cloud: AWS, GCP, Azure, SF Compute, or IndiaAI
  - Local: NVIDIA GPU (8GB+ VRAM) or AMD GPU

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/aieco.git
cd aieco
```

---

## Step 2: Verify Setup (Optional)

Run the pre-flight check to ensure everything is ready:

```bash
python preflight.py
```

This checks:
- ✅ Python version
- ✅ Required files
- ✅ Disk space
- ✅ Dependencies

---

## Step 3: Deploy

### Option A: One-Click Deploy (Recommended)

```bash
python deploy.py
```

This will:
1. Detect your GPU hardware
2. Select the optimal model
3. Install dependencies
4. Start the model server

### Option B: Manual Deploy

```bash
# Start model server
./model-server/multi-model-8x.sh

# In another terminal, start backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8080
```

---

## Step 4: Verify It's Working

### Test the API

```bash
curl http://localhost:8000/v1/models
```

Expected response:
```json
{
  "object": "list",
  "data": [
    {"id": "glm-4.7", "object": "model", ...}
  ]
}
```

### Send your first message

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## Step 5: Use the API

### Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-local",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

### JavaScript

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-local',
  baseURL: 'http://localhost:8000/v1'
});

const response = await client.chat.completions.create({
  model: 'glm-4.7',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

### cURL

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-local" \
  -d '{"model": "glm-4.7", "messages": [{"role": "user", "content": "Hello!"}]}'
```

---

## Common Use Cases

### 1. Coding Assistant

```python
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "system", "content": "You are an expert programmer."},
        {"role": "user", "content": "Write a Python function to parse JSON with error handling"}
    ],
    temperature=0.3  # Lower for more precise code
)
```

### 2. Document Analysis (RAG)

```bash
# Upload document
curl -X POST http://localhost:8080/api/v1/rag/upload \
  -F "file=@document.pdf" \
  -F "collection_name=my-docs"

# Query
curl http://localhost:8080/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main points?", "collection_name": "my-docs"}'
```

### 3. Long Context (Analyze Entire Codebase)

```python
# Load entire codebase (~500K tokens)
with open("full_codebase.txt") as f:
    codebase = f.read()

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "system", "content": "You are a code reviewer."},
        {"role": "user", "content": f"Review this codebase:\n\n{codebase}"}
    ],
    max_tokens=8000
)
```

### 4. Streaming for Real-Time UI

```python
stream = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

---

## Next Steps

Now that you're up and running:

| Topic | Guide |
|-------|-------|
| API Reference | [docs/api/API_REFERENCE.md](api/API_REFERENCE.md) |
| Python SDK | [docs/sdk/PYTHON_SDK.md](sdk/PYTHON_SDK.md) |
| JavaScript SDK | [docs/sdk/JAVASCRIPT_SDK.md](sdk/JAVASCRIPT_SDK.md) |
| CLI Integration | [docs/CODING_CLI_SETUP.md](CODING_CLI_SETUP.md) |
| Multi-Model Setup | [docs/MULTI_MODEL_ARCHITECTURE.md](MULTI_MODEL_ARCHITECTURE.md) |
| Cost Analysis | [docs/COST_ANALYSIS.md](COST_ANALYSIS.md) |

---

## Troubleshooting

### Model takes too long to load

This is normal on first run (~5-10 minutes). The model weights are being downloaded (~300-500GB).

### Out of memory error

Try a smaller model:
```bash
python deploy.py --local  # Uses small 7B model
```

### Connection refused

Wait for the model to fully load:
```bash
# Check if loading
tail -f vllm_glm-4.7.log
```

### Need help?

- 📖 [Full Documentation](DOCUMENTATION.md)
- 🐛 [GitHub Issues](https://github.com/yourusername/aieco/issues)

---

*Happy coding! 🚀*
