-- Migration: Create page_views table for site analytics
-- This migration is idempotent and safe to run multiple times

-- Create page_views table
CREATE TABLE IF NOT EXISTS page_views (
    id SERIAL PRIMARY KEY,
    path VARCHAR(500) NOT NULL,
    referrer VARCHAR(1000),
    visitor_id VARCHAR(64),
    country VARCHAR(100),
    city VARCHAR(200),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_page_views_path ON page_views(path);
CREATE INDEX IF NOT EXISTS idx_page_views_visitor_id ON page_views(visitor_id);
CREATE INDEX IF NOT EXISTS idx_page_views_country ON page_views(country);
CREATE INDEX IF NOT EXISTS idx_page_views_created_at ON page_views(created_at);
CREATE INDEX IF NOT EXISTS idx_page_views_path_created ON page_views(path, created_at);
CREATE INDEX IF NOT EXISTS idx_page_views_date ON page_views(created_at);

-- Add comment
COMMENT ON TABLE page_views IS 'Stores anonymous page view data for site analytics';
