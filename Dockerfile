# Orchestra AI Agent System Dockerfile
FROM python:3.12.7-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1

# Install system dependencies with security updates
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Install Poetry and update setuptools for security
RUN pip install --upgrade setuptools>=78.1.1 \
    && pip install poetry==$POETRY_VERSION

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root \
    && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Install the application
RUN poetry install --only main

# Create non-root user for security
RUN groupadd -r orchestra && useradd -r -g orchestra orchestra
RUN chown -R orchestra:orchestra /app
USER orchestra

# Expose port for health checks
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import src; print('Orchestra is healthy')" || exit 1

# Default command
CMD ["python", "-m", "src.cli.main", "--help"]
