#!/bin/bash
echo "🚀 Starting EPUB Translator Backend..."
echo "Make sure Redis is running: brew services start redis"
echo ""

cd "$(dirname "$0")"

# Set environment
export PYTHONPATH="$(pwd)"

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8000..."
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000