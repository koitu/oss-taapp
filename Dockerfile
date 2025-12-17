# Multi-stage build for optimized image size
FROM python:3.11-slim AS builder

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy all project files (needed for workspace resolution)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies (sync entire workspace)
RUN uv sync --frozen --no-dev --all-packages

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy uv from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code and config from builder
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/uv.lock /app/

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
