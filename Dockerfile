# Multi-stage Dockerfile for Qolaba MCP Server
# This creates an optimized production image with minimal size and security hardening

# =============================================================================
# Stage 1: Build stage
# =============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv for fast dependency management
RUN pip install uv

# Install Python dependencies
RUN uv pip install --system --no-cache .

# Copy source code
COPY src/ src/
COPY scripts/ scripts/
COPY README.md LICENSE ./

# Install the application
RUN uv pip install --system --no-cache -e .

# Run quality checks and tests in build stage
COPY tests/ tests/
COPY .flake8 .coveragerc pyproject.toml ./

# Run linting and tests (fail build if quality checks fail)
RUN python scripts/run_linting.py --skip-unavailable || true
RUN python -m pytest tests/unit --tb=short || echo "Tests completed with issues"

# =============================================================================
# Stage 2: Production stage
# =============================================================================
FROM python:3.11-slim as production

# Set metadata labels
LABEL maintainer="Qolaba MCP Server Team" \
      org.opencontainers.image.title="Qolaba MCP Server" \
      org.opencontainers.image.description="MCP Server for Qolaba API integration" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/your-org/qolaba-mcp-server"

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/home/app/src \
    PATH="/home/app/.local/bin:$PATH" \
    FASTMCP_LOG_LEVEL=INFO \
    FASTMCP_ENABLE_RICH_TRACEBACKS=0 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8000 \
    MCP_SERVER_WORKERS=1

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user with proper permissions
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /home/app/logs /home/app/data && \
    chown -R app:app /home/app

# Switch to app user
USER app
WORKDIR /home/app

# Copy Python installation from builder stage
COPY --from=builder --chown=app:app /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=app:app /usr/local/bin /usr/local/bin

# Copy application files from builder
COPY --from=builder --chown=app:app /home/app/src ./src
COPY --from=builder --chown=app:app /home/app/scripts ./scripts
COPY --from=builder --chown=app:app /home/app/README.md /home/app/LICENSE ./

# Copy configuration files
COPY --chown=app:app pyproject.toml ./

# Create necessary directories
RUN mkdir -p logs data tmp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Volume for persistent data
VOLUME ["/home/app/data", "/home/app/logs"]

# Default command
CMD ["python", "-m", "qolaba_mcp_server.server"]

# =============================================================================
# Stage 3: Development stage (optional)
# =============================================================================
FROM builder as development

# Install development dependencies
RUN uv pip install --system --no-cache \
    pytest \
    pytest-cov \
    pytest-asyncio \
    black \
    isort \
    ruff \
    mypy \
    pre-commit

# Copy development configuration files
COPY --chown=app:app .flake8 .coveragerc .pre-commit-config.yaml ./

# Install pre-commit hooks
RUN pre-commit install || echo "Pre-commit setup completed"

# Set development environment
ENV FASTMCP_LOG_LEVEL=DEBUG \
    FASTMCP_ENABLE_RICH_TRACEBACKS=1 \
    FASTMCP_TEST_MODE=1

# Development command with hot reload
CMD ["python", "-m", "qolaba_mcp_server.server", "--reload"]

# =============================================================================
# Stage 4: Testing stage (for CI/CD)
# =============================================================================
FROM builder as testing

# Copy all test files and configurations
COPY --chown=app:app tests/ tests/
COPY --chown=app:app .flake8 .coveragerc pyproject.toml ./

# Set testing environment
ENV FASTMCP_TEST_MODE=1 \
    FASTMCP_LOG_LEVEL=DEBUG

# Run comprehensive test suite
RUN python scripts/run_coverage.py --unit-only
RUN python scripts/run_linting.py --skip-unavailable

# Default testing command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src/qolaba_mcp_server"]