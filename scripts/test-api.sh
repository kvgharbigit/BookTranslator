#!/bin/bash
echo "🧪 Testing EPUB Translator API..."
echo ""

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Test root endpoint
echo "Testing root endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

echo "✅ API test complete!"
echo "If you see JSON responses above, the API is working!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Try uploading an EPUB file"
echo "3. Test the complete user flow"