# AIEco Documentation

> Complete documentation for the AIEco Private AI Platform

---

## 📚 Table of Contents

### Getting Started
- [**Getting Started Guide**](guides/GETTING_STARTED.md) - From zero to production in 15 minutes
- [**Quick Start**](QUICKSTART.md) - 5-minute setup
- [**Deployment Guide**](guides/DEPLOYMENT.md) - Deploy on any infrastructure

### API Reference
- [**API Reference**](api/API_REFERENCE.md) - Complete REST API documentation
  - Authentication
  - Chat Completions
  - Function Calling
  - Streaming
  - Error Handling

### SDKs
- [**Python SDK**](sdk/PYTHON_SDK.md) - Official Python client
- [**JavaScript SDK**](sdk/JAVASCRIPT_SDK.md) - Official JS/TS client

### Features
- [**Coding CLI Setup**](CODING_CLI_SETUP.md) - OpenCode, Aider, Continue.dev integration
- [**Multi-Model Architecture**](MULTI_MODEL_ARCHITECTURE.md) - Running multiple models
- [**RAG Pipeline**](DOCUMENTATION.md#4-rag-pipeline) - Document Q&A

### Reference
- [**Configuration**](DOCUMENTATION.md#configuration) - Environment variables & settings
- [**Cost Analysis**](COST_ANALYSIS.md) - Pricing comparison
- [**Benchmarks**](BENCHMARKS.md) - Performance metrics
- [**Security**](SECURITY.md) - Security whitepaper

### Architecture
- [**ADR 001: FastAPI Backend**](adr/001-fastapi-backend.md)
- [**ADR 002: GLM-4.7 Model**](adr/002-glm-47-model.md)
- [**ADR 003: Skills System**](adr/003-skills-system.md)

---

## 🚀 Quick Links

| I want to... | Go to... |
|--------------|----------|
| Get started quickly | [Quick Start](QUICKSTART.md) |
| Use the REST API | [API Reference](api/API_REFERENCE.md) |
| Use Python SDK | [Python SDK](sdk/PYTHON_SDK.md) |
| Use JavaScript SDK | [JavaScript SDK](sdk/JAVASCRIPT_SDK.md) |
| Deploy to production | [Deployment Guide](guides/DEPLOYMENT.md) |
| Use with OpenCode/Aider | [Coding CLI Setup](CODING_CLI_SETUP.md) |
| Compare costs | [Cost Analysis](COST_ANALYSIS.md) |
| Check performance | [Benchmarks](BENCHMARKS.md) |

---

## 📖 Documentation Structure

```
docs/
├── README.md              # This file
├── QUICKSTART.md          # 5-minute setup
├── DOCUMENTATION.md       # Full reference
│
├── api/
│   └── API_REFERENCE.md   # REST API docs
│
├── sdk/
│   ├── PYTHON_SDK.md      # Python client
│   └── JAVASCRIPT_SDK.md  # JS/TS client
│
├── guides/
│   ├── GETTING_STARTED.md # Beginner guide
│   └── DEPLOYMENT.md      # Deployment guide
│
├── adr/                   # Architecture decisions
│   ├── 001-fastapi-backend.md
│   ├── 002-glm-47-model.md
│   └── 003-skills-system.md
│
├── COST_ANALYSIS.md       # Pricing comparison
├── BENCHMARKS.md          # Performance metrics
├── SECURITY.md            # Security docs
├── CODING_CLI_SETUP.md    # CLI integration
├── MULTI_MODEL_ARCHITECTURE.md  # Multi-model setup
├── MODEL_COMPARISON.md    # Model comparison
└── PRIVACY_ANALYSIS.md    # Privacy benefits
```

---

## 🔗 External Resources

- [GitHub Repository](https://github.com/yourusername/aieco)
- [HuggingFace Models](https://huggingface.co/THUDM)
- [vLLM Documentation](https://docs.vllm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 📝 Contributing to Docs

Found an error? Want to improve the docs?

1. Fork the repository
2. Edit the markdown files in `docs/`
3. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

*Last updated: January 2026*
