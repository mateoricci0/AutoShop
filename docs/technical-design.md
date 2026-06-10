# ASE — Technical Design Document

## 1. Key Architectural Decisions

### 1.1 Monorepo Structure
**Decision:** Single Git monorepo with service directories under `services/`.

**Rationale:**
- Atomic commits across services (no dependency hell between repos)
- Shared code in `shared/python/ase_shared/` consumed as a local Python package
- Single CI pipeline with service-level test isolation
- Easier for a small team; extract to polyrepo if services diverge significantly

**Trade-off:** Large repo clone size as codebase grows; mitigated with sparse checkout.

---

### 1.2 API Gateway Pattern
**Decision:** Traefik (layer-4/7 routing) + FastAPI Gateway service (business logic middleware).

**Traefik** handles:
- TLS termination
- Service discovery via Docker labels
- Load balancing
- Circuit breaking (future)

**FastAPI Gateway** handles:
- JWT validation (calls Auth service on first request, caches result in Redis 60s)
- Rate limiting (Redis sliding window)
- Request ID injection
- Structured access logging
- Store ownership enforcement header injection

**Why not just Traefik?** Business-logic middleware (JWT validation, multi-store routing) requires application code, not just routing rules.

---

### 1.3 Database Strategy — Shared-First
**Decision:** Single PostgreSQL instance, all services share the same DB, isolated by schema prefix conventions and `store_id` foreign keys.

**Phase 1 (current):** One DB, all tables in `public` schema. Services connect with their own PG role with restricted permissions.

**Phase 2+ (migration path):**
```
public.users         → auth schema
public.stores        → auth schema
public.products_*    → products schema
public.marketing_*   → marketing schema
public.analytics     → analytics schema
```

**Why shared-first?** Reduces operational overhead. True DB-per-service is premature until service boundaries are proven stable.

---

### 1.4 Celery Queues — Named per Service Domain
```python
CELERY_QUEUES = {
    "products.scrape",       # Product Hunter scraping tasks
    "products.analyze",      # DeepSeek scoring tasks
    "marketing.generate",    # Marketing copy generation
    "images.generate",       # Image generation (GPU-constrained, can scale separately)
    "publish.shopify",       # Shopify API calls (rate-limited)
    "analytics.collect",     # Metrics collection
    "notifications.send",    # Notification dispatch
    "scheduler.default",     # Scheduler internal tasks
}
```

Separate queues allow:
- Independent worker scaling (e.g., 10x image workers during peak)
- Priority tuning per domain
- Isolated failure (image generation failures don't block publishing)

---

### 1.5 AI Model Abstraction
```python
class LLMProvider(ABC):
    async def complete(self, messages, model, temperature) -> LLMResponse: ...
    async def stream(self, messages, model) -> AsyncIterator[str]: ...

class DeepSeekProvider(LLMProvider): ...   # Primary
class OpenAIProvider(LLMProvider): ...     # Premium fallback
class AnthropicProvider(LLMProvider): ...  # Premium fallback
```

**Selection logic:** Each task config specifies `model_tier: primary | premium`. Primary uses DeepSeek. Premium routes to GPT-4o or Claude based on `LLM_PREMIUM_PROVIDER` env var.

Token usage and cost are tracked per `agent_logs` row.

---

### 1.6 Shopify Client — Rate Limiting & Retry
Shopify REST Admin API: 2 req/s (Basic), 4 req/s (Advanced).

```python
class ShopifyClient:
    # Leaky bucket per store
    _rate_limiters: dict[str, AsyncLeakyBucket]
    
    async def request(self, store_id, method, endpoint, **kwargs):
        async with self._rate_limiters[store_id]:
            response = await self._session.request(...)
            if response.status == 429:
                await asyncio.sleep(response.headers["Retry-After"])
                return await self.request(...)  # retry
```

Retry policy: exponential backoff, max 5 retries, jitter.

---

### 1.7 Multi-Tenancy Model
All data rows carry `store_id` and `user_id`. The API Gateway injects `X-User-ID` and `X-Store-IDs` headers after JWT validation. Services trust these headers (only from the Gateway on the internal network).

A user can own multiple stores. Every API request that touches store-specific data must include a `store_id` parameter that is validated against the user's allowed stores.

---

## 2. Service-by-Service Design

### 2.1 Auth Service

**Endpoints:**
```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
GET    /auth/me
PUT    /auth/me
POST   /auth/verify-email
POST   /auth/forgot-password
POST   /auth/reset-password

GET    /api-keys
POST   /api-keys
DELETE /api-keys/{id}

GET    /stores
POST   /stores
PUT    /stores/{id}
DELETE /stores/{id}
GET    /stores/{id}/test-connection
```

**JWT payload:**
```json
{
  "sub": "user_uuid",
  "role": "operator",
  "store_ids": ["uuid1", "uuid2"],
  "iat": 1234567890,
  "exp": 1234568790,
  "jti": "unique_token_id"
}
```

**Token storage:**
- Access token: `Authorization: Bearer` header only (never cookie)
- Refresh token: HttpOnly Secure SameSite=Strict cookie
- Refresh token hash stored in Redis with key `rt:{user_id}:{jti}` TTL 30d

---

### 2.2 Product Hunter Service

**Scraper architecture:**
```
BaseScraper (ABC)
├── PlaywrightScraper       # Browser-based, JS-heavy sites
│   ├── TikTokCreativeScraper
│   ├── TikTokShopScraper
│   └── FacebookAdsScraper
├── HTTPScraper             # API-based, simple HTTP
│   ├── AliExpressScraper
│   ├── AmazonScraper
│   └── RedditScraper
└── IntegrationScraper      # Third-party APIs
    ├── ApifyScraper
    ├── GoogleTrendsScraper
    └── BrightDataScraper
```

**Scoring algorithm (DeepSeek):**
```python
SCORE_WEIGHTS = {
    "demand":     0.25,
    "trend":      0.20,
    "margin":     0.20,
    "engagement": 0.15,
    "competition":0.10,  # inverse
    "saturation": 0.05,  # inverse
    "branding":   0.05,
}
# success_score = weighted sum, 0-100
```

**Deduplication:** SHA-256 hash of normalized title + source + source_product_id. Stored in Redis bloom filter for O(1) lookups before DB insertion.

---

### 2.3 Marketing Service

**Content generation pipeline:**
```
Product Data
    │
    ▼
Context Builder (product + store brand + target audience)
    │
    ▼
Prompt Templates (Jinja2 templates per content type)
    │
    ▼
LLM Provider (DeepSeek primary)
    │
    ▼
Output Parser (structured JSON extraction)
    │
    ▼
Quality Validator (length checks, required fields, toxicity)
    │
    ▼
marketing_assets table
```

**Generated assets per product:**
- 1 brand name + tagline
- 1 short description (50 words)
- 1 long description (300 words)
- 5 bullet points
- 5 FAQs
- Meta title + description + 10 keywords
- 10 ad hooks, 5 headlines, 5 CTAs, 5 ad copies
- Platform-specific: Facebook (3 variants), Instagram (3), TikTok (3), Google (2)
- Email sequence: welcome + 3 follow-ups

---

### 2.4 Image Pipeline Service

**Image types and specs:**
| Type | Dimensions | Purpose |
|---|---|---|
| hero | 1200×1200 | Shopify main product image |
| lifestyle | 1200×800 | Contextual use scene |
| infographic | 1200×1500 | Feature callouts |
| before_after | 1200×600 | Split comparison |
| banner | 1200×400 | Collection/home banner |
| ad_square | 1080×1080 | Facebook/Instagram ads |
| ad_story | 1080×1920 | Stories format |

**Provider abstraction:**
```python
class ImageProvider(ABC):
    async def generate(self, prompt, negative_prompt, size, quality) -> ImageResult: ...

class OpenAIDalleProvider(ImageProvider): ...
class StabilityAIProvider(ImageProvider): ...
```

**Quality review:** Automated CLIP-score check (prompt-image alignment). Images below threshold (0.25) are regenerated once, then flagged for manual review.

**Storage:** MinIO bucket `ase-images/{store_id}/{product_id}/{type}/{uuid}.webp`. CDN URL returned for Shopify upload.

---

### 2.5 Shopify Publisher Service

**Publication checklist (all must pass before publish):**
```
[ ] product title present and < 255 chars
[ ] at least 1 description (short or long)
[ ] at least 1 image uploaded to S3
[ ] price > 0 and price > cost
[ ] store connection active
[ ] Shopify store rate limit not exceeded
```

**Operations:**
```python
class ShopifyProductService:
    async def create_product(store_id, product_data) -> ShopifyProduct
    async def update_product(store_id, shopify_id, updates) -> ShopifyProduct
    async def archive_product(store_id, shopify_id) -> bool
    async def sync_inventory(store_id, shopify_id, quantity) -> bool
    async def add_to_collection(store_id, product_id, collection_id) -> bool
    async def update_seo(store_id, shopify_id, seo_data) -> bool
    async def upload_image(store_id, shopify_id, image_url) -> ShopifyImage
```

**Retry strategy:** Tenacity library, exponential backoff 1s→2s→4s→8s→16s. On 5th failure: mark task as `failed`, create error notification.

---

### 2.6 Analytics Service

**Decision engine:**
```python
class DecisionEngine:
    THRESHOLDS = {
        "scale":    {"roas": 3.0, "min_spend": 50},
        "optimize": {"roas": (1.0, 3.0), "min_spend": 20},
        "pause":    {"roas": 1.0},
    }
    
    def evaluate(self, analytics_row: Analytics) -> Decision:
        if analytics_row.spend < self.THRESHOLDS["scale"]["min_spend"]:
            return Decision.INSUFFICIENT_DATA
        if analytics_row.roas >= self.THRESHOLDS["scale"]["roas"]:
            return Decision.SCALE
        if analytics_row.roas >= self.THRESHOLDS["optimize"]["roas"]:
            return Decision.OPTIMIZE
        return Decision.PAUSE
```

All decisions are persisted in `analytics.auto_decision`. The system never auto-applies decisions in v1 — it recommends and notifies. Manual confirmation required. Auto-application is a Phase 3 feature behind a feature flag.

---

### 2.7 Scheduler Service

Celery Beat with database-backed schedule (using `django-celery-beat` equivalent for FastAPI: `celery-sqlalchemy-scheduler`).

**Default schedules:**
| Task | Default frequency | Configurable |
|---|---|---|
| hunt_products | Every 6 hours | Yes |
| analyze_trending | Every 12 hours | Yes |
| collect_analytics | Every 6 hours | Yes |
| cleanup_old_tasks | Daily 02:00 UTC | No |
| health_report | Daily 08:00 UTC | Yes |

Per-store schedules stored in `scheduled_jobs` table. The beat scheduler reads from DB on startup and after any update.

---

### 2.8 Notification Service

**Channel implementations:**
```python
class EmailChannel(BaseChannel):
    # SMTP via SMTP2Go or SES
    
class DiscordChannel(BaseChannel):
    # Webhook URL per user setting
    
class TelegramChannel(BaseChannel):
    # Bot API, chat_id per user setting
    
class SlackChannel(BaseChannel):
    # Incoming webhook per user setting
```

**Event → channel mapping** stored in `settings` table per user. Default: email only.

**Retry:** Failed notifications retried 3x with 5-min delays. After 3 failures, log `critical` and store in `notifications.delivery_status`.

---

## 3. Frontend Architecture (Next.js 15)

### 3.1 App Router Structure
```
app/
├── (auth)/              # Public routes (no sidebar)
│   ├── login/page.tsx
│   └── register/page.tsx
├── (dashboard)/         # Protected routes (with sidebar)
│   ├── layout.tsx       # Dashboard shell + sidebar
│   ├── overview/page.tsx
│   ├── products/
│   │   ├── page.tsx         # Candidate list
│   │   ├── [id]/page.tsx    # Candidate detail
│   │   └── published/page.tsx
│   ├── marketing/
│   │   ├── page.tsx         # Assets list
│   │   └── [id]/page.tsx    # Asset detail + editor
│   ├── shopify/
│   │   ├── page.tsx         # Published products
│   │   └── stores/page.tsx  # Store management
│   ├── performance/page.tsx # Analytics + ROAS dashboard
│   ├── agents/page.tsx      # Agent monitor
│   ├── logs/page.tsx        # Activity logs
│   └── settings/page.tsx    # User + store settings
└── api/                 # BFF API routes
    └── [...]/route.ts
```

### 3.2 State Management
- **Server state:** React Query (TanStack Query v5) — all API data, 30s stale time
- **Client state:** Zustand — UI state, selected store, sidebar state
- **Forms:** React Hook Form + Zod validation

### 3.3 Real-time Updates
Server-Sent Events (SSE) from the API Gateway for:
- Agent status changes
- New product candidates
- Task completion events

SSE endpoint: `GET /api/events/stream` (auth-protected, per-user)

### 3.4 API Client Layer
```typescript
// services/api/client.ts — typed Axios instance
// services/api/products.ts — product endpoints
// services/api/marketing.ts — marketing endpoints
// services/api/analytics.ts — analytics endpoints
// services/api/agents.ts — agent control endpoints
```

All responses are typed via shared TypeScript types generated from OpenAPI schemas.

---

## 4. Shared Python Package (`ase_shared`)

Installed as an editable local package in each service's Docker image:
```dockerfile
COPY shared/python /app/shared
RUN pip install -e /app/shared
```

**Modules:**
```
ase_shared/
├── database/
│   ├── base.py          # DeclarativeBase, TimestampMixin
│   ├── session.py       # async_sessionmaker factory
│   └── migrations/      # Alembic env + versions
├── models/              # SQLAlchemy ORM (source of truth for schema)
├── schemas/             # Pydantic v2 schemas shared across services
├── security/
│   ├── encryption.py    # Fernet for secrets at rest
│   └── hashing.py       # bcrypt helpers
├── logging/
│   └── config.py        # structlog JSON renderer
├── cache/
│   └── redis.py         # Async Redis client factory
├── messaging/
│   └── celery_config.py # Celery app factory with all queue defs
└── exceptions.py        # Shared exception hierarchy
```

---

## 5. Environment Configuration

### 5.1 Variable Hierarchy
1. `.env.example` — committed, no secrets, documents all vars
2. `.env.local` — local dev overrides, git-ignored
3. `.env.production` — injected by CI/CD, never on disk
4. Docker secrets (production) — for `*_SECRET` vars

### 5.2 Required Variables per Service
```bash
# All services
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/ase
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
SERVICE_NAME=product-hunter
ENVIRONMENT=development

# Auth Service
JWT_PRIVATE_KEY=<RS256 PEM>
JWT_PUBLIC_KEY=<RS256 PEM>
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=2592000

# Product Hunter
APIFY_API_KEY=
BRIGHTDATA_USERNAME=
BRIGHTDATA_PASSWORD=
DEEPSEEK_API_KEY=

# Marketing
DEEPSEEK_API_KEY=
OPENAI_API_KEY=          # optional premium
ANTHROPIC_API_KEY=       # optional premium
LLM_PREMIUM_PROVIDER=openai

# Image Pipeline
OPENAI_API_KEY=
STABILITY_API_KEY=
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=ase-images

# Shopify Publisher
SHOPIFY_API_VERSION=2024-10
SHOPIFY_SECRET_KEY=      # for webhook verification

# Notifications
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
DISCORD_DEFAULT_WEBHOOK=
TELEGRAM_BOT_TOKEN=
SLACK_DEFAULT_WEBHOOK=
```

---

## 6. Testing Strategy

### 6.1 Test Pyramid
```
                   ┌───────────┐
                   │  E2E (5%) │  Playwright — critical user journeys
                   ├───────────┤
                   │ Integ(25%)│  pytest + testcontainers (real PG/Redis)
                   ├───────────┤
                   │Unit  (70%)│  pytest + httpx AsyncClient + mocks
                   └───────────┘
```

### 6.2 Per-Service Test Structure
```
tests/
├── unit/
│   ├── test_scraper.py
│   ├── test_scorer.py
│   └── test_deduplicator.py
├── integration/
│   ├── test_api_products.py   # Against real DB (testcontainers)
│   └── test_tasks.py          # Against real Redis
└── conftest.py                # Fixtures, test DB setup
```

### 6.3 Coverage Targets
- Unit tests: 90% line coverage
- Integration tests: all API endpoints
- E2E tests: login, product approval, publish flow

---

## 7. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml (per-service matrix)
jobs:
  test:
    strategy:
      matrix:
        service: [auth, product-hunter, marketing, image-pipeline, shopify-publisher, analytics, notifications, dashboard]
    steps:
      - lint (ruff + mypy / eslint + tsc)
      - unit tests
      - integration tests (testcontainers)
      - coverage check (>= 80%)
      - build Docker image
      - security scan (Trivy)

  deploy-staging:
    needs: test
    if: branch == 'main'

  deploy-prod:
    needs: deploy-staging
    if: tagged release (v*.*.*)
```

---

## 8. Performance Considerations

| Concern | Approach |
|---|---|
| Slow scraping | Playwright pool (max 5 concurrent browsers), headless, user-agent rotation |
| AI API latency | Async HTTP (httpx), connection pooling, timeout 30s |
| DB query performance | Indexes on `store_id`, `status`, `created_at` (see schema); read replicas in Phase 3 |
| Image generation | Separate Celery queue, can scale workers horizontally |
| Shopify rate limits | Per-store leaky bucket, queue depth monitoring |
| Dashboard load time | React Query caching + SSR for initial page load |
| Analytics queries | Materialized views for ROAS aggregates (daily rollup job) |

---

## 9. Scalability Path

| Phase | Scale event | Action |
|---|---|---|
| Phase 1 | Single instance | Docker Compose, 1 worker per queue |
| Phase 2 | 10+ stores | Scale image/scraping workers independently |
| Phase 3 | 100+ stores | Redis Cluster, PG read replicas, worker autoscaling |
| Phase 4 | 1000+ stores | Kubernetes (manifests already in `infra/k8s/`), schema-per-service |
