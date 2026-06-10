# Autonomous Shopify Engine (ASE) — Architecture

> **Phase 0 — Architecture & Technical Design**
> This document defines the complete system architecture. No implementation begins until this is validated.

---

## 1. System Overview

ASE is a multi-agent SaaS platform that autonomously discovers profitable products, generates marketing content, publishes to Shopify, and monitors performance — all from a single dashboard supporting multiple stores.

**Core design principles:**
- Each service owns its domain and can be deployed independently
- All inter-service async communication goes through Celery/Redis (not direct HTTP calls between services)
- All sync external-facing communication routes through the API Gateway
- Shared database schema in Phase 1, migrating to per-service schemas in Phase 3+
- Secrets never stored in code; always injected via environment or secret manager

---

## 2. System Topology

```mermaid
graph TB
    subgraph EXTERNAL["External Systems"]
        TT[TikTok Creative Center]
        AE[AliExpress]
        AM[Amazon]
        FB[Facebook Ad Library]
        GT[Google Trends]
        RD[Reddit]
        SH[Shopify Admin API]
        DS[DeepSeek API]
        IM[Image Model APIs]
        NT[Notification Channels<br/>Email · Discord · Telegram · Slack]
    end

    subgraph CLIENT["Client Layer"]
        WEB[Next.js 15 Dashboard<br/>:3000]
    end

    subgraph GATEWAY["API Gateway Layer"]
        GW[API Gateway<br/>FastAPI :8000]
        TR[Traefik<br/>Reverse Proxy :80/443]
    end

    subgraph SERVICES["Backend Services"]
        AUTH[Auth Service<br/>:8001]
        HUNTER[Product Hunter<br/>:8002]
        MARKET[Marketing Service<br/>:8003]
        IMGPIPE[Image Pipeline<br/>:8004]
        PUBLISH[Shopify Publisher<br/>:8005]
        ANALYT[Analytics Service<br/>:8006]
        NOTIF[Notification Service<br/>:8007]
        SCHED[Scheduler Service<br/>Celery Beat]
    end

    subgraph INFRA["Infrastructure"]
        PG[(PostgreSQL 16<br/>:5432)]
        RD2[(Redis 7<br/>:6379)]
        MN[MinIO / S3<br/>:9000]
        PR[Prometheus<br/>:9090]
        GF[Grafana<br/>:3001]
    end

    WEB -->|HTTPS| TR
    TR -->|route /api/*| GW
    GW -->|JWT verify| AUTH
    GW -->|proxy| HUNTER
    GW -->|proxy| MARKET
    GW -->|proxy| IMGPIPE
    GW -->|proxy| PUBLISH
    GW -->|proxy| ANALYT
    GW -->|proxy| NOTIF

    HUNTER -->|scrape| TT
    HUNTER -->|scrape| AE
    HUNTER -->|scrape| AM
    HUNTER -->|scrape| FB
    HUNTER -->|scrape| GT
    HUNTER -->|scrape| RD
    HUNTER -->|AI analysis| DS
    MARKET -->|generate| DS
    IMGPIPE -->|generate| IM
    PUBLISH -->|publish| SH
    ANALYT -->|fetch| SH
    NOTIF -->|send| NT

    HUNTER -->|tasks| RD2
    MARKET -->|tasks| RD2
    IMGPIPE -->|tasks| RD2
    PUBLISH -->|tasks| RD2
    ANALYT -->|tasks| RD2
    NOTIF -->|tasks| RD2
    SCHED -->|schedule| RD2

    HUNTER & MARKET & IMGPIPE & PUBLISH & ANALYT & NOTIF & AUTH -->|read/write| PG
    IMGPIPE -->|store assets| MN
    AUTH -->|sessions/cache| RD2

    SERVICES -->|metrics| PR
    PR -->|visualize| GF
```

---

## 3. Product Lifecycle Data Flow

```mermaid
flowchart LR
    A([Scheduler<br/>triggers]) --> B[Product Hunter<br/>Scraping Workers]
    B --> C{Deduplicate<br/>& Normalize}
    C --> D[DeepSeek<br/>Scoring Engine]
    D --> E[(products_candidates<br/>status=pending)]
    E --> F{Auto-approve?<br/>score > threshold}
    F -->|Yes / Manual| G[Approved Product]
    F -->|No| H[Rejected]
    G --> I[Marketing Agent<br/>Generate copy + SEO]
    G --> J[Image Pipeline<br/>Generate visuals]
    I --> K[(marketing_assets)]
    J --> L[(generated_images<br/>+ S3)]
    K & L --> M[Shopify Publisher]
    M --> N[Shopify Store]
    N --> O[Analytics Agent<br/>Collect metrics]
    O --> P[(analytics)]
    P --> Q{Decision<br/>Engine}
    Q -->|ROAS > 3| R[Scale]
    Q -->|ROAS 1-3| S[Optimize]
    Q -->|ROAS < 1| T[Pause]
    R & S & T --> U[Notifications<br/>Dispatcher]
```

---

## 4. Agent Orchestration

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant MQ as Redis / Celery
    participant PH as Product Hunter
    participant MA as Marketing Agent
    participant IP as Image Pipeline
    participant SP as Shopify Publisher
    participant AN as Analytics
    participant NO as Notifications

    SCH->>MQ: Enqueue hunt_products task
    MQ->>PH: Execute hunt_products
    PH->>PH: Scrape sources (Playwright / Apify)
    PH->>PH: Normalize + Deduplicate
    PH->>PH: DeepSeek scoring
    PH->>MQ: Enqueue notify_new_candidates
    MQ->>NO: Send "new winners" notification

    Note over PH,MA: On manual/auto approval

    PH->>MQ: Enqueue generate_marketing(product_id)
    PH->>MQ: Enqueue generate_images(product_id)

    MQ->>MA: Execute generate_marketing
    MA->>MA: DeepSeek — branding + copy
    MA-->>MQ: marketing_complete event

    MQ->>IP: Execute generate_images
    IP->>IP: Prompt generation
    IP->>IP: Image model API call
    IP->>IP: Quality review
    IP->>IP: Upload to S3
    IP-->>MQ: images_complete event

    Note over MA,SP: Both assets ready

    MQ->>SP: Execute publish_product
    SP->>SP: Shopify Admin API
    SP-->>MQ: published event
    MQ->>NO: Send "product published" notification

    loop Every 6 hours
        SCH->>MQ: Enqueue collect_analytics
        MQ->>AN: Execute collect_analytics
        AN->>AN: Fetch Shopify + Ad metrics
        AN->>AN: Run decision engine
        AN-->>MQ: decision event (scale/optimize/pause)
        MQ->>NO: Send ROAS alert if threshold crossed
    end
```

---

## 5. Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as API Gateway
    participant AU as Auth Service
    participant RD as Redis
    participant DB as PostgreSQL

    C->>GW: POST /api/auth/login {email, password}
    GW->>AU: Forward request
    AU->>DB: SELECT user WHERE email
    AU->>AU: Verify bcrypt hash
    AU->>RD: Store refresh token hash (TTL 30d)
    AU-->>GW: {access_token (15min), refresh_token (30d)}
    GW-->>C: Set HttpOnly cookie + return access_token

    Note over C,GW: Subsequent requests

    C->>GW: GET /api/products (Authorization: Bearer <access_token>)
    GW->>AU: Validate JWT (internal call)
    AU->>AU: Verify signature + expiry
    AU-->>GW: {user_id, role, store_ids}
    GW->>GW: Inject X-User-* headers
    GW->>GW: Forward to target service

    Note over C,RD: Token refresh

    C->>GW: POST /api/auth/refresh {refresh_token}
    GW->>AU: Forward
    AU->>RD: Validate refresh token hash
    AU->>AU: Rotate: revoke old, issue new pair
    AU->>RD: Store new refresh token hash
    AU-->>C: New token pair
```

---

## 6. Multi-Store Architecture

```mermaid
graph TD
    U[User Account] --> S1[Store A<br/>mystore1.myshopify.com]
    U --> S2[Store B<br/>mystore2.myshopify.com]
    U --> S3[Store C<br/>mystore3.myshopify.com]

    S1 & S2 & S3 --> PH[Product Hunter<br/>shared pool]
    S1 --> MA1[Marketing<br/>Store A context]
    S2 --> MA2[Marketing<br/>Store B context]
    S3 --> MA3[Marketing<br/>Store C context]

    S1 --> PUB1[Publisher → Shopify A]
    S2 --> PUB2[Publisher → Shopify B]
    S3 --> PUB3[Publisher → Shopify C]

    S1 & S2 & S3 --> AN[Analytics<br/>per-store metrics]
```

Every DB row is tagged with `store_id`. The API Gateway enforces store ownership: a user can only access `store_id` values that belong to their account.

---

## 7. Infrastructure Topology (Docker Compose)

```mermaid
graph TB
    subgraph docker["Docker Network: ase_network"]
        TR[traefik:80/443]
        GW[gateway:8000]
        FE[dashboard:3000]
        AU[auth:8001]
        PH[product-hunter:8002]
        MA[marketing:8003]
        IP[image-pipeline:8004]
        SP[shopify-publisher:8005]
        AN[analytics:8006]
        NO[notifications:8007]
        SC[scheduler/beat]

        PH_W[product-hunter-worker]
        MA_W[marketing-worker]
        IP_W[image-worker]
        SP_W[publisher-worker]
        AN_W[analytics-worker]
        NO_W[notification-worker]

        PG[(postgres:5432)]
        RD[(redis:6379)]
        MN[(minio:9000)]
        PR[prometheus:9090]
        GF[grafana:3001]
    end

    TR --> GW
    TR --> FE
    GW --> AU & PH & MA & IP & SP & AN & NO
    PH --> PH_W
    MA --> MA_W
    IP --> IP_W
    SP --> SP_W
    AN --> AN_W
    NO --> NO_W
    SC --> RD
    PH_W & MA_W & IP_W & SP_W & AN_W & NO_W --> RD
    PH_W & MA_W & IP_W & SP_W & AN_W & NO_W & AU & GW --> PG
    IP_W --> MN
    AU --> RD
    PR --> GF
```

---

## 8. Service Responsibilities & Ports

| Service | Port | Responsibility | Workers |
|---|---|---|---|
| Traefik | 80/443 | Reverse proxy, TLS termination | — |
| API Gateway | 8000 | Auth middleware, routing, rate limiting | — |
| Dashboard (Next.js) | 3000 | Web UI (BFF pattern) | — |
| Auth Service | 8001 | JWT, refresh tokens, users, API keys | — |
| Product Hunter | 8002 | Scraping, scoring, candidate mgmt | `product-hunter-worker` |
| Marketing | 8003 | Branding, copy, ad generation | `marketing-worker` |
| Image Pipeline | 8004 | Prompt gen, image gen, S3 upload | `image-worker` |
| Shopify Publisher | 8005 | Shopify Admin API operations | `publisher-worker` |
| Analytics | 8006 | Metrics collection, ROAS decisions | `analytics-worker` |
| Notifications | 8007 | Multi-channel dispatch | `notification-worker` |
| Scheduler | — | Celery Beat, cron orchestration | — |
| PostgreSQL | 5432 | Primary data store | — |
| Redis | 6379 | Cache, Celery broker/backend, sessions | — |
| MinIO | 9000 | S3-compatible asset storage | — |
| Prometheus | 9090 | Metrics scraping | — |
| Grafana | 3001 | Metrics visualization | — |

---

## 9. Inter-Service Communication Rules

| Pattern | When to use | Implementation |
|---|---|---|
| Sync HTTP | User-facing requests only | Via API Gateway → service |
| Async Task | Background operations | Celery task on named queue |
| Event notification | Cross-service side-effects | Celery task (fire-and-forget) |
| Cache read | Hot data, session data | Redis GET/SETEX |
| Direct DB query | Within service own domain only | SQLAlchemy session |

**Services never call each other directly.** All cross-service async work goes through named Celery queues.

---

## 10. Security Architecture

```mermaid
graph LR
    A[Internet] -->|TLS 1.3| B[Traefik]
    B -->|internal| C[API Gateway]
    C -->|verify JWT| D[Auth Service]
    D -->|validated| C
    C -->|X-User-ID header| E[Target Service]
    E -->|RLS store_id check| F[(PostgreSQL)]

    G[Encrypted at rest] -.-> H[Shopify tokens<br/>Fernet encryption]
    G -.-> I[API keys<br/>bcrypt hash]
    G -.-> J[Passwords<br/>bcrypt hash]
```

**Layers:**
1. **Transport**: TLS 1.3 via Traefik (Let's Encrypt in prod)
2. **Network**: All services on private Docker network; only Traefik exposed
3. **Auth**: JWT RS256 (asymmetric keys), 15-min access tokens
4. **Authorization**: Role-based (Admin / Operator / Viewer) + store ownership check
5. **Data**: Shopify access tokens encrypted with Fernet before DB storage
6. **Input**: Pydantic validation on all endpoints; parameterized SQL via SQLAlchemy
7. **Rate limiting**: Sliding window per IP and per user_id in Redis

---

## 11. Observability Architecture

Every service exposes:
- `GET /health` — liveness probe
- `GET /ready` — readiness probe
- `GET /metrics` — Prometheus scrape endpoint

Structured JSON logs flow: service → stdout → Loki (or CloudWatch in prod).

Agent runs are recorded in `agent_logs` with token usage and AI cost tracking.
