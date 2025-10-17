-- Performance optimization indexes for dashboard queries
-- Run this on production database

-- Composite index for CVE filtering + severity/exploited queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vuln_cve_severity_exploited 
ON vulnerabilities (cve_id, severity, exploited_in_the_wild) 
WHERE cve_id LIKE 'CVE-%';

-- Index for recent updates query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vuln_cve_updated 
ON vulnerabilities (updated_at DESC) 
WHERE cve_id LIKE 'CVE-%';

-- Index for LLM processing status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vuln_llm_processed 
ON vulnerabilities (llm_processed, llm_processed_at);

-- Analyze tables after index creation
ANALYZE vulnerabilities;
