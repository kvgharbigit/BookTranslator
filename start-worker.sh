#!/bin/bash
echo "⚙️ Starting EPUB Translator Worker..."
echo "Make sure Redis is running: brew services start redis"
echo ""

cd "$(dirname "$0")"

# Set environment
export PYTHONPATH="$(pwd)"

# Start the RQ worker
echo "Starting RQ worker for translation jobs..."
poetry run rq worker translate --url redis://localhost:6379