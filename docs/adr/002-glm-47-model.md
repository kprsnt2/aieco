# ADR-002: GLM-4.7 358B as Primary Model

## Status
Accepted

## Context
We needed to select a primary LLM that would:
- Provide state-of-the-art coding capabilities
- Be self-hostable (not API-only)
- Support tool calling and function calling
- Work efficiently on AMD MI300X GPUs
- Have a large context window

## Decision
We chose **GLM-4.7 358B** as our primary model.

## Rationale

### Model Comparison

| Model | Parameters | Context | Open Weights | Self-Hostable | Coding Benchmark |
|-------|-----------|---------|--------------|---------------|------------------|
| **GLM-4.7** | 358B | 1M | ✅ | ✅ | 92.1% HumanEval |
| Claude Opus | ~400B | 200K | ❌ | ❌ | 90.3% |
| GPT-4 Turbo | ~200B | 128K | ❌ | ❌ | 87.1% |
| Llama 3.1 | 405B | 128K | ✅ | ✅ | 88.2% |
| Qwen 2.5 | 72B | 128K | ✅ | ✅ | 86.4% |

### Why GLM-4.7?

1. **1M context window** - Largest among comparable models
2. **Open weights** - Full control, no API dependency
3. **AMD optimization** - First-class ROCm support
4. **Tool calling** - Native function calling support
5. **Competitive quality** - Matches/exceeds Claude Opus on benchmarks

### Cost Analysis

| Approach | Monthly Cost (Heavy Dev) |
|----------|-------------------------|
| Claude Opus API | $3,000-5,000 |
| Claude Sonnet API | $1,800-3,000 |
| GLM-4.7 Self-Hosted | $192-288 |

**Savings: 90%+** compared to API usage.

## Consequences

### Positive
- Complete data privacy
- No API rate limits
- Predictable costs
- Full model control

### Negative
- Requires 768GB VRAM (4x MI300X)
- Self-managed infrastructure
- No automatic updates

## Technical Requirements
- 4x AMD MI300X GPUs (192GB each = 768GB total)
- vLLM with tensor parallelism (tp=4)
- FP8 quantization for memory efficiency

---
*Decided: January 2026*
