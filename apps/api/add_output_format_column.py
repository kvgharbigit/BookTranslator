#!/usr/bin/env python3
"""
Migration script to add output_format column to jobs table.
Run this once to update the Railway PostgreSQL database schema.

Usage:
    railway run python add_output_format_column.py
"""

from sqlalchemy import text
from app.db import engine
from app.logger import get_logger

logger = get_logger(__name__)


def migrate():
    """Add output_format column to jobs table if it doesn't exist."""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='jobs' AND column_name='output_format'
            """))

            if result.fetchone():
                logger.info("✅ Column 'output_format' already exists in jobs table")
                return

            # Add the column
            logger.info("Adding 'output_format' column to jobs table...")
            conn.execute(text("""
                ALTER TABLE jobs
                ADD COLUMN output_format VARCHAR DEFAULT 'translation'
            """))
            conn.commit()

            logger.info("✅ Successfully added 'output_format' column to jobs table")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    migrate()
