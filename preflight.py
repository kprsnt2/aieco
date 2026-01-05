#!/usr/bin/env python3
"""
AIEco Pre-Flight Check
======================
Run this BEFORE starting your GPU instance to ensure everything is ready.
This saves you from wasting expensive GPU time on setup issues.

Usage:
    python preflight.py          # Run all checks
    python preflight.py --fix    # Auto-fix issues where possible
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_mark(ok: bool) -> str:
    return "✅" if ok else "❌"


def run_checks():
    """Run all pre-flight checks"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         AIEco Pre-Flight Check                               ║
║         Run this BEFORE starting GPU instance!               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    all_ok = True
    issues = []
    
    # ================================
    # 1. Python Version
    # ================================
    print("1️⃣ Checking Python version...")
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    print(f"   {check_mark(py_ok)} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    if not py_ok:
        issues.append("Python 3.10+ required")
        all_ok = False
    
    # ================================
    # 2. Required Files
    # ================================
    print("\n2️⃣ Checking required files...")
    files_to_check = [
        ("deploy.py", "Main deployment script"),
        ("backend/app/main.py", "FastAPI backend"),
        ("backend/app/config.py", "Configuration"),
        ("backend/requirements.txt", "Backend dependencies"),
    ]
    
    for file_path, desc in files_to_check:
        exists = Path(file_path).exists()
        print(f"   {check_mark(exists)} {file_path}")
        if not exists:
            issues.append(f"Missing: {file_path}")
            all_ok = False
    
    # ================================
    # 3. Model Server Scripts
    # ================================
    print("\n3️⃣ Checking model server scripts...")
    model_scripts = [
        "model-server/multi-model-8x.sh",
        "model-server/max-context-coding.sh",
    ]
    
    for script in model_scripts:
        exists = Path(script).exists()
        print(f"   {check_mark(exists)} {script}")
    
    # ================================
    # 4. HuggingFace Token (for gated models)
    # ================================
    print("\n4️⃣ Checking HuggingFace configuration...")
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    hf_ok = bool(hf_token)
    print(f"   {check_mark(hf_ok)} HF_TOKEN environment variable")
    if not hf_ok:
        print("   ⚠️ Some models may require HuggingFace token")
        print("   Set with: export HF_TOKEN=hf_xxx...")
    
    # Check HF cache
    hf_cache = Path.home() / ".cache" / "huggingface"
    print(f"   {check_mark(hf_cache.exists())} HuggingFace cache directory")
    
    # ================================
    # 5. Disk Space
    # ================================
    print("\n5️⃣ Checking disk space...")
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (1024**3)
        disk_ok = free_gb >= 500  # Need ~500GB for large models
        print(f"   {check_mark(disk_ok)} Free disk space: {free_gb} GB")
        if not disk_ok:
            issues.append(f"Need 500GB+ free space, have {free_gb}GB")
            all_ok = False
    except Exception as e:
        print(f"   ⚠️ Could not check disk space: {e}")
    
    # ================================
    # 6. Core Dependencies
    # ================================
    print("\n6️⃣ Checking Python dependencies...")
    deps = [
        ("fastapi", "FastAPI web framework"),
        ("pydantic", "Data validation"),
        ("httpx", "HTTP client"),
    ]
    
    for dep, desc in deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - run: pip install {dep}")
            issues.append(f"Missing: {dep}")
    
    # ================================
    # 7. vLLM Check (informational)
    # ================================
    print("\n7️⃣ Checking vLLM (optional, will install on GPU)...")
    try:
        import vllm
        print(f"   ✅ vLLM {vllm.__version__} installed")
    except ImportError:
        print("   ℹ️ vLLM not installed (will be installed on GPU instance)")
    
    # ================================
    # 8. Environment File
    # ================================
    print("\n8️⃣ Checking environment configuration...")
    env_file = Path("backend/.env")
    if env_file.exists():
        print(f"   ✅ {env_file} exists")
    else:
        print(f"   ℹ️ {env_file} not found (using defaults)")
    
    # ================================
    # Summary
    # ================================
    print("\n" + "="*60)
    if all_ok:
        print("🎉 All pre-flight checks passed!")
        print("\nYou're ready to deploy. On your GPU instance, run:")
        print("   git clone <your-repo>")
        print("   cd aieco")
        print("   python deploy.py")
    else:
        print("⚠️ Some issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nFix these issues before starting your GPU instance.")
    print("="*60)
    
    return all_ok


def create_env_template():
    """Create a .env template file"""
    template = """# AIEco Environment Configuration
# Copy this to backend/.env and customize

# Environment
ENVIRONMENT=production
DEBUG=false

# Security (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-super-secret-key-change-me

# Model Server
VLLM_BASE_URL=http://localhost:8000/v1
DEFAULT_MODEL=glm-4.7

# Optional: HuggingFace Token (for gated models)
# HF_TOKEN=hf_xxx...

# Optional: Database (disabled by default)
DATABASE_ENABLED=false
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aieco

# Optional: Redis (disabled by default)
REDIS_ENABLED=false
# REDIS_URL=redis://localhost:6379/0
"""
    
    env_path = Path("backend/.env.example")
    env_path.write_text(template)
    print(f"✅ Created {env_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AIEco Pre-Flight Check")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("--create-env", action="store_true", help="Create .env template")
    args = parser.parse_args()
    
    if args.create_env:
        create_env_template()
    else:
        success = run_checks()
        sys.exit(0 if success else 1)
