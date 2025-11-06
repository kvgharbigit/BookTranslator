#!/bin/bash
# Project Cleanup Script for BookTranslator

echo "🧹 Cleaning up BookTranslator project..."

# 1. Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# 2. Remove .DS_Store files (macOS)
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null

# 3. Remove old log files
echo "Removing old log files..."
rm -f test_output.log test_output_full.log

# 4. Remove old .pack files from Next.js
echo "Removing old Next.js cache files..."
find apps/web/.next/cache -name "*.old" -delete 2>/dev/null

# 5. Create scripts directory and move test scripts
echo "Organizing test scripts..."
mkdir -p scripts
mv test_all_languages.py scripts/ 2>/dev/null
mv test_failing_languages.py scripts/ 2>/dev/null

# 6. Create archive directory for old debug scripts
echo "Archiving old debug scripts..."
mkdir -p scripts/archive
mv debug_*.py scripts/archive/ 2>/dev/null
mv test_pdf_fix.py scripts/archive/ 2>/dev/null
mv test_toc_fix.py scripts/archive/ 2>/dev/null
mv fix_txt_format.py scripts/archive/ 2>/dev/null
mv run_tests.py scripts/archive/ 2>/dev/null
mv epub_to_pdf_with_images.py scripts/archive/ 2>/dev/null

# 7. Keep only latest test results
echo "Organizing test results..."
# Keep test_results directory as is (already organized)

echo "✅ Cleanup complete!"
echo ""
echo "📁 Project structure:"
echo "  - scripts/              (test scripts)"
echo "  - scripts/archive/      (old debug scripts)"
echo "  - test_results/         (test output)"
echo "  - docs/                 (documentation)"
echo "  - apps/                 (application code)"
echo "  - sample_books/         (test EPUBs)"
