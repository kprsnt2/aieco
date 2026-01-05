# 🚀 Quick Start Guide

Get AIEco running in under 5 minutes!

---

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/aieco.git
cd aieco
```

## Step 2: Deploy

```bash
python deploy.py
```

**What happens:**
1. 🔍 Detects your GPU hardware
2. 📦 Installs dependencies
3. 🧠 Downloads and starts model server
4. 🔧 Starts FastAPI backend

## Step 3: Use It!

### Option A: Web Chat

Open [http://localhost:3000](http://localhost:3000)

### Option B: API

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4.7", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Option C: Python SDK

```python
from aieco import AIEcoClient

client = AIEcoClient()
response = client.chat("Write a Python function to sort a list")
print(response)
```

### Option D: CLI (OpenCode/Aider)

```bash
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="sk-local"

# Now use your favorite CLI!
opencode
aider
```

---

## 🎉 You're Done!

**Next Steps:**

1. 📊 Check the [Dashboard](http://localhost:3001)
2. 📚 Read [docs/DOCUMENTATION.md](DOCUMENTATION.md)
3. 🛠️ Explore [Skills](../skills/)
4. 🤖 Try [Agents](DOCUMENTATION.md#3-google-adk-agents)

---

## Quick Commands

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/v1/models

# List skills
curl http://localhost:8080/api/v1/skills

# Stop everything
pkill -f vllm
pkill -f uvicorn
```

---

## Hardware Requirements

| Setup | Min VRAM | Model |
|-------|----------|-------|
| Cloud (best) | 768GB+ | GLM-4.7 358B |
| Gaming PC | 24GB | Qwen 2.5 32B |
| Laptop | 8GB | Qwen 2.5 7B |
| CPU only | 16GB RAM | Phi-3 Mini |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No GPU detected | Install CUDA or ROCm drivers |
| Out of memory | Use `python deploy.py --local` |
| Connection refused | Wait for model to load (~2-5 min) |
| Slow inference | Enable prefix caching |

---

*Need help? Open an [issue](https://github.com/yourusername/aieco/issues)!*
