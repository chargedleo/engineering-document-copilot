FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered streaming logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies including Tesseract OCR engine, English language data,
# and headless graphics libraries for OpenCV (libgl1, libglib2.0-0)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first to optimize Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create an unprivileged user and directories for uploaded/processed documents
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 -d /app appuser \
    && mkdir -p /app/data/documents /app/data/processed \
    && chown -R appuser:appgroup /app

# Copy application source code into container
COPY . .

# Normalize shell line endings and ensure entrypoint script permissions
RUN sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && chown -R appuser:appgroup /app

# Run as non-root user
USER appuser

# Expose backend API port
EXPOSE 8000

# Container healthcheck using FastAPI liveness endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
