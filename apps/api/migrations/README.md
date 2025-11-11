# Database Migrations

This directory contains database migration scripts for the BookTranslator API.

## Running Migrations

### On Railway (Production)

1. Connect to your Railway deployment:
   ```bash
   railway link
   ```

2. Run the migration using Railway CLI:
   ```bash
   railway run python migrations/001_add_bilingual_keys.py
   ```

   OR connect to the PostgreSQL database directly:
   ```bash
   railway run psql $DATABASE_URL
   ```

   Then manually run the SQL:
   ```sql
   ALTER TABLE jobs ADD COLUMN bilingual_epub_key VARCHAR;
   ALTER TABLE jobs ADD COLUMN bilingual_pdf_key VARCHAR;
   ALTER TABLE jobs ADD COLUMN bilingual_txt_key VARCHAR;
   ```

### On Local Development

```bash
cd apps/api
set -a && source .env.local && set +a
PYTHONPATH=. python migrations/001_add_bilingual_keys.py
```

## Migration History

### 001_add_bilingual_keys.py

**Date:** 2025-11-11
**Purpose:** Add support for storing bilingual file references

Adds three new columns to the `jobs` table:
- `bilingual_epub_key` - R2 storage key for bilingual EPUB file
- `bilingual_pdf_key` - R2 storage key for bilingual PDF file
- `bilingual_txt_key` - R2 storage key for bilingual TXT file

These columns enable the "both" output format to properly display all 6 download files (3 regular + 3 bilingual) in the UI.

**Impact:** Non-breaking - existing jobs continue to work, new jobs with "bilingual" or "both" formats will populate these fields.
