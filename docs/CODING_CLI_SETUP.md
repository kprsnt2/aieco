# 🖥️ AIEco for Coding CLIs

> **2M Context Window** - 10x more than Claude Code or Cursor!

---

## 🎯 Why Context Matters for Coding

When using AI coding assistants (OpenCode, Claude Code, Cursor, Aider), context window is **everything**:

| What Eats Context | Typical Size |
|------------------|--------------|
| System prompt + instructions | 2-5K tokens |
| Conversation history | 10-50K tokens |
| Current file | 1-10K tokens |
| Referenced files | 50-500K tokens |
| Codebase context (RAG) | 100-500K tokens |
| **Total needed** | **200K-1M+ tokens** |

### The Problem with Commercial APIs

| Service | Context | Limitation |
|---------|---------|------------|
| Claude Code | 200K | Can't fit large codebases |
| GPT-4 Turbo | 128K | Even more limited |
| Cursor | 32-128K | Context compression needed |
| Gemini 2.5 | 1M | API rate limits |

### AIEco Solution

| Config | Context | Use Case |
|--------|---------|----------|
| Standard | 1M | Most projects |
| **Max Context** | **2M** | Enterprise codebases |

---

## 🚀 Context Window Options (8x MI300X)

### Option 1: Max Context (2M tokens)
Best for: Large monorepos, enterprise codebases

```bash
# Use all 1.5TB for maximum context
./model-server/max-context-coding.sh

# Results in:
# - Model: GLM-4.7 358B
# - Context: 2,097,152 tokens (2M)
# - VRAM: Model ~400GB + KV Cache ~1100GB
```

### Option 2: Balanced (1M tokens + MiniMax)
Best for: Mixed workloads, faster response

```bash
# Run both models
./model-server/multi-model-8x.sh

# Results in:
# - GLM-4.7: 1M context (coding)
# - MiniMax: 200K context (fast chat)
```

### Option 3: Ultra Fast (128K tokens)
Best for: Quick iterations, testing

```bash
MAX_CONTEXT=131072 ./model-server/max-context-coding.sh

# Results in:
# - Faster prefill
# - Lower latency
# - Similar to Cursor experience
```

---

## 📊 Context Comparison Chart

```
Context Window (tokens)
│
│ AIEco 2M     ████████████████████████████████████████ 2,097,152
│ AIEco 1M     ████████████████████          1,048,576
│ Gemini 2.5   ████████████████████          1,000,000
│ Claude Code  ████                            200,000
│ GPT-4 Turbo  ███                             128,000
│ Cursor       █                                32,000
│
└──────────────────────────────────────────────────────
```

---

## 🔧 OpenCode Integration

Configure OpenCode to use AIEco:

```bash
# Set environment variables
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="sk-local-aieco"
export OPENAI_MODEL="glm-4.7-max"

# Or edit ~/.opencode/config.yaml
provider: openai-compatible
base_url: http://localhost:8000/v1
model: glm-4.7-max
api_key: sk-local-aieco
```

### OpenCode Config File

```yaml
# ~/.opencode/config.yaml
providers:
  aieco:
    type: openai-compatible
    base_url: http://localhost:8000/v1
    api_key: sk-local
    models:
      - glm-4.7-max

default_provider: aieco
default_model: glm-4.7-max

# Context settings
max_context_tokens: 2000000  # 2M!
```

---

## 🔧 Aider Integration

```bash
# Run Aider with AIEco
aider --model openai/glm-4.7-max \
      --openai-api-base http://localhost:8000/v1 \
      --openai-api-key sk-local
```

### Aider Config

```yaml
# ~/.aider.conf.yml
model: openai/glm-4.7-max
openai-api-base: http://localhost:8000/v1
openai-api-key: sk-local
```

---

## 🔧 Continue.dev Integration

```json
// ~/.continue/config.json
{
  "models": [
    {
      "title": "AIEco GLM-4.7 (2M Context)",
      "provider": "openai",
      "model": "glm-4.7-max",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "sk-local"
    }
  ],
  "tabAutocompleteModel": {
    "title": "AIEco Fast",
    "provider": "openai",
    "model": "glm-4.7-max",
    "apiBase": "http://localhost:8000/v1"
  }
}
```

---

## 🔧 Cursor-Like Experience

Create a Cursor-like experience with AIEco:

### Features Comparison

| Feature | Cursor | AIEco |
|---------|--------|-------|
| Context window | 32-128K | **2M** |
| Codebase indexing | ✅ | ✅ (RAG pipeline) |
| Multi-file edit | ✅ | ✅ (MCP tools) |
| Privacy | ❌ Cloud | ✅ Local |
| Cost | $20-40/mo | Self-hosted |

### Setup

```bash
# 1. Start AIEco backend
cd aieco && docker-compose up -d

# 2. Start max context model
./model-server/max-context-coding.sh

# 3. Use with your favorite editor
#    - VSCode + Continue extension
#    - Neovim + copilot.lua
#    - Emacs + gptel
```

---

## 💡 Pro Tips for Coding

### 1. Use Prefix Caching
System prompts and common instructions are cached:
```python
# First request: Full prefill (slow)
# Subsequent: Cached prefix (fast!)
```

### 2. Chunk Large Files
For files > 100K tokens:
```bash
# Let RAG handle chunking
aieco rag upload giant-codebase.zip
```

### 3. Stream Responses
```bash
# Enable streaming for better UX
stream=true
```

### 4. Batch Similar Requests
Same codebase context = shared KV cache

---

## 📈 Performance Expectations

| Metric | 128K Context | 1M Context | 2M Context |
|--------|--------------|------------|------------|
| Time to First Token | 500ms | 2s | 4s |
| Tokens/sec (decode) | 50 | 45 | 40 |
| Memory per request | 20GB | 150GB | 300GB |
| Concurrent users | 50 | 6 | 3 |

**Trade-off**: Larger context = slower prefill but better code understanding

---

*Last updated: January 2026*
