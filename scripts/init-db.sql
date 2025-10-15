-- Initialize PostgreSQL database for OpenThreat
-- This script runs automatically when the database is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Trigram extension for fuzzy text search
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- GIN index support for btree types

-- Create schema if needed (optional, using public schema by default)
-- CREATE SCHEMA IF NOT EXISTS openthreat;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE openthreat TO openthreat;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'OpenThreat database initialized successfully';
    RAISE NOTICE 'Extensions enabled: pg_trgm, btree_gin';
END $$;
