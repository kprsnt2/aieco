#!/bin/bash
# ================================
# AIEco - Maximum Context Configuration
# 8x AMD MI300X (1.5TB VRAM)
# Optimized for Coding CLI (OpenCode, Claude Code, etc.)
# ================================
#
# Context Window Calculation:
# ================================
# Total VRAM: 1536GB (8 x 192GB)
# Model weights (GLM-4.7 FP8): ~400GB
# Available for KV Cache: ~1100GB
# 
# KV Cache per token ≈ 0.5KB (for 358B model with GQA)
# Max tokens = 1100GB / 0.5KB = ~2.2M tokens!
#
# Conservative estimate with headroom: 2M tokens
# ================================
#
# Comparison:
# - Claude Code: 200K context
# - GPT-4 Turbo: 128K context
# - Cursor: 32-128K context
# - **AIEco**: 2M context (10x more!)
# ================================

set -e

echo "🚀 Starting AIEco MAX CONTEXT Server..."
echo "   Optimized for coding CLIs (OpenCode, Claude Code style)"
echo ""

# Configuration
MODEL="THUDM/glm-4.7-358b-a16b-fp8"
MODEL_NAME="glm-4.7-max"

# Maximum context options (choose based on your needs):
# - 1048576 (1M) - Safe, fast prefill
# - 1572864 (1.5M) - Balanced  
# - 2097152 (2M) - Maximum, slower prefill

MAX_CONTEXT=${MAX_CONTEXT:-2097152}  # 2M tokens default!

echo "📊 Configuration:"
echo "   Model: GLM-4.7 358B (FP8)"
echo "   GPUs: 8x MI300X (1.5TB VRAM)"
echo "   Context: $(($MAX_CONTEXT / 1000))K tokens"
echo ""

# Start vLLM with maximum context
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --served-model-name $MODEL_NAME \
    --port 8000 \
    --host 0.0.0.0 \
    --tensor-parallel-size 8 \
    --dtype bfloat16 \
    --quantization fp8 \
    --max-model-len $MAX_CONTEXT \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --max-num-batched-tokens 131072 \
    --disable-log-requests \
    --trust-remote-code \
    --kv-cache-dtype fp8 \
    &

SERVER_PID=$!

echo ""
echo "⏳ Waiting for model to load (this may take 2-5 minutes)..."
sleep 120

# Health check
if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
    echo ""
    echo "================================"
    echo "🎉 AIEco MAX CONTEXT Server Ready!"
    echo "================================"
    echo ""
    echo "📡 Endpoint: http://localhost:8000/v1"
    echo "🧠 Model: $MODEL_NAME"
    echo "📏 Context: $(($MAX_CONTEXT / 1000000))M tokens ($(($MAX_CONTEXT / 1000))K)"
    echo ""
    echo "💡 Usage with OpenCode/CLI:"
    echo "   export OPENAI_API_BASE=http://localhost:8000/v1"
    echo "   export OPENAI_API_KEY=sk-local"
    echo "   export OPENAI_MODEL=$MODEL_NAME"
    echo ""
    echo "📊 Context Comparison:"
    echo "   Claude Code:  200K tokens"
    echo "   GPT-4 Turbo:  128K tokens"
    echo "   Cursor:       32-128K tokens"
    echo "   >>> AIEco:    $(($MAX_CONTEXT / 1000000))M tokens! <<<"
    echo ""
    echo "================================"
else
    echo "❌ Health check failed. Check logs."
    exit 1
fi

# Keep running
wait $SERVER_PID
