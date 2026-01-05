# ================================
# AIEco Backend - Multi-stage Dockerfile
# Optimized for production deployment
# ================================

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim as production

# Security: Create non-root user
RUN groupadd -r aieco && useradd -r -g aieco aieco

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=aieco:aieco app/ ./app/
COPY --chown=aieco:aieco alembic.ini ./
COPY --chown=aieco:aieco alembic/ ./alembic/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/skills && \
    chown -R aieco:aieco /app

# Copy skills if they exist
COPY --chown=aieco:aieco ../skills/ ./skills/ 2>/dev/null || true

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Switch to non-root user
USER aieco

# Expose port
EXPOSE ${PORT}

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

# ================================
# Development stage (optional)
# ================================
FROM production as development

USER root

# Install dev dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    ruff \
    isort \
    mypy \
    httpx

# Switch back to non-root
USER aieco

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
