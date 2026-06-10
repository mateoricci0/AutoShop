# Autonomous Shopify Engine (ASE)

ASE is a personal-use multi-agent platform that automatically discovers winning products, generates marketing content, publishes to Shopify stores, and monitors ROAS — all running locally on a single machine with Docker Compose.

## Quick Start

```bash
git clone <repo-url> AutoShop && cd AutoShop
bash scripts/setup.sh
docker compose -f infra/docker/docker-compose.yml up
```

The setup script generates cryptographic secrets, runs database migrations, and seeds default settings. It will prompt you to set an admin password.

## URLs

| Service    | URL                                         |
|------------|---------------------------------------------|
| Dashboard  | http://localhost                            |
| Grafana    | http://localhost:3001 (admin / admin)       |
| MinIO      | http://localhost:9001 (minioadmin / minioadmin) |
| Prometheus | http://localhost:9090                       |

## Development (Hot Reload)

```bash
docker compose \
  -f infra/docker/docker-compose.yml \
  -f infra/docker/docker-compose.dev.yml \
  up
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system diagram and [docs/technical-design.md](docs/technical-design.md) for implementation decisions.

## Phase 1 Status

- [x] Shared Python package (`ase_shared`) — models, DB session, Redis, Celery config, security
- [x] Auth service (port 8001) — single-user login, Redis sessions, Fernet-encrypted Shopify tokens
- [x] Stub services — product-hunter, marketing, image-pipeline, shopify-publisher, analytics, notifications
- [x] Celery workers — one per domain queue
- [x] Scheduler (Celery Beat) — product hunt every 6h, analytics every 6h
- [x] Docker Compose — full stack + dev overrides with hot reload
- [x] Nginx reverse proxy
- [x] Prometheus + Grafana monitoring
- [ ] Phase 2: Full agent implementations (product scraping, AI scoring, image generation, Shopify publish)
