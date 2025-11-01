-- Add progress_percent column to jobs table
-- Run this on Railway PostgreSQL database

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS progress_percent INTEGER DEFAULT 0;

-- Update existing jobs to have 100% if they are done
UPDATE jobs SET progress_percent = 100 WHERE status = 'done';

-- Update existing jobs to have 0% if they are queued
UPDATE jobs SET progress_percent = 0 WHERE status = 'queued';

-- Show results
SELECT id, status, progress_step, progress_percent FROM jobs LIMIT 10;
