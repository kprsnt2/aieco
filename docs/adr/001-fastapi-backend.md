# ADR-001: FastAPI Backend Framework

## Status
Accepted

## Context
We needed to choose a Python web framework for our AI ecosystem backend that would:
- Handle high-throughput async operations for LLM inference
- Provide OpenAPI documentation automatically
- Support modern Python type hints
- Integrate well with async libraries for database and Redis

## Decision
We chose **FastAPI** over Django, Flask, and other alternatives.

## Rationale

### Why FastAPI?
| Criteria | FastAPI | Django | Flask |
|----------|---------|--------|-------|
| Async native | ✅ Yes | ⚠️ Partial | ❌ No |
| Auto OpenAPI | ✅ Yes | ❌ Manual | ❌ Manual |
| Type hints | ✅ First-class | ⚠️ Optional | ❌ Optional |
| Performance | ✅ ~50K req/s | ⚠️ ~10K | ⚠️ ~15K |
| Learning curve | ✅ Low | ❌ High | ✅ Low |

### Key Benefits
1. **Async/await native** - Critical for LLM streaming responses
2. **Pydantic integration** - Type-safe request/response validation
3. **OpenAPI auto-generation** - Swagger UI out of the box
4. **Modern Python** - Type hints, dataclasses, async

## Consequences

### Positive
- 3x fewer lines of code vs Django
- Zero manual API documentation
- Native async for all I/O operations
- Excellent developer experience

### Negative
- Smaller ecosystem than Django
- Need to choose individual components (ORM, admin, etc.)
- Less opinionated (requires more architecture decisions)

## Alternatives Considered
- **Django REST Framework**: Too heavy, async support retrofitted
- **Flask + extensions**: More boilerplate, no native async
- **Starlette (bare)**: Too low-level
- **Litestar**: Newer, smaller community

---
*Decided: January 2026*
