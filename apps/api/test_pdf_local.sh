#!/bin/bash
# Helper script to test bilingual PDF generation locally with Homebrew libraries

# Set library path for WeasyPrint to find Homebrew-installed Pango/Cairo
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Run the test
cd "$(dirname "$0")"
PYTHONPATH=. python app/html_to_pdf.py
