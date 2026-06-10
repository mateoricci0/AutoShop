-- init-db.sql — PostgreSQL initialization script
-- Runs as superuser on first container start (before Alembic migrations).
-- Tables and indexes are created by Alembic (run: scripts/migrate.sh).
-- This file only installs extensions that require superuser privileges.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
