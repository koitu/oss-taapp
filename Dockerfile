# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files into container
COPY . .

# Install uv (your package manager)
RUN pip install uv

# Install all dependencies
RUN uv sync --all-packages --no-dev

# Set PYTHONPATH so imports work
ENV PYTHONPATH=/app/src:/app/clients/python

# Expose FastAPI port
EXPOSE 8000

# Default command runs the FastAPI service
CMD ["sh", "-c", "uv run uvicorn discord_client_service.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
