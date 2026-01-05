# 📖 AIEco Complete Documentation

> Everything you need to use AIEco effectively

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Deployment Options](#deployment-options)
3. [API Reference](#api-reference)
4. [Features](#features)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- GPU (optional, but recommended)

### One-Click Install

```bash
git clone https://github.com/yourusername/aieco.git
cd aieco
python deploy.py
```

That's it! The script will:
1. ✅ Detect your GPU hardware
2. ✅ Choose the optimal model
3. ✅ Install dependencies
4. ✅ Start model servers
5. ✅ Start the backend API

---

## Deployment Options

### Hardware Configuration Matrix

| GPUs | VRAM | Model(s) | Context | Command |
|------|------|----------|---------|---------|
| 8x MI300X | 1.5TB | GLM-4.7 + MiniMax | 2M | `python deploy.py` |
| 4x MI300X | 768GB | GLM-4.7 358B | 1M | `python deploy.py` |
| 1x MI300X | 192GB | Qwen 2.5 72B | 128K | `python deploy.py` |
| RTX 4090 | 24GB | Qwen 2.5 32B | 32K | `python deploy.py` |
| RTX 3060 | 12GB | Qwen 2.5 7B | 8K | `python deploy.py` |
| No GPU | CPU | Phi-3 Mini | 4K | `python deploy.py --local` |

### Manual Model Selection

```bash
# Force specific mode
python deploy.py --local      # Small model for local GPU
python deploy.py --cloud      # Large model for cloud GPU
python deploy.py --dry-run    # Preview without deploying
```

### Docker Deployment

```bash
# Cloud setup (8x MI300X)
docker-compose -f docker/docker-compose.cloud.yml up -d

# Local setup (consumer GPU)  
docker-compose -f docker/docker-compose.local.yml up -d
```

---

## API Reference

### Base URLs

| Service | URL |
|---------|-----|
| Model API | `http://localhost:8000/v1` |
| Model API (Secondary) | `http://localhost:8001/v1` |
| Backend API | `http://localhost:8080` |
| API Documentation | `http://localhost:8080/docs` |

### Authentication

```bash
# Get access token
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}

# Use token
curl http://localhost:8080/api/v1/chat/completions \
  -H "Authorization: Bearer eyJ..."
```

### Chat Completions

```bash
# Basic chat
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'

# Streaming
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

### RAG (Document Q&A)

```bash
# Upload document
curl -X POST http://localhost:8080/api/v1/rag/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  -F "collection_name=my-docs"

# Query
curl -X POST http://localhost:8080/api/v1/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "collection_name": "my-docs",
    "top_k": 5
  }'
```

### Agents

```bash
# List agents
curl http://localhost:8080/api/v1/agents \
  -H "Authorization: Bearer $TOKEN"

# Run agent
curl -X POST http://localhost:8080/api/v1/agents/code/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a Flask REST API"}'
```

### Skills

```bash
# List skills
curl http://localhost:8080/api/v1/skills \
  -H "Authorization: Bearer $TOKEN"

# Activate skill
curl -X POST http://localhost:8080/api/v1/skills/mcp-builder/activate \
  -H "Authorization: Bearer $TOKEN"
```

### MCP Tools

```bash
# List tools
curl http://localhost:8080/api/v1/mcp/tools \
  -H "Authorization: Bearer $TOKEN"

# Execute tool
curl -X POST http://localhost:8080/api/v1/mcp/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "read_file",
    "arguments": {"path": "/path/to/file.py"}
  }'
```

---

## Features

### 1. Multi-Model Serving

Run multiple models simultaneously on 8x MI300X:

| Model | Port | GPUs | Context | Use Case |
|-------|------|------|---------|----------|
| GLM-4.7 358B | 8000 | 0-3 | 1-2M | Coding, reasoning |
| MiniMax M2.1 | 8001 | 4-7 | 200K | Fast chat |

**Intelligent Routing:**
```python
# Router auto-selects best model
response = router.route_request(
    messages=[{"role": "user", "content": "Debug this code"}],
    prefer_speed=False  # Use GLM for quality
)
```

### 2. Anthropic-Style Skills

Skills extend the model's capabilities:

| Skill | Description |
|-------|-------------|
| `mcp-builder` | Create MCP servers |
| `skill-creator` | Create new skills |
| `pdf` | PDF processing |
| `docx` | Word documents |
| `frontend-design` | UI development |
| `code-review` | Code analysis |
| `python-developer` | Python best practices |

**Usage:**
```bash
# List skills
curl http://localhost:8080/api/v1/skills

# Activate for session
curl -X POST http://localhost:8080/api/v1/skills/pdf/activate
```

### 3. Google ADK Agents

Agent types available:

| Agent | Description |
|-------|-------------|
| `LlmAgent` | Single LLM with tools |
| `SequentialAgent` | Run sub-agents in order |
| `ParallelAgent` | Run sub-agents concurrently |
| `LoopAgent` | Repeat until condition |

**Create custom agent:**
```python
from backend.app.services.agents import AgentBuilder

agent = (AgentBuilder("code-helper")
    .with_description("Helps with coding")
    .with_skill("python-developer")
    .with_tool("file", "shell")
    .build())
```

### 4. RAG Pipeline

Full document processing pipeline:

```
Document → Chunking → Embedding → ChromaDB
                                      ↓
Query → Embedding → Similarity Search → Context
                                            ↓
                              LLM → Response
```

**Supported formats:** PDF, DOCX, TXT, MD, HTML, JSON, CSV

### 5. Prompt Caching

90% token savings on repeated context:

```python
# First request: Full processing
# Cached: System prompt + common instructions
# Subsequent: Only process new content

cache.enable(ttl_minutes=60)  # Cache for 1 hour
```

### 6. Security Features

| Feature | Description |
|---------|-------------|
| JWT Auth | Token-based authentication |
| API Keys | For service accounts |
| Rate Limiting | 60 req/min, 100K tokens/min |
| Input Validation | Prompt injection protection |
| Audit Logging | Complete request logs |

### 7. Observability

| Tool | Purpose |
|------|---------|
| Langfuse | LLM tracing |
| Prometheus | Metrics |
| structlog | Structured logging |
| OpenTelemetry | Distributed tracing |

---

## Configuration

### Environment Variables

```bash
# Core
DATABASE_URL=postgresql://localhost/aieco
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key

# Model
VLLM_MODEL=THUDM/glm-4.7-358b-a16b-fp8
TENSOR_PARALLEL_SIZE=4
MAX_MODEL_LEN=2097152

# Optional
LANGFUSE_SECRET_KEY=your-langfuse-key
CHROMA_HOST=localhost
CHROMA_PORT=8100
```

### Model Configuration

Edit `model-server/config.yaml`:

```yaml
models:
  primary:
    hf_id: THUDM/glm-4.7-358b-a16b-fp8
    port: 8000
    gpus: [0, 1, 2, 3]
    max_context: 2097152
    
  secondary:
    hf_id: MiniMaxAI/MiniMax-M2.1
    port: 8001
    gpus: [4, 5, 6, 7]
    max_context: 204800
```

### Backend Configuration

Edit `backend/app/config.py`:

```python
class Settings:
    PROJECT_NAME = "AIEco"
    VERSION = "1.0.0"
    
    # Rate limits
    RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_TOKENS_PER_MINUTE = 100000
    
    # Caching
    CACHE_TTL_MINUTES = 60
```

---

## Troubleshooting

### Common Issues

#### 1. Out of Memory

```
Error: CUDA out of memory
```

**Solutions:**
- Reduce `MAX_MODEL_LEN`
- Use smaller model
- Enable FP8 quantization

```bash
MAX_MODEL_LEN=131072 python deploy.py
```

#### 2. Model Download Fails

```
Error: Connection timeout
```

**Solutions:**
- Set HuggingFace mirror
- Pre-download model

```bash
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download THUDM/glm-4.7-358b-a16b-fp8
```

#### 3. Port Already in Use

```
Error: Address already in use
```

**Solutions:**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

#### 4. ROCm Not Detected

**Solutions:**
```bash
# Install ROCm
sudo apt install rocm-smi

# Verify
rocm-smi --showproductname
```

### Logs

```bash
# Backend logs
tail -f backend/logs/aieco.log

# Model server logs
tail -f /var/log/vllm.log
```

### Health Checks

```bash
# Model server
curl http://localhost:8000/health

# Backend
curl http://localhost:8080/health

# Full system
python scripts/health_check.py
```

---

## Support

- 📝 Issues: [GitHub Issues](https://github.com/yourusername/aieco/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/aieco/discussions)
- 📧 Email: support@your-domain.com

---

*Last updated: January 2026*
