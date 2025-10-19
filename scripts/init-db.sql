-- Initialize PostgreSQL database for OpenThreat
-- This script runs automatically when the database is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Trigram extension for fuzzy text search
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- GIN index support for btree types

-- Create schema if needed (optional, using public schema by default)
-- CREATE SCHEMA IF NOT EXISTS openthreat;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE openthreat TO openthreat;

-- Apply migrations if tables exist (for existing databases)
-- This is safe to run multiple times due to IF EXISTS/IF NOT EXISTS checks

-- Fix comments table schema (if it exists)
DO $$
BEGIN
    -- Check if comments table exists and needs migration
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'comments') THEN
        -- Add cve_id column if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'cve_id') THEN
            ALTER TABLE comments ADD COLUMN cve_id VARCHAR(50);

            -- Populate from vulnerability_id if it exists
            IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'vulnerability_id') THEN
                UPDATE comments c SET cve_id = v.cve_id FROM vulnerabilities v WHERE c.vulnerability_id = v.id;
            END IF;

            ALTER TABLE comments ALTER COLUMN cve_id SET NOT NULL;
            ALTER TABLE comments ADD CONSTRAINT comments_cve_id_fkey FOREIGN KEY (cve_id) REFERENCES vulnerabilities(cve_id);
            CREATE INDEX IF NOT EXISTS idx_comments_cve_id ON comments(cve_id);
            CREATE INDEX IF NOT EXISTS idx_comments_cve_created ON comments(cve_id, created_at);

            RAISE NOTICE 'Comments table: Added cve_id column';
        END IF;

        -- Rename edited to is_edited if needed
        IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'edited') THEN
            ALTER TABLE comments RENAME COLUMN edited TO is_edited;
            RAISE NOTICE 'Comments table: Renamed edited to is_edited';
        END IF;

        -- Add upvotes/downvotes if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'upvotes') THEN
            ALTER TABLE comments ADD COLUMN upvotes INTEGER DEFAULT 0 NOT NULL;
            ALTER TABLE comments ADD COLUMN downvotes INTEGER DEFAULT 0 NOT NULL;
            RAISE NOTICE 'Comments table: Added upvotes/downvotes columns';
        END IF;

        -- Make vulnerability_id nullable
        IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'vulnerability_id' AND is_nullable = 'NO') THEN
            ALTER TABLE comments ALTER COLUMN vulnerability_id DROP NOT NULL;
            RAISE NOTICE 'Comments table: Made vulnerability_id nullable';
        END IF;
    END IF;

    -- Fix comment_votes table (if it exists)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'comment_votes') THEN
        -- Add updated_at if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comment_votes' AND column_name = 'updated_at') THEN
            ALTER TABLE comment_votes ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;
            RAISE NOTICE 'Comment_votes table: Added updated_at column';
        END IF;

        -- Fix vote_type to be INTEGER
        IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'comment_votes' AND column_name = 'vote_type' AND data_type != 'integer') THEN
            ALTER TABLE comment_votes ALTER COLUMN vote_type TYPE INTEGER
            USING CASE
                WHEN vote_type = 'upvote' THEN 1
                WHEN vote_type = 'downvote' THEN -1
                ELSE vote_type::INTEGER
            END;
            RAISE NOTICE 'Comment_votes table: Converted vote_type to INTEGER';
        END IF;
    END IF;
END $$;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'OpenThreat database initialized successfully';
    RAISE NOTICE 'Extensions enabled: pg_trgm, btree_gin';
END $$;
