-- 002_add_status.sql
ALTER TABLE items ADD COLUMN status TEXT NOT NULL DEFAULT 'active';