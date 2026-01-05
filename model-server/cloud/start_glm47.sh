#!/bin/bash
# ============================================
# GLM-4.7 358B Model Server Startup Script
# For AMD MI300X (4 GPUs, 768GB total VRAM)
# ============================================

set -e

echo "🚀 Starting GLM-4.7 358B on AMD MI300X..."
echo "================================================"

# Configuration
MODEL_NAME="${MODEL_NAME:-zai-org/GLM-4.7-FP8}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-glm-4.7}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-4}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-1048576}"  # 1M context
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.95}"
PORT="${PORT:-8000}"
API_KEY="${VLLM_API_KEY:-}"

echo "📋 Configuration:"
echo "   Model: $MODEL_NAME"
echo "   Served as: $SERVED_MODEL_NAME"
echo "   Tensor Parallel: $TENSOR_PARALLEL_SIZE GPUs"
echo "   Max Context: $MAX_MODEL_LEN tokens"
echo "   GPU Memory: ${GPU_MEMORY_UTILIZATION}%"
echo "   Port: $PORT"
echo ""

# Check HuggingFace token for gated models
if [ -z "$HF_TOKEN" ]; then
    echo "⚠️  Warning: HF_TOKEN not set. May be required for gated models."
fi

# Check vLLM API key
if [ -z "$API_KEY" ]; then
    echo "⚠️  Warning: VLLM_API_KEY not set. API will be unprotected!"
    API_KEY_ARG=""
else
    echo "🔐 API key protection enabled"
    API_KEY_ARG="--api-key $API_KEY"
fi

echo ""
echo "🔧 Starting vLLM server..."
echo "================================================"

# Start vLLM with GLM-4.7 optimized settings
vllm serve "$MODEL_NAME" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
    --speculative-config.method mtp \
    --speculative-config.num_speculative_tokens 1 \
    --tool-call-parser glm47 \
    --reasoning-parser glm45 \
    --enable-auto-tool-choice \
    --served-model-name "$SERVED_MODEL_NAME" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
    $API_KEY_ARG \
    --host 0.0.0.0 \
    --port "$PORT" \
    --trust-remote-code
