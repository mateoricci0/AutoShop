# ASE — Complete Folder Structure

```
AutoShop/                                   # Monorepo root
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                          # Per-service test + build matrix
│   │   ├── deploy-staging.yml              # Auto-deploy on main merge
│   │   └── deploy-prod.yml                 # Manual trigger on tagged release
│   └── PULL_REQUEST_TEMPLATE.md
│
├── services/
│   │
│   ├── gateway/                            # API Gateway — FastAPI :8000
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                     # FastAPI app + lifespan
│   │   │   ├── config.py                   # Pydantic Settings
│   │   │   ├── dependencies.py             # Shared FastAPI deps
│   │   │   ├── middleware/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py                 # JWT validation middleware
│   │   │   │   ├── rate_limit.py           # Redis sliding window
│   │   │   │   ├── request_id.py           # Inject X-Request-ID
│   │   │   │   └── access_log.py           # Structured access logging
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── proxy.py                # HTTPX reverse proxy routes
│   │   │   │   └── sse.py                  # Server-Sent Events stream
│   │   │   └── health.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── auth/                               # Auth Service — FastAPI :8001
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py                 # login, register, refresh, logout
│   │   │   │   ├── users.py                # me, update profile
│   │   │   │   ├── api_keys.py             # CRUD API keys
│   │   │   │   └── stores.py               # Store CRUD + Shopify connection
│   │   │   ├── schemas/
│   │   │   │   ├── auth.py
│   │   │   │   ├── user.py
│   │   │   │   └── store.py
│   │   │   └── services/
│   │   │       ├── auth_service.py
│   │   │       ├── jwt_service.py          # RS256 sign/verify
│   │   │       ├── password_service.py     # bcrypt
│   │   │       └── store_service.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_jwt.py
│   │   │   │   └── test_password.py
│   │   │   └── integration/
│   │   │       ├── test_auth_routes.py
│   │   │       └── test_store_routes.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── product-hunter/                     # Product Hunter — FastAPI :8002 + Celery workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   ├── candidates.py           # GET/PATCH candidates, approve/reject
│   │   │   │   ├── sources.py              # Scraper source config
│   │   │   │   └── jobs.py                 # Trigger scraping jobs
│   │   │   ├── schemas/
│   │   │   │   ├── candidate.py
│   │   │   │   └── scrape_job.py
│   │   │   ├── services/
│   │   │   │   ├── scrapers/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py             # BaseScraper ABC + ScrapedProduct model
│   │   │   │   │   ├── playwright_base.py  # Browser pool management
│   │   │   │   │   ├── tiktok_creative.py
│   │   │   │   │   ├── tiktok_shop.py
│   │   │   │   │   ├── aliexpress.py
│   │   │   │   │   ├── temu.py
│   │   │   │   │   ├── amazon.py
│   │   │   │   │   ├── facebook_ads.py
│   │   │   │   │   ├── google_trends.py
│   │   │   │   │   └── reddit.py
│   │   │   │   ├── normalizer.py           # Normalize scraped → standard schema
│   │   │   │   ├── deduplicator.py         # Bloom filter + DB check
│   │   │   │   └── scorer.py              # DeepSeek scoring + weight calculation
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       ├── scrape_tasks.py         # hunt_products, scrape_source
│   │   │       └── analyze_tasks.py        # score_candidate, batch_score
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_normalizer.py
│   │   │   │   ├── test_deduplicator.py
│   │   │   │   └── test_scorer.py
│   │   │   ├── integration/
│   │   │   │   └── test_candidate_routes.py
│   │   │   └── fixtures/
│   │   │       └── scraped_products.json   # Test fixtures
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── marketing/                          # Marketing Service — FastAPI :8003 + Celery workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   ├── assets.py               # CRUD marketing assets
│   │   │   │   ├── generate.py             # Trigger generation jobs
│   │   │   │   └── templates.py            # Prompt template management
│   │   │   ├── schemas/
│   │   │   │   ├── asset.py
│   │   │   │   └── generation.py
│   │   │   ├── services/
│   │   │   │   ├── context_builder.py      # Build LLM context from product data
│   │   │   │   ├── prompt_templates/
│   │   │   │   │   ├── branding.j2
│   │   │   │   │   ├── description.j2
│   │   │   │   │   ├── ad_copy.j2
│   │   │   │   │   ├── seo.j2
│   │   │   │   │   └── email.j2
│   │   │   │   ├── llm/
│   │   │   │   │   ├── base.py             # LLMProvider ABC
│   │   │   │   │   ├── deepseek.py
│   │   │   │   │   ├── openai.py
│   │   │   │   │   └── anthropic.py
│   │   │   │   ├── output_parsers.py       # Structured JSON extraction
│   │   │   │   └── quality_validator.py    # Output validation
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── marketing_tasks.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── image-pipeline/                     # Image Pipeline — FastAPI :8004 + Celery workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   ├── images.py               # CRUD images
│   │   │   │   └── generate.py             # Trigger image generation
│   │   │   ├── schemas/
│   │   │   │   ├── image.py
│   │   │   │   └── generation.py
│   │   │   ├── services/
│   │   │   │   ├── prompt_generator.py     # Product → image prompt
│   │   │   │   ├── providers/
│   │   │   │   │   ├── base.py             # ImageProvider ABC
│   │   │   │   │   ├── openai_dalle.py
│   │   │   │   │   └── stability_ai.py
│   │   │   │   ├── quality_reviewer.py     # CLIP score + auto-review
│   │   │   │   ├── storage.py              # MinIO/S3 client
│   │   │   │   └── cdn.py                  # CDN URL generation
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── image_tasks.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── shopify-publisher/                  # Shopify Publisher — FastAPI :8005 + Celery workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   ├── products.py             # Published products CRUD + sync
│   │   │   │   ├── publish.py              # Trigger publish jobs
│   │   │   │   └── webhooks.py             # Shopify webhook receiver
│   │   │   ├── schemas/
│   │   │   │   ├── product.py
│   │   │   │   └── publish.py
│   │   │   ├── services/
│   │   │   │   ├── shopify_client.py       # Async Shopify Admin API client + rate limiter
│   │   │   │   ├── product_publisher.py    # Orchestrate publish checklist
│   │   │   │   ├── inventory_manager.py
│   │   │   │   ├── collection_manager.py
│   │   │   │   └── seo_manager.py
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── publish_tasks.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── analytics/                          # Analytics Service — FastAPI :8006 + Celery workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   ├── analytics.py            # Query analytics data + KPIs
│   │   │   │   ├── campaigns.py            # Campaign CRUD
│   │   │   │   └── decisions.py            # View/apply ROAS decisions
│   │   │   ├── schemas/
│   │   │   │   ├── analytics.py
│   │   │   │   └── decision.py
│   │   │   ├── services/
│   │   │   │   ├── decision_engine.py      # ROAS rules engine
│   │   │   │   ├── kpi_calculator.py       # Compute CTR/CPC/CPA/ROAS etc.
│   │   │   │   └── integrations/
│   │   │   │       ├── shopify_analytics.py
│   │   │   │       ├── meta_ads.py         # Future: Meta Marketing API
│   │   │   │       └── google_ads.py       # Future: Google Ads API
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── analytics_tasks.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── notifications/                      # Notification Service — FastAPI :8007 + Celery workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routes/
│   │   │   │   └── notifications.py        # List/mark-read notifications
│   │   │   ├── schemas/
│   │   │   │   └── notification.py
│   │   │   ├── services/
│   │   │   │   ├── dispatcher.py           # Route to correct channels
│   │   │   │   └── channels/
│   │   │   │       ├── base.py             # BaseChannel ABC
│   │   │   │       ├── email.py            # SMTP / SES
│   │   │   │       ├── discord.py          # Webhook
│   │   │   │       ├── telegram.py         # Bot API
│   │   │   │       └── slack.py            # Incoming webhook
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── notification_tasks.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── scheduler/                          # Celery Beat — no HTTP port
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── celery_app.py               # Beat app with DB scheduler
│   │   │   └── default_schedules.py        # Built-in periodic tasks
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   └── dashboard/                          # Next.js 15 Frontend — :3000
│       ├── src/
│       │   ├── app/
│       │   │   ├── (auth)/
│       │   │   │   ├── login/
│       │   │   │   │   └── page.tsx
│       │   │   │   └── register/
│       │   │   │       └── page.tsx
│       │   │   ├── (dashboard)/
│       │   │   │   ├── layout.tsx          # Sidebar + header shell
│       │   │   │   ├── overview/
│       │   │   │   │   └── page.tsx        # KPI widgets + agent status
│       │   │   │   ├── products/
│       │   │   │   │   ├── page.tsx        # Candidate table + filter
│       │   │   │   │   ├── [id]/
│       │   │   │   │   │   └── page.tsx    # Candidate detail + approve/reject
│       │   │   │   │   └── published/
│       │   │   │   │       └── page.tsx    # Published products table
│       │   │   │   ├── marketing/
│       │   │   │   │   ├── page.tsx        # Assets list
│       │   │   │   │   └── [id]/
│       │   │   │   │       └── page.tsx    # Asset detail + copy editing
│       │   │   │   ├── shopify/
│       │   │   │   │   ├── page.tsx        # Published product sync status
│       │   │   │   │   └── stores/
│       │   │   │   │       └── page.tsx    # Store management
│       │   │   │   ├── performance/
│       │   │   │   │   └── page.tsx        # ROAS charts + campaign table
│       │   │   │   ├── agents/
│       │   │   │   │   └── page.tsx        # Agent monitor + manual trigger
│       │   │   │   ├── logs/
│       │   │   │   │   └── page.tsx        # Agent logs viewer
│       │   │   │   └── settings/
│       │   │   │       └── page.tsx        # User + notification + agent settings
│       │   │   ├── api/
│       │   │   │   └── [...]/
│       │   │   │       └── route.ts        # BFF proxy routes
│       │   │   ├── layout.tsx
│       │   │   ├── not-found.tsx
│       │   │   ├── error.tsx
│       │   │   └── globals.css
│       │   ├── components/
│       │   │   ├── ui/                     # shadcn/ui re-exports
│       │   │   ├── charts/
│       │   │   │   ├── RoasChart.tsx
│       │   │   │   ├── RevenueChart.tsx
│       │   │   │   └── FunnelChart.tsx
│       │   │   ├── tables/
│       │   │   │   ├── ProductsTable.tsx
│       │   │   │   ├── CandidatesTable.tsx
│       │   │   │   └── AnalyticsTable.tsx
│       │   │   ├── forms/
│       │   │   │   ├── StoreForm.tsx
│       │   │   │   └── SettingsForm.tsx
│       │   │   ├── layout/
│       │   │   │   ├── Sidebar.tsx
│       │   │   │   ├── Header.tsx
│       │   │   │   └── StoreSwitcher.tsx
│       │   │   ├── agents/
│       │   │   │   ├── AgentCard.tsx
│       │   │   │   └── AgentStatusBadge.tsx
│       │   │   └── notifications/
│       │   │       └── NotificationBell.tsx
│       │   ├── hooks/
│       │   │   ├── useSSE.ts               # Server-Sent Events hook
│       │   │   ├── useStore.ts             # Current store selector
│       │   │   └── useAuth.ts
│       │   ├── stores/                     # Zustand state
│       │   │   ├── auth.store.ts
│       │   │   ├── ui.store.ts             # sidebar, modals
│       │   │   └── store-selector.store.ts # active store
│       │   ├── services/
│       │   │   ├── api/
│       │   │   │   ├── client.ts           # Axios instance + interceptors
│       │   │   │   ├── auth.ts
│       │   │   │   ├── products.ts
│       │   │   │   ├── marketing.ts
│       │   │   │   ├── analytics.ts
│       │   │   │   ├── agents.ts
│       │   │   │   └── notifications.ts
│       │   │   └── query-keys.ts           # React Query key factory
│       │   ├── types/
│       │   │   ├── api.ts                  # API response types
│       │   │   ├── product.ts
│       │   │   ├── analytics.ts
│       │   │   └── agent.ts
│       │   └── lib/
│       │       ├── utils.ts                # cn() + misc utils
│       │       └── format.ts               # currency, date, number formatters
│       ├── public/
│       │   └── icons/
│       ├── tests/
│       │   ├── e2e/                        # Playwright E2E
│       │   │   ├── auth.spec.ts
│       │   │   ├── products.spec.ts
│       │   │   └── publish.spec.ts
│       │   └── unit/                       # Vitest unit tests
│       ├── Dockerfile
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       ├── components.json                 # shadcn/ui config
│       ├── package.json
│       ├── tsconfig.json
│       └── vitest.config.ts
│
├── shared/
│   ├── python/
│   │   ├── ase_shared/
│   │   │   ├── __init__.py
│   │   │   ├── database/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│   │   │   │   ├── session.py              # async_sessionmaker factory
│   │   │   │   └── migrations/
│   │   │   │       ├── env.py              # Alembic env
│   │   │   │       ├── script.py.mako
│   │   │   │       └── versions/           # Migration files
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py                 # User, RefreshToken, ApiKey
│   │   │   │   ├── store.py
│   │   │   │   ├── product.py              # ProductCandidate, ProductPublished
│   │   │   │   ├── marketing.py            # MarketingAsset, GeneratedImage
│   │   │   │   ├── analytics.py            # Analytics, Campaign
│   │   │   │   ├── task.py                 # Task, ScheduledJob
│   │   │   │   ├── notification.py
│   │   │   │   ├── settings.py
│   │   │   │   └── audit_log.py
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── common.py               # Pagination, ErrorResponse
│   │   │   │   └── events.py               # SSE event types
│   │   │   ├── security/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── encryption.py           # Fernet encrypt/decrypt for secrets
│   │   │   │   └── hashing.py              # bcrypt helpers
│   │   │   ├── logging/
│   │   │   │   ├── __init__.py
│   │   │   │   └── config.py               # structlog JSON renderer + context vars
│   │   │   ├── cache/
│   │   │   │   ├── __init__.py
│   │   │   │   └── redis.py                # Async Redis client factory
│   │   │   ├── messaging/
│   │   │   │   ├── __init__.py
│   │   │   │   └── celery_config.py        # Celery app factory + queue definitions
│   │   │   ├── observability/
│   │   │   │   ├── __init__.py
│   │   │   │   └── metrics.py              # prometheus_client registry
│   │   │   └── exceptions.py               # ASEError hierarchy
│   │   ├── pyproject.toml
│   │   └── setup.py
│   └── typescript/
│       ├── src/
│       │   └── types/
│       │       ├── api.ts                  # Shared API response types
│       │       ├── product.ts
│       │       └── analytics.ts
│       ├── package.json
│       └── tsconfig.json
│
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml              # Full local stack (all services)
│   │   ├── docker-compose.dev.yml          # Dev: hot-reload overrides
│   │   ├── docker-compose.test.yml         # CI: test containers
│   │   └── docker-compose.prod.yml         # Prod: no volume mounts, resource limits
│   ├── traefik/
│   │   ├── traefik.yml                     # Static config
│   │   └── dynamic/
│   │       └── routes.yml                  # Dynamic routing rules
│   ├── prometheus/
│   │   └── prometheus.yml                  # Scrape config for all services
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── ase-overview.json
│   │   │   ├── product-hunter.json
│   │   │   └── celery-workers.json
│   │   └── provisioning/
│   │       ├── datasources.yml
│   │       └── dashboards.yml
│   ├── minio/
│   │   └── init.sh                         # Create buckets on startup
│   └── k8s/                                # Kubernetes (Phase 4+)
│       ├── namespaces/
│       ├── deployments/
│       ├── services/
│       ├── ingress/
│       ├── configmaps/
│       └── secrets/                        # Sealed secrets templates
│
├── docs/
│   ├── architecture.md                     # → ARCHITECTURE.md (root)
│   ├── technical-design.md                 # This domain
│   ├── database-schema.sql
│   ├── folder-structure.md
│   ├── api-contracts.md
│   └── roadmap.md
│
├── scripts/
│   ├── setup.sh                            # Clone + setup local env
│   ├── generate-keys.sh                    # Generate JWT RSA keys + Fernet key
│   ├── migrate.sh                          # Run Alembic migrations
│   ├── seed.sh                             # Insert dev seed data
│   └── healthcheck.sh                      # Verify all services healthy
│
├── ARCHITECTURE.md                         # Top-level architecture (this doc)
├── README.md
├── .env.example
├── .gitignore
└── .editorconfig
```

---

## Key Conventions

### Python Services
- `main.py` — FastAPI app instantiation, middleware registration, router inclusion, lifespan
- `config.py` — Pydantic `BaseSettings`, reads from environment
- `dependencies.py` — FastAPI dependency injection (DB session, current user, store check)
- `routes/` — Thin HTTP layer only; all business logic in `services/`
- `services/` — Business logic; no FastAPI imports
- `tasks/` — Celery tasks; thin wrappers that call `services/`
- `schemas/` — Pydantic v2 request/response models (service-local, not shared)
- `tests/unit/` — Fast, no I/O, mocked dependencies
- `tests/integration/` — Real DB + Redis via testcontainers

### Frontend
- All pages use React Server Components by default
- Client Components only for interactivity (charts, forms, real-time)
- React Query for all server state; no client-side caching of server data in Zustand
- Zustand only for UI state (sidebar open/closed, active store selection, modal state)

### Docker
- Each service has its own `Dockerfile` (API server) and optionally `Dockerfile.worker` (Celery worker)
- Base image: `python:3.12-slim` for all Python services
- Multi-stage builds: `builder` stage installs deps, `runtime` stage copies artifacts
- Non-root user in all containers
