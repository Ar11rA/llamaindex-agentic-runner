# Build stage
# Using slim (Debian) instead of alpine because:
# - asyncpg requires glibc (alpine uses musl)
# - LlamaIndex/OpenTelemetry have C extensions optimized for glibc
# - Pre-built wheels available = faster builds
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-dev --no-install-project

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
# - libpq5: PostgreSQL client library for asyncpg
# - curl: For Docker healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Install the project itself
RUN uv sync --no-dev

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 6001

# Run the application
# Uvicorn flags:
# --log-level info: Log level for uvicorn
# --access-log: Enable access logging (requests)
# --proxy-headers: Trust X-Forwarded-* headers from nginx
# --forwarded-allow-ips='*': Accept forwarded headers from Docker network
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6001", "--log-level", "info", "--access-log", "--proxy-headers", "--forwarded-allow-ips", "*"]

