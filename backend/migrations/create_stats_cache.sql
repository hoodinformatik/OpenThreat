-- Create a materialized stats cache table for fast dashboard queries
-- This avoids scanning 300k+ rows on every stats request

CREATE TABLE IF NOT EXISTS vulnerability_stats_cache (
    id SERIAL PRIMARY KEY,
    total_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    exploited_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    critical_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    high_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    medium_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    low_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    unknown_vulnerabilities INTEGER NOT NULL DEFAULT 0,
    recent_updates INTEGER NOT NULL DEFAULT 0,
    last_calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT single_row_only CHECK (id = 1)
);

-- Insert initial row
INSERT INTO vulnerability_stats_cache (id) VALUES (1)
ON CONFLICT (id) DO NOTHING;

-- Function to refresh stats cache
CREATE OR REPLACE FUNCTION refresh_vulnerability_stats_cache()
RETURNS void AS $$
DECLARE
    v_total INTEGER;
    v_exploited INTEGER;
    v_critical INTEGER;
    v_high INTEGER;
    v_medium INTEGER;
    v_low INTEGER;
    v_unknown INTEGER;
    v_recent INTEGER;
BEGIN
    -- Calculate all stats in one query
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE exploited_in_the_wild = true),
        COUNT(*) FILTER (WHERE severity = 'CRITICAL'),
        COUNT(*) FILTER (WHERE severity = 'HIGH'),
        COUNT(*) FILTER (WHERE severity = 'MEDIUM'),
        COUNT(*) FILTER (WHERE severity = 'LOW'),
        COUNT(*) FILTER (WHERE severity IS NULL OR severity = 'UNKNOWN'),
        COUNT(*) FILTER (WHERE published_at >= NOW() - INTERVAL '7 days')
    INTO
        v_total,
        v_exploited,
        v_critical,
        v_high,
        v_medium,
        v_low,
        v_unknown,
        v_recent
    FROM vulnerabilities
    WHERE cve_id LIKE 'CVE-%';

    -- Update cache table
    UPDATE vulnerability_stats_cache
    SET
        total_vulnerabilities = v_total,
        exploited_vulnerabilities = v_exploited,
        critical_vulnerabilities = v_critical,
        high_vulnerabilities = v_high,
        medium_vulnerabilities = v_medium,
        low_vulnerabilities = v_low,
        unknown_vulnerabilities = v_unknown,
        recent_updates = v_recent,
        last_calculated_at = NOW()
    WHERE id = 1;
END;
$$ LANGUAGE plpgsql;

-- Initial calculation
SELECT refresh_vulnerability_stats_cache();

-- Create index on published_at for recent updates query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_published_at
ON vulnerabilities (published_at DESC)
WHERE cve_id LIKE 'CVE-%';

ANALYZE vulnerability_stats_cache;
ANALYZE vulnerabilities;
