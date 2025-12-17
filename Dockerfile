# Multi-stage build for optimized image size
FROM python:3.11-slim AS builder

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./
COPY src/*/pyproject.toml src/*/

# Install dependencies (sync workspace)
RUN uv sync --frozen --no-dev

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy uv from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy all source code
COPY src/ /app/src/
COPY pyproject.toml uv.lock /app/

# Create directory for telemetry
RUN mkdir -p /app/telemetry

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/clients/python \
    PATH="/app/.venv/bin:$PATH"

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Run the OSPSD service
CMD ["python", "-m", "ospsd_service.main"]
