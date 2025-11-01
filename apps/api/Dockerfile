FROM python:3.11-slim

# Install system dependencies including PDF generation tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    supervisor \
    calibre \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy Poetry files from apps/api directory (Railway builds from repo root)
COPY apps/api/pyproject.toml apps/api/poetry.lock ./

# Configure Poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --only=main --no-root --no-interaction --no-ansi

# Copy application code from apps/api directory
COPY apps/api/app/ ./app/
COPY apps/api/supervisord.conf ./

# Create directories for storage and processing
RUN mkdir -p /app/data /app/local_storage/uploads /app/local_storage/outputs /tmp/epub-processing

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Expose port
EXPOSE 8000

# Run supervisord (manages both FastAPI and RQ worker)
CMD ["supervisord", "-c", "supervisord.conf"]