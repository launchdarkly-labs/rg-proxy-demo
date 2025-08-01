# Use Alpine Linux 3.22.1
FROM alpine:3.22.1

# Set working directory
WORKDIR /app

# Install system dependencies including Python
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    wget \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application files
COPY service.py .
COPY blue.yaml .
COPY green.yaml .

# Create non-root user for security
RUN adduser -D -s /bin/sh appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port the service runs on
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV CONFIG_PATH=config.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the service
CMD ["python3", "service.py"]
