# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv (modern Python dependency manager)
RUN pip install uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv && \
    .venv/bin/uv pip install --no-cache-dir -r <(uv pip compile pyproject.toml)

# Copy application code
COPY app/ ./app/
COPY database/ ./database/

# Add .venv to PATH and set Python environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

# Default command
CMD ["python", "-m", "app.main"]
