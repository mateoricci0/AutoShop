#!/bin/bash
# migrate.sh — Run Alembic migrations against the running PostgreSQL container
set -e

cd "$(dirname "$0")/.."

DOCKER_COMPOSE="docker compose"
COMPOSE_FILE="infra/docker/docker-compose.yml"

echo "Running Alembic migrations..."

# Source .env for POSTGRES_PASSWORD if available
if [ -f .env ]; then
    set -a
    # shellcheck source=/dev/null
    . .env
    set +a
fi

POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-ase_dev_password}"

$DOCKER_COMPOSE -f "$COMPOSE_FILE" run --rm \
    -e DATABASE_URL="postgresql+asyncpg://ase_app:${POSTGRES_PASSWORD}@postgres:5432/ase" \
    auth \
    python -m alembic \
        -c /shared/ase_shared/database/migrations/alembic.ini \
        upgrade head

echo "Migrations complete"
