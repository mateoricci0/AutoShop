#!/bin/bash
# setup.sh — Bootstrap the ASE development environment
# Run once after cloning: bash scripts/setup.sh
set -e

cd "$(dirname "$0")/.."

echo "Setting up ASE..."

# ── Dependency checks ────────────────────────────────────────────────────────

command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not found. Install Docker Desktop or Docker Engine."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 not found."; exit 1; }

DOCKER_COMPOSE="docker compose"
$DOCKER_COMPOSE version >/dev/null 2>&1 || {
    echo "ERROR: 'docker compose' (v2) not found. Update Docker or install the compose plugin."
    exit 1
}

echo "  docker: $(docker --version)"
echo "  python: $(python3 --version)"

# ── Secrets ──────────────────────────────────────────────────────────────────

if [ ! -f .env.local ]; then
    echo ""
    echo "No .env.local found. Generating secrets..."
    bash scripts/generate-keys.sh
else
    echo "  .env.local already exists — skipping key generation"
fi

# ── .env file ────────────────────────────────────────────────────────────────

if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example (add your API keys)"
else
    echo "  .env already exists"
fi

# Merge .env.local into .env for Docker Compose
if [ -f .env.local ]; then
    echo "  Merging .env.local into .env..."
    while IFS= read -r line; do
        # Skip comments and blank lines
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        KEY="${line%%=*}"
        # Only add if key doesn't already have a non-empty value in .env
        CURRENT=$(grep "^${KEY}=" .env 2>/dev/null | cut -d= -f2-)
        if [ -z "$CURRENT" ]; then
            # Update the key in .env
            if grep -q "^${KEY}=" .env 2>/dev/null; then
                sed -i "s|^${KEY}=.*|${line}|" .env
            else
                echo "$line" >> .env
            fi
        fi
    done < .env.local
fi

# ── Build images ─────────────────────────────────────────────────────────────

echo ""
echo "Building Docker images (this may take a few minutes)..."
$DOCKER_COMPOSE -f infra/docker/docker-compose.yml build --parallel

# ── Start infrastructure ─────────────────────────────────────────────────────

echo ""
echo "Starting infrastructure services..."
$DOCKER_COMPOSE -f infra/docker/docker-compose.yml up -d postgres redis minio

# ── Wait for PostgreSQL ───────────────────────────────────────────────────────

echo "Waiting for PostgreSQL to be ready..."
RETRIES=30
until $DOCKER_COMPOSE -f infra/docker/docker-compose.yml exec -T postgres \
    pg_isready -U ase_app -d ase >/dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        echo "ERROR: PostgreSQL did not become ready in time."
        exit 1
    fi
    sleep 2
done
echo "  PostgreSQL is ready"

# ── Run migrations ────────────────────────────────────────────────────────────

echo ""
echo "Running database migrations..."
bash scripts/migrate.sh

# ── Seed defaults ─────────────────────────────────────────────────────────────

echo ""
echo "Seeding default settings..."
bash scripts/seed.sh

echo ""
echo "Setup complete!"
echo ""
echo "Start all services:"
echo "  docker compose -f infra/docker/docker-compose.yml up"
echo ""
echo "Start with hot reload (development):"
echo "  docker compose -f infra/docker/docker-compose.yml \\"
echo "                 -f infra/docker/docker-compose.dev.yml up"
echo ""
echo "Access URLs:"
echo "  Dashboard:  http://localhost"
echo "  Grafana:    http://localhost:3001  (admin / \${GRAFANA_PASSWORD:-admin})"
echo "  MinIO:      http://localhost:9001  (minioadmin / minioadmin)"
echo "  Prometheus: http://localhost:9090"
