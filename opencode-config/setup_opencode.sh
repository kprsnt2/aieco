#!/bin/bash
# ============================================
# AIEco - OpenCode CLI Setup Script
# ============================================
# This script configures OpenCode CLI to use your private AIEco backend
# 
# Usage:
#   chmod +x setup_opencode.sh
#   ./setup_opencode.sh [cloud|local|backend]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          AIEco - OpenCode CLI Setup                      ║"
echo "║    Connect OpenCode to your private GLM-4.7 358B model   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if OpenCode is installed
if ! command -v opencode &> /dev/null; then
    echo -e "${YELLOW}OpenCode CLI not found. Installing...${NC}"
    
    # Try npm install
    if command -v npm &> /dev/null; then
        npm install -g @anthropics/opencode
    else
        echo -e "${RED}Error: npm not found. Please install Node.js first.${NC}"
        echo "Visit: https://nodejs.org/"
        exit 1
    fi
fi

# Select profile
PROFILE=${1:-backend}
echo -e "${GREEN}Selected profile: $PROFILE${NC}"

case $PROFILE in
    cloud)
        echo -e "${YELLOW}Using GLM-4.7 358B on AMD Cloud${NC}"
        echo ""
        read -p "Enter your AMD Cloud IP address: " AMD_CLOUD_IP
        read -p "Enter your vLLM API key: " VLLM_API_KEY
        
        # Update config with cloud settings
        export VLLM_API_KEY
        sed -i "s/YOUR_AMD_CLOUD_IP/$AMD_CLOUD_IP/g" "$CONFIG_FILE"
        ;;
    local)
        echo -e "${YELLOW}Using GLM-4 9B on local Ollama${NC}"
        echo ""
        echo "Make sure Ollama is running with: ollama serve"
        echo "Pull the model with: ollama pull glm4:9b"
        ;;
    backend)
        echo -e "${YELLOW}Using AIEco Backend API${NC}"
        echo ""
        read -p "Enter your AIEco API key: " AIECO_API_KEY
        export AIECO_API_KEY
        ;;
esac

# Create OpenCode config directory
OPENCODE_DIR="$HOME/.config/opencode"
mkdir -p "$OPENCODE_DIR"

# Copy config
cp "$CONFIG_FILE" "$OPENCODE_DIR/config.json"

# Set default profile
cat > "$OPENCODE_DIR/settings.json" << EOF
{
  "defaultProfile": "$PROFILE",
  "configPath": "$OPENCODE_DIR/config.json"
}
EOF

echo ""
echo -e "${GREEN}✅ OpenCode CLI configured successfully!${NC}"
echo ""
echo -e "Usage:"
echo -e "  ${BLUE}opencode${NC}              # Start interactive mode"
echo -e "  ${BLUE}opencode ask \"...\"${NC}    # Ask a question"
echo -e "  ${BLUE}opencode code \"...\"${NC}  # Generate code"
echo -e "  ${BLUE}opencode debug file${NC}  # Debug a file"
echo ""
echo -e "Switch profiles with:"
echo -e "  ${BLUE}opencode --profile cloud${NC}"
echo -e "  ${BLUE}opencode --profile local${NC}"
echo -e "  ${BLUE}opencode --profile backend${NC}"
echo ""
echo -e "${GREEN}Happy coding with your private AI! 🚀${NC}"
