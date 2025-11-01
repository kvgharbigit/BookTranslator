#!/bin/bash

# Set environment variables for Python/Cairo on macOS
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

cd "$(dirname "$0")/../apps/api"

# Set Python path
export PYTHONPATH="$(pwd)"

echo "🚀 Starting EPUB Translator Backend..."
echo "📍 Backend will be available at: http://localhost:8000"
echo "🔍 Health check: http://localhost:8000/health"
echo "⚠️  Make sure Redis is running: brew services start redis"
echo ""

# Start the FastAPI server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000