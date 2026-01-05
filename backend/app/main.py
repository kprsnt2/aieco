"""
AIEco Backend - Main Application Entry Point
FastAPI application with all routes, middleware, and startup events
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.config import settings
from app.api.v1 import router as api_router
from app.core.database import init_db, close_db
from app.core.redis_client import init_redis, close_redis
from app.core.observability import setup_logging

# Configure structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan management - startup and shutdown"""
    # ===== Startup =====
    logger.info("🚀 Starting AIEco Backend", 
                environment=settings.environment,
                debug=settings.debug)
    
    # Initialize database (optional)
    if settings.database_enabled:
        await init_db()
        logger.info("✅ Database connected")
    else:
        logger.info("⏭️ Database disabled (set DATABASE_ENABLED=true to enable)")
    
    # Initialize Redis (optional)
    if settings.redis_enabled:
        await init_redis()
        logger.info("✅ Redis connected")
    else:
        logger.info("⏭️ Redis disabled (set REDIS_ENABLED=true to enable)")
    
    # Log model configuration
    logger.info("🤖 Model configuration", 
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                backend=settings.local_backend)
    
    yield
    
    # ===== Shutdown =====
    logger.info("🛑 Shutting down AIEco Backend")
    if settings.database_enabled:
        await close_db()
    if settings.redis_enabled:
        await close_redis()
    logger.info("👋 Goodbye!")


# ===== Create FastAPI Application =====
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
# 🚀 AIEco - Private AI Platform API

Production-grade self-hosted AI ecosystem powered by GLM-4.7 358B.

## Features
- 🤖 **Chat Completions** - OpenAI-compatible API
- 📚 **RAG Pipeline** - Document search with citations
- 🤖 **AI Agents** - LangGraph-powered agents
- 🔌 **MCP Tools** - Extensible tool system
- 📊 **Observability** - Full tracing and metrics

## Authentication
Use JWT Bearer token or API key in `X-API-Key` header.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ===== Middleware =====
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    request_id = request.headers.get("X-Request-ID", "N/A")
    
    logger.info(
        "➡️ Request",
        method=request.method,
        path=request.url.path,
        request_id=request_id
    )
    
    response = await call_next(request)
    
    logger.info(
        "⬅️ Response",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        request_id=request_id
    )
    
    return response


# ===== Exception Handlers =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(
        "❌ Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.debug else None
        }
    )


# ===== Routes =====
# API v1 routes
app.include_router(api_router, prefix=settings.api_prefix)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ===== Health Checks =====
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "aieco-backend",
        "version": settings.api_version,
        "environment": settings.environment
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies enabled dependencies"""
    from app.core.llm import check_llm_connection
    
    checks = {
        "llm": await check_llm_connection()
    }
    
    # Only check database if enabled
    if settings.database_enabled:
        from app.core.database import check_db_connection
        checks["database"] = await check_db_connection()
    
    # Only check redis if enabled
    if settings.redis_enabled:
        from app.core.redis_client import check_redis_connection
        checks["redis"] = await check_redis_connection()
    
    all_healthy = all(checks.values())
    
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks
        }
    )


# ===== Root Endpoint =====
@app.get("/", tags=["Root"])
async def root():
    """API root - returns basic info"""
    return {
        "name": "AIEco API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
