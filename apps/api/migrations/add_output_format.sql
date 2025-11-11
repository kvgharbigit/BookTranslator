-- Migration: Add output_format column to jobs table
-- Run this on Railway PostgreSQL database

-- Add output_format column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='jobs' AND column_name='output_format'
    ) THEN
        ALTER TABLE jobs
        ADD COLUMN output_format VARCHAR DEFAULT 'translation';

        RAISE NOTICE 'Added output_format column to jobs table';
    ELSE
        RAISE NOTICE 'Column output_format already exists in jobs table';
    END IF;
END $$;
