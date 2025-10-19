# Database Migrations

This directory contains SQL migration files that are automatically executed when the backend starts.

## How it works

1. **Automatic Execution**: All `.sql` files in this directory are executed automatically on backend startup
2. **Idempotent**: Migrations use `IF EXISTS` / `IF NOT EXISTS` checks, making them safe to run multiple times
3. **Ordered**: Migrations are executed in alphabetical order by filename

## Adding a new migration

1. Create a new `.sql` file with a descriptive name (e.g., `fix_comments_schema.sql`)
2. Use idempotent SQL statements (with `IF EXISTS` / `IF NOT EXISTS`)
3. Test the migration locally
4. Commit and push - it will run automatically on next deployment

## Example migration structure

```sql
-- Migration: Description of what this does
-- Date: YYYY-MM-DD

-- Add column if it doesn't exist
ALTER TABLE my_table
ADD COLUMN IF NOT EXISTS new_column VARCHAR(50);

-- Create index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_my_table_column
ON my_table(new_column);

-- Conditional updates
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.columns
               WHERE table_name = 'my_table'
               AND column_name = 'old_column') THEN
        -- Do something
    END IF;
END $$;
```

## Current migrations

- `fix_comments_schema.sql` - Fixes comments table schema to match the model
  - Adds `cve_id` column
  - Renames `edited` to `is_edited`
  - Adds `upvotes` and `downvotes` columns
  - Makes `vulnerability_id` nullable
  - Fixes `comment_votes` table schema

## Manual execution

If you need to run migrations manually:

```bash
# From host machine
cat backend/migrations/your_migration.sql | docker compose exec -T postgres psql -U openthreat -d openthreat

# Or inside the container
docker compose exec postgres psql -U openthreat -d openthreat -f /path/to/migration.sql
```

## Best practices

1. ✅ Always use `IF EXISTS` / `IF NOT EXISTS`
2. ✅ Make migrations idempotent (safe to run multiple times)
3. ✅ Test migrations on a copy of production data
4. ✅ Use descriptive filenames
5. ✅ Add comments explaining what the migration does
6. ❌ Never drop data without a backup
7. ❌ Never use `DROP TABLE` without `IF EXISTS`
