# Multi-stage build for Daily Logger Assist
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/static && \
    chown -R app:app /app

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base as production

# Set production environment
ENV ENVIRONMENT=production

# Copy production-specific configurations
COPY ./deploy/production/gunicorn_conf.py /app/gunicorn_conf.py

# Use gunicorn for production
CMD ["gunicorn", "app.main:app", "-c", "/app/gunicorn_conf.py"]

# Development stage
FROM base as development

# Set development environment
ENV ENVIRONMENT=development

# Install development dependencies
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Use uvicorn with reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Testing stage
FROM development as testing

# Install test dependencies
COPY requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt

# Run tests
CMD ["python", "-m", "pytest", "-v", "--cov=app", "--cov-report=term-missing"] 