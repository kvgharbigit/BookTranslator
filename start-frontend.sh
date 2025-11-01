#!/bin/bash
echo "💻 Starting EPUB Translator Frontend..."
echo ""

cd "$(dirname "$0")/apps/web"

# Start the Next.js development server
echo "Starting Next.js frontend on http://localhost:3000..."
npm run dev