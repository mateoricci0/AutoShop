# ASE — Folder Structure (Personal Use)

```
AutoShop/
│
├── .github/
│   └── workflows/
│       └── ci.yml                          # Lint + test en cada push (sin deploy)
│
├── services/
│   │
│   ├── auth/                               # Auth Service — :8001
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                     # FastAPI app
│   │   │   ├── config.py                   # Pydantic Settings (env vars)
│   │   │   ├── routes/
│   │   │   │   ├── auth.py                 # POST /login, /logout, GET /verify
│   │   │   │   └── stores.py               # CRUD tiendas Shopify
│   │   │   ├── schemas/
│   │   │   │   ├── auth.py
│   │   │   │   └── store.py
│   │   │   └── services/
│   │   │       ├── session.py              # Redis session management
│   │   │       └── store_service.py        # Fernet encrypt/decrypt + Shopify test
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   └── test_session.py
│   │   │   └── integration/
│   │   │       ├── test_auth.py
│   │   │       └── test_stores.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── product-hunter/                     # Product Hunter — :8002 + workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── candidates.py           # GET/PATCH candidatos, aprobar/rechazar
│   │   │   │   └── jobs.py                 # POST /jobs/hunt, GET /jobs/{id}
│   │   │   ├── schemas/
│   │   │   │   └── candidate.py
│   │   │   ├── services/
│   │   │   │   ├── scrapers/
│   │   │   │   │   ├── base.py             # BaseScraper ABC + ScrapedProduct
│   │   │   │   │   ├── playwright_base.py  # Pool de browsers Playwright
│   │   │   │   │   ├── tiktok_creative.py
│   │   │   │   │   ├── tiktok_shop.py
│   │   │   │   │   ├── aliexpress.py
│   │   │   │   │   ├── temu.py
│   │   │   │   │   ├── amazon.py
│   │   │   │   │   ├── facebook_ads.py
│   │   │   │   │   ├── google_trends.py
│   │   │   │   │   └── reddit.py
│   │   │   │   ├── normalizer.py
│   │   │   │   ├── deduplicator.py         # SHA-256 hash + Redis
│   │   │   │   └── scorer.py               # DeepSeek 7-dimension scoring
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
│   │   │       └── scraped_products.json
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   └── requirements.txt
│   │
│   ├── marketing/                          # Marketing Service — :8003 + workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── assets.py               # CRUD marketing assets
│   │   │   │   └── generate.py             # POST /generate, GET /jobs/{id}
│   │   │   ├── schemas/
│   │   │   │   └── asset.py
│   │   │   ├── services/
│   │   │   │   ├── context_builder.py      # Producto → contexto LLM
│   │   │   │   ├── prompt_templates/
│   │   │   │   │   ├── branding.j2
│   │   │   │   │   ├── description.j2
│   │   │   │   │   ├── seo.j2
│   │   │   │   │   ├── ad_copy.j2
│   │   │   │   │   └── ads_platform.j2
│   │   │   │   ├── llm/
│   │   │   │   │   ├── base.py             # LLMProvider ABC
│   │   │   │   │   ├── deepseek.py
│   │   │   │   │   ├── openai.py
│   │   │   │   │   └── anthropic.py
│   │   │   │   ├── output_parsers.py       # JSON estructurado desde LLM
│   │   │   │   └── quality_validator.py
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── marketing_tasks.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_context_builder.py
│   │   │   │   ├── test_output_parsers.py
│   │   │   │   └── test_quality_validator.py
│   │   │   └── integration/
│   │   │       └── test_asset_routes.py
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   └── requirements.txt
│   │
│   ├── image-pipeline/                     # Image Pipeline — :8004 + workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── images.py               # GET/DELETE imágenes, aprobar
│   │   │   │   └── generate.py             # POST /generate, GET /jobs/{id}
│   │   │   ├── schemas/
│   │   │   │   └── image.py
│   │   │   ├── services/
│   │   │   │   ├── prompt_generator.py     # Producto → prompt por tipo
│   │   │   │   ├── providers/
│   │   │   │   │   ├── base.py             # ImageProvider ABC
│   │   │   │   │   ├── openai_dalle.py
│   │   │   │   │   └── stability_ai.py
│   │   │   │   ├── quality_reviewer.py     # CLIP score check
│   │   │   │   └── storage.py              # MinIO S3 client
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── image_tasks.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_prompt_generator.py
│   │   │   │   └── test_quality_reviewer.py
│   │   │   └── integration/
│   │   │       └── test_image_routes.py
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   └── requirements.txt
│   │
│   ├── shopify-publisher/                  # Shopify Publisher — :8005 + workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── products.py             # GET productos publicados, sync
│   │   │   │   ├── publish.py              # POST /publish, GET /jobs/{id}
│   │   │   │   └── webhooks.py             # POST /webhooks/shopify
│   │   │   ├── schemas/
│   │   │   │   └── product.py
│   │   │   ├── services/
│   │   │   │   ├── shopify_client.py       # Async client + leaky bucket
│   │   │   │   ├── product_publisher.py    # Orchestrate publish checklist
│   │   │   │   ├── image_uploader.py       # MinIO URL → Shopify CDN
│   │   │   │   └── seo_manager.py
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── publish_tasks.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_publish_checklist.py
│   │   │   │   └── test_shopify_client.py
│   │   │   └── integration/
│   │   │       └── test_publish_routes.py
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   └── requirements.txt
│   │
│   ├── analytics/                          # Analytics — :8006 + workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── analytics.py            # Summary, timeseries, per-product
│   │   │   │   ├── campaigns.py
│   │   │   │   └── decisions.py            # Ver y confirmar decisiones ROAS
│   │   │   ├── schemas/
│   │   │   │   ├── analytics.py
│   │   │   │   └── decision.py
│   │   │   ├── services/
│   │   │   │   ├── decision_engine.py      # ROAS rules
│   │   │   │   ├── kpi_calculator.py       # CTR, CPC, ROAS, etc.
│   │   │   │   └── integrations/
│   │   │   │       └── shopify_analytics.py
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── analytics_tasks.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   ├── test_decision_engine.py
│   │   │   │   └── test_kpi_calculator.py
│   │   │   └── integration/
│   │   │       └── test_analytics_routes.py
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   └── requirements.txt
│   │
│   ├── notifications/                      # Notifications — :8007 + workers
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routes/
│   │   │   │   ├── notifications.py        # List, mark read, stream SSE
│   │   │   │   └── settings.py             # Config canales
│   │   │   ├── schemas/
│   │   │   │   └── notification.py
│   │   │   ├── services/
│   │   │   │   ├── dispatcher.py           # Route a canales correctos
│   │   │   │   └── channels/
│   │   │   │       ├── base.py
│   │   │   │       ├── email.py
│   │   │   │       ├── discord.py
│   │   │   │       ├── telegram.py
│   │   │   │       └── slack.py
│   │   │   └── tasks/
│   │   │       ├── celery_app.py
│   │   │       └── notification_tasks.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── Dockerfile.worker
│   │   └── requirements.txt
│   │
│   ├── scheduler/                          # Celery Beat (sin HTTP)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py               # Beat app con DB scheduler
│   │   │   └── default_schedules.py        # Jobs por defecto al arrancar
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── dashboard/                          # Next.js 15 — :3000
│       ├── src/
│       │   ├── app/
│       │   │   ├── login/
│       │   │   │   └── page.tsx            # Pantalla de login
│       │   │   ├── (dashboard)/
│       │   │   │   ├── layout.tsx          # Sidebar + header
│       │   │   │   ├── overview/
│       │   │   │   │   └── page.tsx        # KPIs + estado agentes
│       │   │   │   ├── products/
│       │   │   │   │   ├── page.tsx        # Tabla candidatos
│       │   │   │   │   └── [id]/
│       │   │   │   │       └── page.tsx    # Detalle + aprobar/rechazar
│       │   │   │   ├── published/
│       │   │   │   │   └── page.tsx        # Productos en Shopify
│       │   │   │   ├── marketing/
│       │   │   │   │   ├── page.tsx        # Lista assets
│       │   │   │   │   └── [id]/
│       │   │   │   │       └── page.tsx    # Editor de copy + imágenes
│       │   │   │   ├── performance/
│       │   │   │   │   └── page.tsx        # ROAS + métricas + campañas
│       │   │   │   ├── agents/
│       │   │   │   │   └── page.tsx        # Monitor agentes + logs
│       │   │   │   └── settings/
│       │   │   │       └── page.tsx        # Tiendas + notificaciones + scheduler
│       │   │   ├── api/
│       │   │   │   └── [...proxy]/
│       │   │   │       └── route.ts        # BFF proxy a servicios backend
│       │   │   ├── layout.tsx
│       │   │   ├── not-found.tsx
│       │   │   └── globals.css
│       │   ├── components/
│       │   │   ├── ui/                     # shadcn/ui components
│       │   │   ├── charts/
│       │   │   │   ├── RoasChart.tsx       # Recharts line chart
│       │   │   │   ├── RevenueChart.tsx
│       │   │   │   └── ScoreRadar.tsx      # Radar chart de scores
│       │   │   ├── tables/
│       │   │   │   ├── CandidatesTable.tsx
│       │   │   │   └── PublishedTable.tsx
│       │   │   ├── agents/
│       │   │   │   ├── AgentCard.tsx
│       │   │   │   └── AgentStatusBadge.tsx
│       │   │   ├── layout/
│       │   │   │   ├── Sidebar.tsx
│       │   │   │   ├── Header.tsx
│       │   │   │   └── StoreSwitcher.tsx
│       │   │   └── notifications/
│       │   │       └── NotificationBell.tsx
│       │   ├── hooks/
│       │   │   ├── useSSE.ts               # SSE para progreso en tiempo real
│       │   │   └── useActiveStore.ts       # Tienda activa seleccionada
│       │   ├── stores/                     # Zustand
│       │   │   ├── ui.store.ts             # Sidebar, modales
│       │   │   └── store-selector.store.ts # Tienda activa
│       │   ├── services/
│       │   │   └── api/
│       │   │       ├── client.ts           # Axios + interceptores
│       │   │       ├── products.ts
│       │   │       ├── marketing.ts
│       │   │       ├── analytics.ts
│       │   │       └── agents.ts
│       │   ├── types/
│       │   │   ├── product.ts
│       │   │   ├── analytics.ts
│       │   │   └── agent.ts
│       │   └── lib/
│       │       ├── utils.ts                # cn() + helpers
│       │       └── format.ts               # Formateadores de moneda/fecha
│       ├── public/
│       ├── Dockerfile
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       ├── components.json                 # shadcn/ui config
│       ├── package.json
│       └── tsconfig.json
│
├── shared/
│   └── python/
│       ├── ase_shared/
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│       │   │   ├── session.py              # async_sessionmaker factory
│       │   │   └── migrations/
│       │   │       ├── env.py              # Alembic env
│       │   │       ├── script.py.mako
│       │   │       └── versions/           # Archivos de migración
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── store.py
│       │   │   ├── product.py              # ProductCandidate, ProductPublished
│       │   │   ├── marketing.py            # MarketingAsset, GeneratedImage
│       │   │   ├── analytics.py            # Analytics, Campaign
│       │   │   ├── task.py                 # Task, ScheduledJob
│       │   │   ├── notification.py
│       │   │   ├── settings.py
│       │   │   └── auth.py                 # AdminSession
│       │   ├── security/
│       │   │   ├── encryption.py           # Fernet para tokens Shopify
│       │   │   └── hashing.py              # bcrypt helpers
│       │   ├── logging/
│       │   │   └── config.py               # structlog JSON
│       │   ├── cache/
│       │   │   └── redis.py                # aioredis factory
│       │   ├── messaging/
│       │   │   └── celery_config.py        # Celery app factory + queues
│       │   └── exceptions.py
│       ├── pyproject.toml
│       └── setup.py
│
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml              # Stack completo local
│   │   └── docker-compose.dev.yml          # Hot-reload overrides
│   ├── nginx/
│   │   └── nginx.conf                      # Reverse proxy config
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       │   ├── ase-overview.json
│       │   └── celery-workers.json
│       └── provisioning/
│           ├── datasources.yml
│           └── dashboards.yml
│
├── docs/
│   ├── database-schema.sql
│   ├── folder-structure.md
│   ├── technical-design.md
│   ├── api-contracts.md
│   └── roadmap.md
│
├── scripts/
│   ├── setup.sh                            # Setup completo en un comando
│   ├── generate-keys.sh                    # Genera FERNET_KEY, SECRET_KEY, hash password
│   ├── migrate.sh                          # Ejecuta Alembic migrations
│   └── seed.sh                             # Inserta store de prueba + settings default
│
├── ARCHITECTURE.md
├── README.md
├── .env.example
└── .gitignore
```

---

## Notas

### Python Services (convenciones)
- `main.py` — FastAPI app, lifespan, routers, middleware
- `config.py` — `Pydantic BaseSettings`, lee de env
- `routes/` — Solo HTTP; sin lógica de negocio
- `services/` — Lógica de negocio; sin imports de FastAPI
- `tasks/` — Celery tasks; wrappers delgados de services
- `schemas/` — Pydantic v2 request/response (local al servicio)

### Docker
- `Dockerfile` — imagen del servidor HTTP (FastAPI)
- `Dockerfile.worker` — imagen del worker Celery (misma base, distinto CMD)
- Base: `python:3.12-slim`, multi-stage, usuario no-root
