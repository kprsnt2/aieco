#!/bin/bash
# ============================================
# Local Model Server Startup Script
# For RTX 3050 (6GB VRAM) using Ollama
# ============================================

set -e

echo "🏠 Starting Local AI Server (RTX 3050)..."
echo "================================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Ollama not found. Installing..."
    
    # Linux/WSL
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ -n "$WSL_DISTRO_NAME" ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    # macOS
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ollama
    else
        echo "❌ Please install Ollama manually from: https://ollama.com"
        exit 1
    fi
fi

# Start Ollama service
echo "🔧 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
sleep 3

# Available models for 6GB VRAM (choose one)
MODELS=(
    "glm4:9b"           # GLM-4 9B - Best coding model for your ecosystem
    "qwen2.5:7b"        # Qwen 2.5 7B - Good general purpose
    "deepseek-coder:6.7b" # DeepSeek Coder - Code focused
    "codellama:7b"      # Code Llama - Meta's code model
)

echo ""
echo "📋 Available models for RTX 3050 (6GB):"
for i in "${!MODELS[@]}"; do
    echo "   $((i+1)). ${MODELS[$i]}"
done

# Default to GLM-4 9B for consistency with cloud version
MODEL="${1:-glm4:9b}"
echo ""
echo "🤖 Using model: $MODEL"

# Pull the model if not exists
echo "📥 Ensuring model is available..."
ollama pull "$MODEL"

echo ""
echo "================================================"
echo "✅ Local AI Server Ready!"
echo ""
echo "📍 API Endpoints:"
echo "   Ollama Native: http://localhost:11434"
echo "   OpenAI Compatible: http://localhost:11434/v1"
echo ""
echo "🧪 Test with:"
echo "   curl http://localhost:11434/v1/chat/completions \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}'"
echo ""
echo "🛑 Stop with: Ctrl+C or kill $OLLAMA_PID"
echo "================================================"

# Keep running
wait $OLLAMA_PID
