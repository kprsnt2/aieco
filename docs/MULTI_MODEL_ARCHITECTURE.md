# 🚀 AIEco 8x MI300X Multi-Model Architecture

> **$89.10 AMD Credits** = 5.5+ hours of 8x MI300X (1.5TB VRAM)

---

## 💎 Hardware Configuration

| Spec | Value |
|------|-------|
| **GPUs** | 8x AMD MI300X |
| **VRAM** | 1.5TB (1536GB) total |
| **vCPU** | 160 cores |
| **RAM** | 1920 GB |
| **Boot Disk** | 2 TB NVMe |
| **Scratch** | 40 TB NVMe |
| **Cost** | $15.92/hr ($1.99/GPU) |

---

## 🧠 Multi-Model Setup

With 1.5TB VRAM, we can run **multiple frontier models simultaneously**:

### VRAM Budget

```
┌─────────────────────────────────────────────────────────────────┐
│                    1.5TB VRAM Allocation                         │
├─────────────────────────────────────────────────────────────────┤
│ GLM-4.7 358B (FP8)         │ ████████████████ │ ~400GB (GPUs 0-3)│
│ MiniMax M2.1 229B          │ ██████████       │ ~243GB (GPUs 4-7)│
│ KV Cache + Overhead        │ ██████████████████████ │ ~893GB     │
├─────────────────────────────────────────────────────────────────┤
│ Total Used                 │                  │ 643GB            │
│ Available for Context      │                  │ 893GB            │
└─────────────────────────────────────────────────────────────────┘
```

### Model Comparison

| Model | Parameters | Context | Strengths | Port |
|-------|-----------|---------|-----------|------|
| **GLM-4.7** | 358B (dense) | **1M tokens** | Coding, reasoning, tools | 8000 |
| **MiniMax M2.1** | 229B (MoE, 10B active) | 200K tokens | Fast inference, creative | 8001 |

---

## 🔄 Intelligent Routing

The `ModelRouter` automatically selects the best model:

```python
# Auto-routing based on task type
router = get_model_router()
response = await router.route_request(messages)

# Explicit model selection
response = await router.route_request(messages, model="glm-4.7")
response = await router.route_request(messages, model="minimax")
```

### Routing Rules

| Condition | Routes To |
|-----------|-----------|
| Context > 200K tokens | GLM-4.7 |
| Task: coding/reasoning | GLM-4.7 |
| Task: creative/chat | MiniMax M2.1 |
| Prefer speed | MiniMax M2.1 |
| Default | GLM-4.7 |

---

## 🚀 Starting the Cluster

```bash
# Start multi-model server
./model-server/multi-model-8x.sh

# Or with Docker
docker-compose -f docker/docker-compose.8x.yml up -d
```

### Endpoints

| Model | Endpoint |
|-------|----------|
| GLM-4.7 | `http://localhost:8000/v1` |
| MiniMax M2.1 | `http://localhost:8001/v1` |
| AIEco Router | `http://localhost:8080/api/v1/chat/completions` |

---

## 💰 Cost Analysis (8x MI300X)

### Your Credits

| Credit | Value | Hours | Days (8hr/day) |
|--------|-------|-------|----------------|
| $89.10 | AMD Credits | **5.6 hours** | <1 day |
| +$500 | If you add | 31.4 hours | ~4 days |
| +$1000 | If you add | 62.8 hours | ~8 days |

### Monthly Cost (24/7)

```
$15.92/hr × 24hr × 30 days = $11,462/month

vs Commercial APIs:
- GPT-5.2 + Gemini 3 Pro: $20,000-50,000/month
- Savings: 50-75%
```

### Monthly Cost (Work Hours Only)

```
$15.92/hr × 8hr × 22 days = $2,802/month
```

---

## 🆚 Why Two Models?

### GLM-4.7 358B (Primary)

✅ **1M context window** - Entire codebases  
✅ **Best for reasoning** - Complex problems  
✅ **Tool calling** - MCP integration  
✅ **Dense architecture** - Consistent quality  

### MiniMax M2.1 229B (Secondary)

✅ **Fast inference** - Only 10B params active  
✅ **Cost efficient** - Less compute per token  
✅ **Creative tasks** - Great for writing  
✅ **Conversational** - Quick responses  

---

## 📊 Alternative Configurations

### Option A: Single Model, Max Context

Use all 8 GPUs for GLM-4.7 with extended context:

```bash
# All 8 GPUs for GLM-4.7
TENSOR_PARALLEL_SIZE=8
MAX_CONTEXT=2097152  # 2M tokens!
```

### Option B: Redundancy

Run same model on both GPU sets for high availability:

```bash
# GPUs 0-3: GLM-4.7 instance 1
# GPUs 4-7: GLM-4.7 instance 2
# Load balance between them
```

### Option C: Specialized Models

```bash
# GPUs 0-3: GLM-4.7 (coding)
# GPUs 4-5: Whisper (voice)
# GPUs 6-7: Embedding model
```

---

*Last updated: January 2026*
