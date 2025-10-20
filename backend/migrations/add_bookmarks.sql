-- Migration: Add bookmarks table for user watchlist
-- Users can bookmark CVEs to track them

CREATE TABLE IF NOT EXISTS bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cve_id VARCHAR(50) NOT NULL REFERENCES vulnerabilities(cve_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    notes TEXT,
    UNIQUE(user_id, cve_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_cve_id ON bookmarks(cve_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON bookmarks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_created ON bookmarks(user_id, created_at DESC);

-- Add bookmark count to vulnerabilities for denormalization (optional)
ALTER TABLE vulnerabilities ADD COLUMN IF NOT EXISTS bookmark_count INTEGER DEFAULT 0 NOT NULL;
