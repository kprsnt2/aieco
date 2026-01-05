"""AIEco - Observability (Logging, Tracing, Metrics)"""
import structlog
from contextlib import contextmanager
from app.config import settings

def setup_logging():
    """Configure structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if settings.environment == "production"
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

@contextmanager
def trace_llm_call(name: str, model: str, user_id: str = None):
    """Context manager for tracing LLM calls"""
    trace = {"name": name, "model": model, "user_id": user_id, "output": None, "usage": {}}
    try:
        yield trace
        # Would send to Langfuse in production
    except Exception as e:
        trace["error"] = str(e)
        raise
