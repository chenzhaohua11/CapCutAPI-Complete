# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set build arguments
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libopencv-dev \
    ffmpeg \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt requirements-mcp.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir -r requirements-mcp.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Copy Python packages from builder
COPY --from=builder /home/appuser/.local /home/appuser/.local

# Set work directory and permissions
WORKDIR /app
RUN chown appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p drafts media logs templates pattern

# Create configuration from example
RUN cp config.json.example config.json || true

# Expose ports
EXPOSE 9001 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9001/health', timeout=5)" || exit 1

# Default environment
ENV FLASK_ENV=production \
    PYTHONPATH=/app

# Start application
CMD ["python", "capcut_server.py"]