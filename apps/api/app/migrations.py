"""Database migrations - run automatically on startup."""

from sqlalchemy import text, inspect
from app.db import engine
from app.logger import get_logger

logger = get_logger(__name__)


def run_migrations():
    """Run all pending database migrations."""
    logger.info("Running database migrations...")

    _add_output_format_column()

    logger.info("✅ All migrations completed")


def _add_output_format_column():
    """Add output_format column to jobs table if it doesn't exist."""
    try:
        with engine.connect() as conn:
            # Check if column already exists using inspector
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('jobs')]

            if 'output_format' in columns:
                logger.info("Column 'output_format' already exists in jobs table")
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
        logger.error(f"Migration failed: {e}", exc_info=True)
        # Don't crash the app if migration fails - table might already exist
        logger.warning("Continuing despite migration error...")
