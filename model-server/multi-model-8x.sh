#!/bin/bash
# ================================
# AIEco Multi-Model Server
# 8x AMD MI300X (1.5TB VRAM) Configuration
# ================================
#
# VRAM Budget (1536GB total):
# ├── GLM-4.7 358B (FP8):    ~400GB (tp=4, GPUs 0-3)
# ├── MiniMax M2.1 229B:     ~243GB (tp=4, GPUs 4-7)
# └── KV Cache + Overhead:   ~893GB (for extended context)
# ================================

set -e

echo "🚀 Starting AIEco Multi-Model Server on 8x MI300X..."
echo ""

# ================================
# Check for vLLM
# ================================
if ! python -c "import vllm" 2>/dev/null; then
    echo "⚠️ vLLM not found. Installing..."
    pip install vllm --no-cache-dir
fi

# ================================
# AMD ROCm Environment
# ================================
export HSA_FORCE_FINE_GRAIN_PCIE=1
export PYTORCH_ROCM_ARCH="gfx942"
export HIP_FORCE_DEV_KERNARG=1

# Model paths (HuggingFace IDs)
GLM_MODEL="${GLM_MODEL:-THUDM/glm-4.7-358b-a16b-fp8}"
MINIMAX_MODEL="${MINIMAX_MODEL:-MiniMaxAI/MiniMax-M2.1}"

# Context lengths (can be overridden)
GLM_CONTEXT="${GLM_CONTEXT:-1048576}"
MINIMAX_CONTEXT="${MINIMAX_CONTEXT:-204800}"

echo "📊 Configuration:"
echo "   GLM-4.7: $GLM_MODEL (context: $GLM_CONTEXT)"
echo "   MiniMax: $MINIMAX_MODEL (context: $MINIMAX_CONTEXT)"
echo ""

# ================================
# Server 1: GLM-4.7 358B (Primary - Coding/Reasoning)
# GPUs 0-3, Port 8000
# ================================
echo "📦 Starting GLM-4.7 358B on GPUs 0-3..."

HIP_VISIBLE_DEVICES=0,1,2,3 \
CUDA_VISIBLE_DEVICES=0,1,2,3 \
python -m vllm.entrypoints.openai.api_server \
    --model "$GLM_MODEL" \
    --served-model-name glm-4.7 \
    --port 8000 \
    --host 0.0.0.0 \
    --tensor-parallel-size 4 \
    --dtype bfloat16 \
    --max-model-len "$GLM_CONTEXT" \
    --gpu-memory-utilization 0.90 \
    --enable-prefix-caching \
    --disable-log-requests \
    --trust-remote-code \
    2>&1 | tee glm-4.7.log &

GLM_PID=$!
echo "✅ GLM-4.7 starting (PID: $GLM_PID)"

# Wait a bit before starting second model
echo "   Waiting 60s before starting second model..."
sleep 60

# ================================
# Server 2: MiniMax M2.1 229B (Secondary - Fast Inference)
# GPUs 4-7, Port 8001
# ================================
echo "📦 Starting MiniMax M2.1 on GPUs 4-7..."

HIP_VISIBLE_DEVICES=4,5,6,7 \
CUDA_VISIBLE_DEVICES=4,5,6,7 \
python -m vllm.entrypoints.openai.api_server \
    --model "$MINIMAX_MODEL" \
    --served-model-name minimax-m2.1 \
    --port 8001 \
    --host 0.0.0.0 \
    --tensor-parallel-size 4 \
    --dtype bfloat16 \
    --max-model-len "$MINIMAX_CONTEXT" \
    --gpu-memory-utilization 0.85 \
    --enable-prefix-caching \
    --disable-log-requests \
    --trust-remote-code \
    2>&1 | tee minimax-m2.1.log &

MINIMAX_PID=$!
echo "✅ MiniMax M2.1 starting (PID: $MINIMAX_PID)"

# ================================
# Health Check Function
# ================================
check_health() {
    local port=$1
    local name=$2
    local max_attempts=60
    local attempt=1
    
    echo -n "   Checking $name on port $port"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo " ✅ Ready!"
            return 0
        fi
        echo -n "."
        sleep 5
        attempt=$((attempt + 1))
    done
    echo " ❌ Timeout (5min)!"
    return 1
}

# ================================
# Wait for models to load
# ================================
echo ""
echo "⏳ Waiting for models to load (this may take 5-10 minutes)..."
echo ""

check_health 8000 "GLM-4.7"
GLM_OK=$?

check_health 8001 "MiniMax M2.1"
MINIMAX_OK=$?

echo ""
echo "================================"
if [ $GLM_OK -eq 0 ] && [ $MINIMAX_OK -eq 0 ]; then
    echo "🎉 AIEco Multi-Model Server Ready!"
else
    echo "⚠️ Some models failed to start. Check logs:"
    echo "   tail -f glm-4.7.log"
    echo "   tail -f minimax-m2.1.log"
fi
echo "================================"
echo ""
echo "Available Models:"
echo "  • GLM-4.7 358B     → http://localhost:8000/v1"
echo "    - Best for: Coding, reasoning, long context (1M tokens)"
echo ""
echo "  • MiniMax M2.1 229B → http://localhost:8001/v1"
echo "    - Best for: Fast inference, general tasks (200K tokens)"
echo ""
echo "VRAM Usage:"
echo "  • GPUs 0-3: GLM-4.7 (~400GB)"
echo "  • GPUs 4-7: MiniMax M2.1 (~243GB)"
echo "  • Available: ~893GB for KV cache"
echo ""
echo "💰 Cost: \$15.92/hr for 8x MI300X"
echo ""
echo "💡 Quick Test:"
echo "   curl http://localhost:8000/v1/models"
echo ""
echo "🔧 Use with CLI:"
echo "   export OPENAI_API_BASE=http://localhost:8000/v1"
echo "   export OPENAI_API_KEY=sk-local"
echo "================================"
echo ""
echo "📝 Logs: glm-4.7.log, minimax-m2.1.log"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $GLM_PID 2>/dev/null
    kill $MINIMAX_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
wait
