# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq-dev \
        pkg-config \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./

# Install dependencies using UV
RUN uv pip install .

# Copy the rest of the project files
COPY . .

# Create a non-root user
RUN useradd -m -s /bin/bash app_user \
    && chown -R app_user:app_user /app

# Switch to non-root user
USER app_user

# Command to run the application
CMD ["python", "-m", "app.main"]