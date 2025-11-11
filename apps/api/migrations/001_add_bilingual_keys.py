#!/usr/bin/env python3
"""
Migration: Add bilingual file key columns to jobs table

Run this migration on production database to add support for storing
bilingual file references when output_format is "bilingual" or "both".

Usage:
    PYTHONPATH=. python migrations/001_add_bilingual_keys.py
"""

from sqlalchemy import text
from app.db import engine
from app.logger import get_logger

logger = get_logger(__name__)


def migrate():
    """Add bilingual_epub_key, bilingual_pdf_key, bilingual_txt_key columns to jobs table."""

    with engine.connect() as conn:
        try:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'jobs'
                AND column_name IN ('bilingual_epub_key', 'bilingual_pdf_key', 'bilingual_txt_key')
            """))
            existing_cols = {row[0] for row in result}

            # Add missing columns
            columns_to_add = []
            if 'bilingual_epub_key' not in existing_cols:
                columns_to_add.append("bilingual_epub_key VARCHAR")
            if 'bilingual_pdf_key' not in existing_cols:
                columns_to_add.append("bilingual_pdf_key VARCHAR")
            if 'bilingual_txt_key' not in existing_cols:
                columns_to_add.append("bilingual_txt_key VARCHAR")

            if not columns_to_add:
                logger.info("✅ All bilingual key columns already exist")
                return

            # Add each column
            for col_definition in columns_to_add:
                col_name = col_definition.split()[0]
                conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col_definition}"))
                conn.commit()
                logger.info(f"✅ Added column: {col_name}")

            logger.info(f"✅ Migration complete! Added {len(columns_to_add)} column(s)")

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    logger.info("Starting migration: Add bilingual file key columns")
    migrate()
