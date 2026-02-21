FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy health check application
COPY health_check.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash healthcheck
USER healthcheck

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --self-check || exit 1

EXPOSE 8000

CMD ["python", "health_check.py", "--server"]
