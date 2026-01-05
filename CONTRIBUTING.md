# Contributing to AIEco

Thank you for your interest in contributing to AIEco! 🎉

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/aieco.git
cd aieco

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend setup
cd ../frontend/chat-app
npm install

cd ../dashboard
npm install
```

### Running Locally

```bash
# Backend
cd backend
uvicorn app.main:app --reload --port 8080

# Chat UI (separate terminal)
cd frontend/chat-app
npm run dev

# Dashboard (separate terminal)
cd frontend/dashboard
npm run dev
```

## Contributing Guidelines

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Run `black` and `ruff` before committing
- Docstrings for all public functions

**TypeScript/JavaScript:**
- Use TypeScript for new code
- ESLint + Prettier formatting
- Functional components with hooks

### Commit Messages

Use conventional commits:

```
feat: add prompt caching system
fix: resolve rate limiting edge case
docs: update API documentation
test: add unit tests for auth
refactor: simplify agent orchestrator
chore: update dependencies
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` for backend, `npm test` for frontend)
5. Commit with conventional commit message
6. Push to your fork
7. Open a Pull Request

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] CI checks pass
- [ ] Changelog updated (if applicable)

## Areas for Contribution

### High Priority
- 🧪 Improve test coverage
- 📚 Documentation improvements
- 🌐 Internationalization (i18n)
- 🐛 Bug fixes

### Feature Ideas
- Voice interface (Whisper + TTS)
- SSO/SAML authentication
- Webhook integrations
- Additional MCP tools
- Performance optimizations

### Good First Issues

Look for issues labeled `good first issue` - these are beginner-friendly tasks.

## Code of Conduct

- Be respectful and inclusive
- Constructive feedback only
- Help others learn
- Focus on the code, not the person

## Questions?

- Open an issue for bugs or features
- Start a discussion for questions
- Check existing issues before creating new ones

---

Thank you for helping make AIEco better! 💜
