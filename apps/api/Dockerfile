FROM python:3.11-slim

# Install system dependencies
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
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY app/ ./app/
COPY supervisord.conf ./

# Create data directory for SQLite
RUN mkdir -p /app/data

# Create directories for temporary files
RUN mkdir -p /tmp/epub-processing

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run supervisord (manages both FastAPI and RQ worker)
CMD ["supervisord", "-c", "supervisord.conf"]