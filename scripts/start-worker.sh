#!/bin/bash

# Set environment variables for Python/Cairo on macOS
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

cd "$(dirname "$0")/../apps/api"

# Set Python path
export PYTHONPATH="$(pwd)"

echo "⚙️ Starting EPUB Translator Worker..."
echo "🔗 Connecting to Redis at: redis://localhost:6379"
echo "📋 Queue: translate"
echo "⚠️  Make sure Redis is running: brew services start redis"
echo ""

# Start the RQ worker
poetry run rq worker translate --url redis://localhost:6379