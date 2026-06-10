#!/bin/bash
# seed.sh — Insert default settings and seed data for development
set -e

cd "$(dirname "$0")/.."

DOCKER_COMPOSE="docker compose"
COMPOSE_FILE="infra/docker/docker-compose.yml"

echo "Seeding default settings..."

$DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T postgres psql -U ase_app -d ase <<'SQL'
-- Default agent settings (store_id = NULL means global scope)
INSERT INTO settings (store_id, category, key, value) VALUES
    (NULL, 'agents',        'product_hunter.enabled',       '"true"'),
    (NULL, 'agents',        'product_hunter.sources',       '["tiktok_creative","aliexpress","amazon","reddit"]'),
    (NULL, 'agents',        'product_hunter.interval_hours', '6'),
    (NULL, 'scoring',       'auto_approve_threshold',       '75'),
    (NULL, 'scoring',       'min_margin_percent',           '30'),
    (NULL, 'notifications', 'channels',                     '[]'),
    (NULL, 'analytics',     'collect_interval_hours',       '6'),
    (NULL, 'analytics',     'roas_scale_threshold',         '3.0'),
    (NULL, 'analytics',     'roas_optimize_threshold',      '1.0'),
    (NULL, 'analytics',     'min_spend_usd',                '20.0')
ON CONFLICT DO NOTHING;
SQL

echo "Default settings seeded"
