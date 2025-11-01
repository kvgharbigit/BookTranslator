#!/bin/bash

cd "$(dirname "$0")/../apps/web"

echo "💻 Starting EPUB Translator Frontend..."
echo "📍 Frontend will be available at: http://localhost:3000"
echo "🔗 Make sure backend is running at: http://localhost:8000"
echo ""

# Start the Next.js development server
npm run dev