# Output Format Migration - Summary

## Issue
Database error when creating jobs: `table jobs has no column named output_format`

## Root Cause
The `output_format` column was added to the SQLAlchemy model (`app/models.py`) but not to the PostgreSQL database schema on Railway.

## Solution Implemented

### 1. **Removed SQLite Fallback** ✅
- Removed default SQLite database URL from config
- Now requires `DATABASE_URL` environment variable (Railway PostgreSQL)
- Updated `apps/api/app/config/__init__.py` line 14

### 2. **Added Migration Column** ✅
- Ran SQL migration directly on Railway PostgreSQL:
  ```sql
  ALTER TABLE jobs ADD COLUMN IF NOT EXISTS output_format VARCHAR DEFAULT 'translation';
  ```
- Column successfully added with correct default value

### 3. **Updated Local Environment** ✅
- Updated `.env` file to use Railway PostgreSQL instead of SQLite
- Deleted local `jobs.db` files
- Added `*.db` to `.gitignore`

### 4. **Created Automatic Migration System** ✅
- Created `app/migrations.py` with migration functions
- Updated `app/main.py` to run migrations on startup
- Migrations are idempotent (safe to run multiple times)

### 5. **Verified with Tests** ✅
- Created test scripts to verify column exists
- Confirmed column has correct type (`VARCHAR`) and default (`'translation'`)
- Exit code 0 = all tests passed

## Database Schema

The `output_format` column now supports three values:
- **`'translation'`** (default) - Translation-only output (EPUB + PDF + TXT)
- **`'bilingual'`** - Bilingual reader output (side-by-side original + translation)
- **`'both'`** - Both formats (translation + bilingual)

## Files Modified

1. `apps/api/app/config/__init__.py` - Removed SQLite fallback
2. `apps/api/app/migrations.py` - Created (automatic migrations)
3. `apps/api/app/main.py` - Added migration runner on startup
4. `apps/api/.env` - Updated to use Railway PostgreSQL
5. `apps/api/.gitignore` - Added `*.db` files

## Files Created

1. `apps/api/migrations/add_output_format.sql` - SQL migration script
2. `apps/api/test_output_format_simple.py` - Verification test
3. `apps/api/OUTPUT_FORMAT_MIGRATION_SUMMARY.md` - This document

## Verification

Run the test to verify the migration:
```bash
cd apps/api
PYTHONPATH=. python test_output_format_simple.py
```

Expected output: Exit code 0 (success)

## Status: ✅ COMPLETE

The `output_format` column is now available in production and ready to use in all API endpoints.

---
*Migration completed: 2025-11-11*
