# Database Migration Guide

## Comments Schema Fix (October 2025)

### Problem
The comments functionality was broken due to schema mismatch between the database and the model.

### Solution
A migration script has been created to fix the schema.

## For Existing Deployments

If you have an existing database, run this migration **once**:

```bash
# Option 1: Using docker compose
cat backend/migrations/fix_comments_schema.sql | docker compose exec -T postgres psql -U openthreat -d openthreat

# Option 2: Copy and run inside container
docker compose exec postgres psql -U openthreat -d openthreat < backend/migrations/fix_comments_schema.sql
```

## For New Deployments

The migration is included in `scripts/init-db.sql` and will run automatically on first database creation.

## What the Migration Does

1. Adds `cve_id` column to `comments` table
2. Migrates data from `vulnerability_id` to `cve_id`
3. Renames `edited` to `is_edited`
4. Adds `upvotes` and `downvotes` columns
5. Makes `vulnerability_id` nullable
6. Adds `updated_at` to `comment_votes` table
7. Converts `vote_type` from VARCHAR to INTEGER

## Verification

After running the migration, verify it worked:

```bash
# Check comments table schema
docker compose exec postgres psql -U openthreat -d openthreat -c "\d comments"

# Test the API
curl -k "https://localhost/api/v1/vulnerabilities/CVE-2024-12345/comments?page=1&page_size=20"
```

You should see a 200 response with `{"comments":[],"total":0,"page":1,"page_size":20}` if no comments exist yet.

## Files to Commit

- ✅ `backend/migrations/fix_comments_schema.sql` - The migration script
- ✅ `backend/migrations/README.md` - Migration documentation
- ✅ `backend/migrations/run_migrations.py` - Automatic migration runner (for future use)
- ✅ `backend/main.py` - Updated with migration runner
- ✅ `scripts/init-db.sql` - Updated with migration logic for new deployments
- ✅ `MIGRATION_GUIDE.md` - This file

## Important Notes

- ⚠️ The migration is **idempotent** - safe to run multiple times
- ⚠️ Backup your database before running migrations in production
- ⚠️ The old `vulnerability_id` column is kept for safety (can be dropped later)
- ✅ No downtime required - the migration is non-blocking
