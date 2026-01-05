#!/usr/bin/env python3
"""
AIEco - One-Click Deployment
============================
Auto-detects hardware and deploys the optimal configuration.

Usage:
    python deploy.py              # Auto-detect and deploy
    python deploy.py --local      # Force local/consumer GPU mode
    python deploy.py --cloud      # Force cloud GPU mode
    python deploy.py --dry-run    # Show what would be deployed
    python deploy.py --model-only # Only start model server (skip backend)
"""

import os
import sys
import subprocess
import json
import time
import signal
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class DeploymentMode(Enum):
    """Available deployment modes based on hardware"""
    CLOUD_8X = "cloud_8x"          # 8x MI300X - Multi-model (GLM + MiniMax)
    CLOUD_4X = "cloud_4x"          # 4x MI300X - Single large model (GLM-4.7)
    CLOUD_1X = "cloud_1x"          # 1x MI300X - Medium model (Qwen-72B)
    NVIDIA_A100 = "nvidia_a100"    # Full A100 80GB - Large model
    NVIDIA_A100_40 = "nvidia_a100_40"  # A100 40GB - Medium model
    NVIDIA_CONSUMER = "nvidia_consumer"  # RTX 3090/4090 - Medium model
    NVIDIA_SMALL = "nvidia_small"  # 8-16GB VRAM - Small model
    NVIDIA_TINY = "nvidia_tiny"    # 4-8GB VRAM - Tiny model (Phi-3, Qwen 3B)
    LOCAL_SMALL = "local_small"    # CPU or very low VRAM


@dataclass
class GPUInfo:
    """GPU information"""
    name: str
    vram_gb: float
    index: int
    vendor: str  # "AMD" or "NVIDIA"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    mode: DeploymentMode
    gpus: List[GPUInfo]
    total_vram_gb: float
    models: List[Dict]
    ports: List[int]
    recommended_context: int
    estimated_cost_per_hour: float


# ================================
# Model Configurations
# ================================

MODELS = {
    "glm-4.7-358b": {
        "hf_id": "THUDM/glm-4.7-358b-a16b-fp8",
        "vram_required": 400,
        "context": 1048576,
        "tp_size": 4,
        "dtype": "bfloat16",
        "quantization": "fp8",
        "description": "GLM-4.7 358B - Best for coding, 1M context"
    },
    "minimax-m2.1": {
        "hf_id": "MiniMaxAI/MiniMax-M2.1",
        "vram_required": 243,
        "context": 204800,
        "tp_size": 4,
        "dtype": "bfloat16",
        "quantization": None,
        "description": "MiniMax M2.1 229B - Fast MoE, 200K context"
    },
    "qwen2.5-72b": {
        "hf_id": "Qwen/Qwen2.5-72B-Instruct-AWQ",
        "vram_required": 48,
        "context": 131072,
        "tp_size": 1,
        "dtype": "float16",
        "quantization": "awq",
        "description": "Qwen 2.5 72B AWQ - Balanced, 128K context"
    },
    "qwen2.5-32b": {
        "hf_id": "Qwen/Qwen2.5-32B-Instruct-AWQ",
        "vram_required": 24,
        "context": 65536,
        "tp_size": 1,
        "dtype": "float16",
        "quantization": "awq",
        "description": "Qwen 2.5 32B AWQ - Medium model, 64K context"
    },
    "qwen2.5-7b": {
        "hf_id": "Qwen/Qwen2.5-7B-Instruct",
        "vram_required": 8,
        "context": 32768,
        "tp_size": 1,
        "dtype": "float16",
        "quantization": None,
        "description": "Qwen 2.5 7B - Small & fast, 32K context"
    },
    "phi-3-mini": {
        "hf_id": "microsoft/Phi-3-mini-4k-instruct",
        "vram_required": 3,
        "context": 4096,
        "tp_size": 1,
        "dtype": "float16",
        "quantization": None,
        "description": "Phi-3 Mini 3.8B - Tiny, 4K context (3GB VRAM)"
    },
    "qwen2.5-3b": {
        "hf_id": "Qwen/Qwen2.5-3B-Instruct",
        "vram_required": 4,
        "context": 32768,
        "tp_size": 1,
        "dtype": "float16",
        "quantization": None,
        "description": "Qwen 2.5 3B - Great for 5GB VRAM, 32K context"
    },
    "qwen2.5-1.5b": {
        "hf_id": "Qwen/Qwen2.5-1.5B-Instruct",
        "vram_required": 2,
        "context": 32768,
        "tp_size": 1,
        "dtype": "float16",
        "quantization": None,
        "description": "Qwen 2.5 1.5B - Ultra tiny, 32K context"
    }
}


def print_banner():
    """Print AIEco banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     █████╗ ██╗███████╗ ██████╗ ██████╗                       ║
║    ██╔══██╗██║██╔════╝██╔════╝██╔═══██╗                      ║
║    ███████║██║█████╗  ██║     ██║   ██║                      ║
║    ██╔══██║██║██╔══╝  ██║     ██║   ██║                      ║
║    ██║  ██║██║███████╗╚██████╗╚██████╔╝                      ║
║    ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═════╝                       ║
║                                                              ║
║     🚀 Private AI Ecosystem - One Click Deploy               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def run_cmd(cmd: List[str], timeout: int = 30) -> Optional[str]:
    """Run a command and return output, None on error"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def detect_gpus() -> List[GPUInfo]:
    """Detect available GPUs (AMD or NVIDIA) with multiple fallbacks"""
    gpus = []
    
    # ===== Check for manual VRAM override =====
    manual_vram = os.environ.get("AIECO_VRAM_GB")
    if manual_vram:
        try:
            vram = float(manual_vram)
            print(f"📌 Using manual VRAM override: {vram}GB")
            gpus.append(GPUInfo(
                name="Manual GPU",
                vram_gb=vram,
                index=0,
                vendor="NVIDIA"
            ))
            return gpus
        except ValueError:
            pass
    
    # ===== Try AMD ROCm =====
    rocm_output = run_cmd(["rocm-smi", "--showproductname", "--json"])
    if rocm_output:
        try:
            data = json.loads(rocm_output)
            for key, value in data.items():
                if key.startswith("card"):
                    idx = int(key.replace("card", ""))
                    gpus.append(GPUInfo(
                        name=value.get("Card Series", "AMD GPU"),
                        vram_gb=192.0,  # MI300X default
                        index=idx,
                        vendor="AMD"
                    ))
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Get VRAM info separately for AMD
    if gpus:
        vram_output = run_cmd(["rocm-smi", "--showmeminfo", "vram", "--json"])
        if vram_output:
            try:
                vram_data = json.loads(vram_output)
                for gpu in gpus:
                    card_key = f"card{gpu.index}"
                    if card_key in vram_data:
                        vram_bytes = int(vram_data[card_key].get("VRAM Total Memory (B)", 0))
                        gpu.vram_gb = vram_bytes / (1024**3)
            except (json.JSONDecodeError, KeyError):
                pass
        return gpus
    
    # ===== Try NVIDIA nvidia-smi =====
    nvidia_output = run_cmd(["nvidia-smi", "--query-gpu=name,memory.total,index", 
                             "--format=csv,noheader,nounits"])
    if nvidia_output:
        for line in nvidia_output.strip().split("\n"):
            if line:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    gpus.append(GPUInfo(
                        name=parts[0],
                        vram_gb=float(parts[1]) / 1024,  # MB to GB
                        index=int(parts[2]),
                        vendor="NVIDIA"
                    ))
        return gpus
    
    # ===== Fallback 1: nvidia-smi simple =====
    simple_output = run_cmd(["nvidia-smi", "-L"])
    if simple_output and "GPU" in simple_output:
        # Try to extract basic info
        print("⚠️ nvidia-smi detected but limited info available")
        gpus.append(GPUInfo(
            name="NVIDIA GPU",
            vram_gb=5.0,  # Assume small partition
            index=0,
            vendor="NVIDIA"
        ))
        return gpus
    
    # ===== Fallback 2: PyTorch =====
    try:
        import torch
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                gpus.append(GPUInfo(
                    name=props.name,
                    vram_gb=props.total_memory / (1024**3),
                    index=i,
                    vendor="NVIDIA"
                ))
            if gpus:
                print(f"✅ Detected {len(gpus)} GPU(s) via PyTorch")
                return gpus
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ PyTorch GPU detection failed: {e}")
    
    # ===== Fallback 3: Check CUDA_VISIBLE_DEVICES =====
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_devices:
        device_count = len(cuda_devices.split(","))
        print(f"⚠️ No GPU detection working, using CUDA_VISIBLE_DEVICES: {cuda_devices}")
        for i in range(device_count):
            gpus.append(GPUInfo(
                name=f"GPU {i}",
                vram_gb=5.0,  # Conservative default
                index=i,
                vendor="NVIDIA"
            ))
        if gpus:
            return gpus
    
    # ===== Fallback 4: Prompt user =====
    print("")
    print("❌ Could not auto-detect GPU. Please specify manually:")
    print("   Set AIECO_VRAM_GB environment variable, e.g.:")
    print("   export AIECO_VRAM_GB=5    # For 5GB VRAM")
    print("   export AIECO_VRAM_GB=80   # For 80GB A100")
    print("")
    
    try:
        vram_input = input("Enter your GPU VRAM in GB (e.g., 5, 24, 80) [default=5]: ").strip()
        vram = float(vram_input) if vram_input else 5.0
        gpus.append(GPUInfo(
            name="Manual GPU",
            vram_gb=vram,
            index=0,
            vendor="NVIDIA"
        ))
    except (ValueError, EOFError):
        # Default to 5GB if input fails
        gpus.append(GPUInfo(
            name="Default GPU",
            vram_gb=5.0,
            index=0,
            vendor="NVIDIA"
        ))
    
    return gpus


def determine_deployment_mode(gpus: List[GPUInfo]) -> DeploymentMode:
    """Determine the best deployment mode based on hardware"""
    if not gpus:
        return DeploymentMode.LOCAL_SMALL
    
    total_vram = sum(g.vram_gb for g in gpus)
    gpu_count = len(gpus)
    vendor = gpus[0].vendor
    first_gpu_name = gpus[0].name
    
    # AMD MI300X detection
    if vendor == "AMD":
        if gpu_count >= 8 and total_vram >= 1400:
            return DeploymentMode.CLOUD_8X
        elif gpu_count >= 4 and total_vram >= 700:
            return DeploymentMode.CLOUD_4X
        elif total_vram >= 150:
            return DeploymentMode.CLOUD_1X
        else:
            return DeploymentMode.LOCAL_SMALL
    
    # NVIDIA detection - check VRAM first for partitioned GPUs
    if vendor == "NVIDIA":
        # Check for A100/H100 by name
        is_datacenter = any(x in first_gpu_name for x in ["A100", "H100", "H200", "A10", "L40"])
        
        if is_datacenter:
            # Datacenter GPU - use VRAM to determine partition size
            if total_vram >= 70:
                return DeploymentMode.NVIDIA_A100  # Full 80GB A100
            elif total_vram >= 35:
                return DeploymentMode.NVIDIA_A100_40  # 40GB A100 or partition
            elif total_vram >= 16:
                return DeploymentMode.NVIDIA_CONSUMER  # ~20GB partition
            elif total_vram >= 8:
                return DeploymentMode.NVIDIA_SMALL  # ~10GB partition
            else:
                return DeploymentMode.NVIDIA_TINY  # 5GB partition
        
        # Consumer GPUs
        if any(x in first_gpu_name for x in ["3090", "4090", "A6000"]):
            return DeploymentMode.NVIDIA_CONSUMER
        elif any(x in first_gpu_name for x in ["3080", "4080", "3070", "4070"]):
            return DeploymentMode.NVIDIA_SMALL
        elif any(x in first_gpu_name for x in ["3060", "4060", "3050", "4050"]):
            return DeploymentMode.NVIDIA_TINY
    
    # Fallback based purely on VRAM
    if total_vram >= 70:
        return DeploymentMode.NVIDIA_A100
    elif total_vram >= 35:
        return DeploymentMode.NVIDIA_A100_40
    elif total_vram >= 16:
        return DeploymentMode.NVIDIA_CONSUMER
    elif total_vram >= 8:
        return DeploymentMode.NVIDIA_SMALL
    elif total_vram >= 4:
        return DeploymentMode.NVIDIA_TINY
    
    return DeploymentMode.LOCAL_SMALL


def get_deployment_config(mode: DeploymentMode, gpus: List[GPUInfo]) -> DeploymentConfig:
    """Get deployment configuration for mode"""
    total_vram = sum(g.vram_gb for g in gpus) if gpus else 0
    
    configs = {
        DeploymentMode.CLOUD_8X: {
            "models": [
                {"name": "glm-4.7", "model_id": "glm-4.7-358b", "gpus": "0,1,2,3", "port": 8000},
                {"name": "minimax-m2.1", "model_id": "minimax-m2.1", "gpus": "4,5,6,7", "port": 8001}
            ],
            "context": 1048576,  # 1M for safe operation
            "cost": 15.92
        },
        DeploymentMode.CLOUD_4X: {
            "models": [
                {"name": "glm-4.7", "model_id": "glm-4.7-358b", "gpus": "0,1,2,3", "port": 8000}
            ],
            "context": 1048576,
            "cost": 7.96
        },
        DeploymentMode.CLOUD_1X: {
            "models": [
                {"name": "qwen2.5-72b", "model_id": "qwen2.5-72b", "gpus": "0", "port": 8000}
            ],
            "context": 65536,
            "cost": 1.99
        },
        DeploymentMode.NVIDIA_A100: {
            "models": [
                {"name": "qwen2.5-72b", "model_id": "qwen2.5-72b", "gpus": "0", "port": 8000}
            ],
            "context": 65536,
            "cost": 2.50
        },
        DeploymentMode.NVIDIA_A100_40: {
            "models": [
                {"name": "qwen2.5-32b", "model_id": "qwen2.5-32b", "gpus": "0", "port": 8000}
            ],
            "context": 32768,
            "cost": 1.50
        },
        DeploymentMode.NVIDIA_CONSUMER: {
            "models": [
                {"name": "qwen2.5-32b", "model_id": "qwen2.5-32b", "gpus": "0", "port": 8000}
            ],
            "context": 32768,
            "cost": 0.0
        },
        DeploymentMode.NVIDIA_SMALL: {
            "models": [
                {"name": "qwen2.5-7b", "model_id": "qwen2.5-7b", "gpus": "0", "port": 8000}
            ],
            "context": 16384,
            "cost": 0.0
        },
        DeploymentMode.NVIDIA_TINY: {
            "models": [
                {"name": "qwen2.5-3b", "model_id": "qwen2.5-3b", "gpus": "0", "port": 8000}
            ],
            "context": 8192,
            "cost": 0.0
        },
        DeploymentMode.LOCAL_SMALL: {
            "models": [
                {"name": "phi-3-mini", "model_id": "phi-3-mini", "gpus": "0", "port": 8000}
            ],
            "context": 4096,
            "cost": 0.0
        }
    }
    
    config = configs.get(mode, configs[DeploymentMode.LOCAL_SMALL])
    
    return DeploymentConfig(
        mode=mode,
        gpus=gpus,
        total_vram_gb=total_vram,
        models=config["models"],
        ports=[m["port"] for m in config["models"]],
        recommended_context=config["context"],
        estimated_cost_per_hour=config["cost"]
    )


def check_vllm_installed() -> bool:
    """Check if vLLM is installed"""
    try:
        import vllm
        return True
    except ImportError:
        return False


def install_vllm(is_amd: bool = False):
    """Install vLLM for AMD or NVIDIA"""
    print("\n📦 Installing vLLM...")
    
    if is_amd:
        print("   Detected AMD GPU - installing ROCm version...")
        # For AMD, we need the ROCm version
        cmd = [sys.executable, "-m", "pip", "install", 
               "vllm", "--no-cache-dir"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", 
               "vllm>=0.5.0", "--no-cache-dir"]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ vLLM installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install vLLM: {e}")
        return False


def build_vllm_command(model_config: Dict, vendor: str = "NVIDIA") -> List[str]:
    """Build the vLLM server command with all necessary arguments"""
    model_id = model_config["model_id"]
    model_info = MODELS[model_id]
    port = model_config["port"]
    name = model_config["name"]
    gpu_indices = model_config["gpus"]
    
    gpu_count = len(gpu_indices.split(","))
    
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_info["hf_id"],
        "--served-model-name", name,
        "--port", str(port),
        "--host", "0.0.0.0",
        "--tensor-parallel-size", str(model_info.get("tp_size", gpu_count)),
        "--dtype", model_info.get("dtype", "float16"),
        "--max-model-len", str(model_info.get("context", 32768)),
        "--gpu-memory-utilization", "0.90",
        "--trust-remote-code",
        "--disable-log-requests",
    ]
    
    # Add quantization if specified
    if model_info.get("quantization"):
        cmd.extend(["--quantization", model_info["quantization"]])
    
    # Add prefix caching for efficiency
    cmd.append("--enable-prefix-caching")
    
    return cmd


def start_model_server(model_config: Dict, vendor: str, dry_run: bool = False):
    """Start a vLLM model server"""
    model_id = model_config["model_id"]
    model_info = MODELS[model_id]
    port = model_config["port"]
    gpu_indices = model_config["gpus"]
    name = model_config["name"]
    
    cmd = build_vllm_command(model_config, vendor)
    
    # Set up environment
    env = os.environ.copy()
    
    if vendor == "AMD":
        # ROCm environment
        env["HIP_VISIBLE_DEVICES"] = gpu_indices
        env["CUDA_VISIBLE_DEVICES"] = gpu_indices
        env["HSA_FORCE_FINE_GRAIN_PCIE"] = "1"
        env["PYTORCH_ROCM_ARCH"] = "gfx942"  # MI300X architecture
    else:
        env["CUDA_VISIBLE_DEVICES"] = gpu_indices
    
    if dry_run:
        env_str = f"HIP_VISIBLE_DEVICES={gpu_indices}" if vendor == "AMD" else f"CUDA_VISIBLE_DEVICES={gpu_indices}"
        print(f"   Would run: {env_str} {' '.join(cmd)}")
        return None
    
    print(f"   Starting {name} on port {port} (GPUs: {gpu_indices})...")
    print(f"   Model: {model_info['hf_id']}")
    print(f"   Context: {model_info['context']:,} tokens")
    
    # Start process
    log_file = open(f"vllm_{name}.log", "w")
    proc = subprocess.Popen(
        cmd, 
        env=env, 
        stdout=log_file, 
        stderr=subprocess.STDOUT
    )
    
    return proc


def wait_for_server(port: int, timeout: int = 300) -> bool:
    """Wait for server to become available"""
    import urllib.request
    import urllib.error
    
    start_time = time.time()
    url = f"http://localhost:{port}/health"
    
    print(f"   Waiting for server on port {port}...", end="", flush=True)
    
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            urllib.request.urlopen(req, timeout=5)
            print(" ✅ Ready!")
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, Exception):
            print(".", end="", flush=True)
            time.sleep(5)
    
    print(" ❌ Timeout!")
    return False


def deploy(config: DeploymentConfig, dry_run: bool = False, model_only: bool = False):
    """Deploy AIEco with the given configuration"""
    print("\n🚀 Starting deployment...")
    print(f"   Mode: {config.mode.value}")
    print(f"   Total VRAM: {config.total_vram_gb:.1f} GB")
    print(f"   Models: {len(config.models)}")
    print(f"   Context: {config.recommended_context:,} tokens")
    if config.estimated_cost_per_hour > 0:
        print(f"   Cost: ${config.estimated_cost_per_hour:.2f}/hr")
    
    vendor = config.gpus[0].vendor if config.gpus else "NVIDIA"
    processes = []
    
    # Check/install vLLM
    if not dry_run:
        if not check_vllm_installed():
            if not install_vllm(is_amd=(vendor == "AMD")):
                print("❌ Cannot proceed without vLLM")
                return False
    
    # Start model servers
    print("\n🧠 Starting model servers...")
    for model in config.models:
        proc = start_model_server(model, vendor, dry_run)
        if proc:
            processes.append((model, proc))
    
    if dry_run:
        print("\n✅ Dry run complete! No servers started.")
        return True
    
    # Wait for models to load
    print("\n⏳ Waiting for models to load (this may take 2-10 minutes)...")
    all_ready = True
    for model, proc in processes:
        if not wait_for_server(model["port"], timeout=600):
            print(f"   ⚠️ Model {model['name']} failed to start!")
            all_ready = False
    
    if not all_ready:
        print("\n⚠️ Some models failed to start. Check vllm_*.log for details.")
    
    # Print success message
    print("\n" + "="*60)
    print("🎉 AIEco Model Server(s) Running!")
    print("="*60)
    print("\n📡 Endpoints:")
    for model in config.models:
        info = MODELS[model["model_id"]]
        print(f"   • {model['name']}: http://localhost:{model['port']}/v1")
        print(f"     {info['description']}")
    
    print(f"\n📊 Configuration:")
    print(f"   Mode: {config.mode.value}")
    print(f"   Max Context: {config.recommended_context:,} tokens")
    
    print(f"\n💡 Quick Test:")
    print(f'   curl http://localhost:{config.ports[0]}/v1/models')
    
    print(f"\n🔧 Use with OpenAI SDK:")
    print(f'   OPENAI_API_BASE=http://localhost:{config.ports[0]}/v1')
    print(f'   OPENAI_API_KEY=sk-local')
    print(f'   OPENAI_MODEL={config.models[0]["name"]}')
    
    if config.estimated_cost_per_hour > 0:
        print(f"\n💰 Remember: You're spending ${config.estimated_cost_per_hour:.2f}/hr!")
    
    print("="*60)
    print("\n📝 Logs: vllm_<model>.log")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Set up signal handler
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutting down...")
        for model, proc in processes:
            print(f"   Stopping {model['name']}...")
            proc.terminate()
            proc.wait(timeout=10)
        print("👋 Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running
    try:
        while True:
            time.sleep(10)
            # Check if processes are still running
            for model, proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️ Model {model['name']} exited!")
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AIEco One-Click Deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py              # Auto-detect and deploy
  python deploy.py --dry-run    # Preview without deploying
  python deploy.py --local      # Force local small model
  python deploy.py --cloud      # Force cloud configuration
        """
    )
    parser.add_argument("--local", action="store_true", help="Force local/small GPU mode")
    parser.add_argument("--cloud", action="store_true", help="Force cloud GPU mode")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deployed")
    parser.add_argument("--model-only", action="store_true", help="Only start model server")
    args = parser.parse_args()
    
    print_banner()
    
    # Detect GPUs
    print("🔍 Detecting hardware...")
    gpus = detect_gpus()
    
    if gpus:
        print(f"   Found {len(gpus)} GPU(s):")
        for gpu in gpus:
            print(f"   • [{gpu.index}] {gpu.name} ({gpu.vram_gb:.1f} GB) - {gpu.vendor}")
        total_vram = sum(g.vram_gb for g in gpus)
        print(f"   Total VRAM: {total_vram:.0f} GB")
    else:
        print("   ⚠️ No GPUs detected!")
        print("   Will use small model with CPU (very slow)")
    
    # Determine mode
    if args.local:
        mode = DeploymentMode.LOCAL_SMALL
        print("\n📋 Forced mode: LOCAL_SMALL")
    elif args.cloud:
        if len(gpus) >= 8:
            mode = DeploymentMode.CLOUD_8X
        elif len(gpus) >= 4:
            mode = DeploymentMode.CLOUD_4X
        else:
            mode = DeploymentMode.CLOUD_1X
        print(f"\n📋 Forced cloud mode: {mode.value}")
    else:
        mode = determine_deployment_mode(gpus)
        print(f"\n📋 Auto-detected mode: {mode.value}")
    
    # Get configuration
    config = get_deployment_config(mode, gpus)
    
    # Print configuration
    print("\n📦 Models to deploy:")
    for model in config.models:
        info = MODELS[model["model_id"]]
        print(f"   • {model['name']}")
        print(f"     HuggingFace: {info['hf_id']}")
        print(f"     VRAM needed: ~{info['vram_required']} GB")
        print(f"     Context: {info['context']:,} tokens")
        print(f"     GPUs: {model['gpus']}")
        print(f"     Port: {model['port']}")
    
    # Estimate download size
    total_vram_needed = sum(MODELS[m["model_id"]]["vram_required"] for m in config.models)
    download_gb = total_vram_needed * 1.5  # Rough estimate
    print(f"\n⚠️ Model download: ~{download_gb:.0f} GB (first time only)")
    print(f"   Ensure sufficient disk space!")
    
    # Confirm deployment
    if not args.dry_run:
        print("\n" + "="*60)
        if config.estimated_cost_per_hour > 0:
            print(f"💰 COST WARNING: ${config.estimated_cost_per_hour:.2f}/hr while running!")
        response = input("🚀 Ready to deploy? [Y/n]: ").strip().lower()
        if response and response != 'y':
            print("Deployment cancelled.")
            return
    
    # Deploy!
    deploy(config, dry_run=args.dry_run, model_only=args.model_only)


if __name__ == "__main__":
    main()
