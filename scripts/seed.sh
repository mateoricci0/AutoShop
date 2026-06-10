#!/bin/bash
# seed.sh — Insert default settings and seed data for development
set -e

cd "$(dirname "$0")/.."

DOCKER_COMPOSE="docker compose"
COMPOSE_FILE="infra/docker/docker-compose.yml"

echo "Seeding default settings..."

$DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T postgres psql -U ase_app -d ase <<'SQL'
-- Default agent settings
INSERT INTO settings (category, key, value) VALUES
    ('agents',        'product_hunter.enabled',  '"true"'),
    ('agents',        'product_hunter.sources',   '["tiktok_creative","aliexpress","amazon","reddit"]'),
    ('agents',        'product_hunter.interval_hours', '6'),
    ('scoring',       'auto_approve_threshold',   '75'),
    ('scoring',       'min_margin_percent',        '30'),
    ('notifications', 'channels',                 '[]'),
    ('analytics',     'collect_interval_hours',   '6'),
    ('analytics',     'roas_scale_threshold',     '3.0'),
    ('analytics',     'roas_optimize_threshold',  '1.0'),
    ('analytics',     'min_spend_usd',            '20.0')
ON CONFLICT (category, key) DO NOTHING;
SQL

echo "Default settings seeded"
