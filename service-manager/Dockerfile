FROM python:3.12-alpine

# Install only essential packages for security and functionality
RUN apk add --no-cache \
    curl \
    docker-cli \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers \
    make \
    && rm -rf /var/cache/apk/* \
    && rm -rf /tmp/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY service_manager.py service_manager_simple.py pyproject.toml ./
COPY tests ./tests

# Create non-root user for runtime
RUN adduser -D -u 1000 serviceuser && chown -R serviceuser:serviceuser /app
USER serviceuser

# Set secure environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Optimized health check with proper error handling and timeout
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f --max-time 5 http://localhost:9000/health || exit 1

EXPOSE 9000

# Use optimized Python flags for performance
CMD ["python3", "-u", "-m", "service_manager"]
