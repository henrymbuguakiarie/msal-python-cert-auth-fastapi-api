# Multi-stage Dockerfile for Blog API
# Stage 1: Builder - Install dependencies
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev dependencies)
RUN poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Runtime - Create minimal production image
FROM python:3.10-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=production

# Create non-root user
RUN groupadd -r apiuser && useradd -r -g apiuser apiuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=apiuser:apiuser /app/.venv /app/.venv

# Copy application code
COPY --chown=apiuser:apiuser ./src ./src
COPY --chown=apiuser:apiuser ./pyproject.toml ./

# Create directory for database (if using SQLite)
RUN mkdir -p /app/data && chown apiuser:apiuser /app/data

# Switch to non-root user
USER apiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
