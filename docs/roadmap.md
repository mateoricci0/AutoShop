# ASE — Implementation Roadmap

## Overview

6 phases, each validated before the next begins.
Each phase produces a working, testable vertical slice — not scaffolding.

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6
  Arch       Infra +     Product     Marketing   Shopify     Analytics   Polish +
  Design     Auth +      Hunter      + Images    Publisher   + Notif.    Prod-Ready
             Dashboard   Agent
             Skeleton
```

---

## Phase 0 — Architecture & Design (Current)
**Goal:** Complete technical blueprint. No implementation.

**Deliverables:**
- [x] `ARCHITECTURE.md` — System topology, all Mermaid diagrams
- [x] `docs/technical-design.md` — Detailed service design decisions
- [x] `docs/database-schema.sql` — Complete PostgreSQL DDL
- [x] `docs/folder-structure.md` — Full monorepo directory tree
- [x] `docs/api-contracts.md` — All API endpoints documented
- [x] `docs/roadmap.md` — This document

**Gate:** Architecture validated by stakeholders before Phase 1 starts.

---

## Phase 1 — Infrastructure + Auth + Dashboard Skeleton
**Duration:** ~2 weeks
**Goal:** Everything boots, users can log in, stores can be connected, dashboard shell is visible.

### Week 1 — Backend Foundation
- [ ] Monorepo scaffolding (all service directories, shared package)
- [ ] `shared/python/ase_shared` package:
  - Database (SQLAlchemy async, Alembic)
  - Redis client
  - Celery config
  - Structured logging (structlog)
  - Encryption utilities
  - Base exception hierarchy
- [ ] Alembic initial migration (all 13 tables)
- [ ] Auth Service:
  - Register / Login / Refresh / Logout
  - JWT RS256 (generate keys in `scripts/generate-keys.sh`)
  - Store CRUD + Shopify connection test
  - Role-based access (admin/operator/viewer)
- [ ] API Gateway:
  - JWT middleware
  - Redis rate limiting
  - HTTPX proxy routes
  - SSE endpoint (stub)

### Week 2 — Frontend + Docker
- [ ] Next.js 15 project setup (TypeScript, TailwindCSS, shadcn/ui, Zustand, React Query)
- [ ] Auth pages (login, register)
- [ ] Dashboard layout (sidebar, header, store switcher)
- [ ] Overview page (placeholder widgets)
- [ ] Settings page (profile, store management)
- [ ] Docker Compose (postgres, redis, minio, traefik, all services)
- [ ] `scripts/setup.sh` + `scripts/generate-keys.sh`
- [ ] `README.md` with local setup instructions
- [ ] GitHub Actions CI (lint + test for auth + gateway)

**Definition of Done:**
- User can register, login, connect a Shopify store, see the dashboard shell
- All services boot via `docker compose up`
- Auth service tests ≥ 80% coverage

---

## Phase 2 — Product Hunter Agent
**Duration:** ~2 weeks
**Goal:** The system can discover and score product candidates autonomously.

### Week 3 — Scraping Infrastructure
- [ ] `BaseScraper` ABC + `PlaywrightScraper` base (browser pool)
- [ ] Scraper implementations:
  - TikTok Creative Center (Playwright)
  - AliExpress (HTTP + Playwright fallback)
  - Amazon Movers & Shakers (HTTP)
  - Facebook Ad Library (Playwright)
  - Google Trends (HTTP API)
  - Reddit (Reddit API or HTTP)
- [ ] Normalizer (scraper output → `ScrapedProduct` standard schema)
- [ ] Deduplicator (SHA-256 hash + Redis bloom filter)
- [ ] Celery worker setup for `products.scrape` queue
- [ ] Product Hunter API routes (candidates CRUD + job trigger)

### Week 4 — Scoring + UI
- [ ] DeepSeek scoring integration:
  - Prompt template for product analysis
  - 7-dimension score extraction
  - Weighted `success_score` calculation
- [ ] Celery tasks: `hunt_products`, `score_candidate`, `batch_score`
- [ ] Dashboard: Products page
  - Candidates table (filter by status, source, score)
  - Candidate detail page (scores, raw data, AI analysis)
  - Approve / Reject actions
- [ ] Scheduler: default `hunt_products` every 6h
- [ ] Product Hunter tests ≥ 80% coverage

**Definition of Done:**
- Running `docker compose up` + triggering a hunt job discovers real products
- Candidates appear in the dashboard with scores
- User can approve/reject from the UI

---

## Phase 3 — Marketing & Image Pipeline
**Duration:** ~2 weeks
**Goal:** Approved products get full marketing content and product images automatically.

### Week 5 — Marketing Agent
- [ ] `LLMProvider` abstraction (DeepSeek + OpenAI + Anthropic)
- [ ] Jinja2 prompt templates for all content types
- [ ] Context builder (product → rich LLM context)
- [ ] Output parsers for structured JSON extraction
- [ ] Quality validator
- [ ] Generate all marketing assets:
  - Brand name, tagline, descriptions, bullets, FAQs
  - SEO (meta title, description, 10 keywords)
  - 10 hooks, 5 headlines, 5 CTAs, 5 ad copies
  - Platform-specific: Facebook, Instagram, TikTok, Google, Email
- [ ] Marketing Service API + Celery worker
- [ ] Dashboard: Marketing page (assets list + detail editor)

### Week 6 — Image Pipeline
- [ ] `ImageProvider` abstraction (OpenAI DALL·E 3 + Stability AI)
- [ ] Prompt generator (product data → image prompt per type)
- [ ] 7 image types: hero, lifestyle, infographic, before_after, banner, ad_square, ad_story
- [ ] CLIP-score quality review (auto-reject below threshold)
- [ ] MinIO S3 upload + CDN URL
- [ ] Image Pipeline API + Celery worker
- [ ] Dashboard: Image gallery per product with approve/regenerate
- [ ] SSE real-time progress updates during generation

**Definition of Done:**
- Approving a product automatically triggers marketing + image generation
- All assets visible in dashboard within minutes
- Copy can be manually edited before publishing

---

## Phase 4 — Shopify Publisher
**Duration:** ~1.5 weeks
**Goal:** Products publish to Shopify with one click (or automatically).

### Week 7 — Shopify Integration
- [ ] Async Shopify Admin API client (per-store rate limiter, retry with backoff)
- [ ] Publish checklist validation
- [ ] Full publish flow:
  - Upload images to Shopify CDN
  - Create product with variants
  - Set collections + tags
  - Configure SEO
  - Set pricing
- [ ] Update + archive product operations
- [ ] Shopify webhook receiver (product updated, order created)
- [ ] Publisher API + Celery worker

### Week 7.5 — Publisher UI
- [ ] Dashboard: Shopify page (published products, sync status)
- [ ] One-click publish from product detail page
- [ ] Publish status real-time updates (SSE)
- [ ] Store management page (connect multiple stores)
- [ ] Publisher tests ≥ 80% coverage

**Definition of Done:**
- Full flow: scrape → approve → generate content → publish to Shopify works end-to-end
- Multi-store publishing works correctly

---

## Phase 5 — Analytics + Notifications + Scheduler
**Duration:** ~2 weeks
**Goal:** Full observability of performance + automated decision recommendations.

### Week 8 — Analytics
- [ ] Shopify Analytics integration (orders, revenue, sessions)
- [ ] KPI calculator (CTR, CPC, CPA, ROAS, conversion rate, AOV, LTV)
- [ ] Decision engine (scale / optimize / pause rules)
- [ ] Analytics table population
- [ ] Materialized view refresh job
- [ ] Analytics API routes (summary, timeseries, product performance)
- [ ] Dashboard: Performance page
  - ROAS chart (line, 30d)
  - Revenue + profit widgets
  - Campaign table with decisions
  - Per-product performance drill-down

### Week 9 — Notifications + Scheduler Polish
- [ ] Notification Service:
  - Email (SMTP via SMTP2Go/SES)
  - Discord (webhook)
  - Telegram (Bot API)
  - Slack (incoming webhook)
  - Retry logic (3x with 5-min delays)
- [ ] All notification events wired:
  - New winner found
  - Critical agent error
  - Product published
  - ROAS drop below threshold
  - ROAS scale opportunity
- [ ] Dashboard: Notifications bell + unread count
- [ ] Notification settings page (channel preferences per event)
- [ ] Scheduler UI in settings (view/edit/pause scheduled jobs)
- [ ] Agent Monitor page (status, last run, cost, token usage)
- [ ] Logs page (filterable agent logs)

**Definition of Done:**
- Full system runs autonomously; user notified on Discord/Telegram when winner found
- Dashboard shows real ROAS data for published products
- Agent monitor shows all agent run history

---

## Phase 6 — Production Hardening
**Duration:** ~2 weeks
**Goal:** Production-ready: security audit, full test coverage, CI/CD, observability.

### Week 10 — Testing + Security
- [ ] Achieve 80% test coverage across all services
- [ ] E2E tests (Playwright):
  - Login flow
  - Product approval + publish flow
  - Settings configuration
- [ ] Security review:
  - All Shopify tokens confirmed encrypted at rest
  - JWT RS256 keys rotated by `generate-keys.sh`
  - CSRF protection on state-changing endpoints
  - Input validation on all endpoints (Pydantic)
  - SQL injection verified (SQLAlchemy parameterized only)
  - XSS headers (Content-Security-Policy via Traefik)
  - Rate limiting verified under load
- [ ] Dependency audit (pip-audit + npm audit)

### Week 11 — Observability + CI/CD
- [ ] Prometheus metrics on all services (`/metrics`)
- [ ] Grafana dashboards:
  - ASE Overview (revenue, ROAS, agent status)
  - Celery Worker Health
  - Product Hunter Pipeline
- [ ] Health check endpoints (`/health`, `/ready`)
- [ ] GitHub Actions CI complete (all services, matrix build)
- [ ] GitHub Actions CD (staging auto-deploy, prod manual)
- [ ] Docker production images (multi-stage, non-root user, slim)
- [ ] `docker-compose.prod.yml` (resource limits, no volumes, env injection)
- [ ] `scripts/setup.sh` — one-command local setup
- [ ] OpenAPI docs aggregated at `/api/docs`
- [ ] Semantic versioning (`CHANGELOG.md`)

### Week 12 — Documentation + Kubernetes Prep
- [ ] `README.md` complete (architecture overview, quick start, env vars)
- [ ] `docs/` complete (all 6 docs finalized)
- [ ] Kubernetes manifests in `infra/k8s/` (deployments, services, ingress, configmaps)
- [ ] Kubernetes HPA configs (scale workers on CPU/memory)
- [ ] Migration guide (Docker Compose → K8s)

**Definition of Done:**
- Zero high-severity security findings
- All CI checks pass
- Single `./scripts/setup.sh && docker compose up` boots the full system
- Grafana dashboard shows live metrics

---

## Future Roadmap (Post-v1)

| Feature | Phase | Priority |
|---|---|---|
| Meta Ads API integration | 7 | High |
| TikTok Ads API integration | 7 | High |
| Google Ads API integration | 7 | Medium |
| Auto-apply ROAS decisions (feature flag) | 7 | High |
| AI product description A/B testing | 8 | Medium |
| Competitor price monitoring | 8 | Medium |
| Supplier direct integration (AliExpress DSers) | 8 | High |
| Customer segmentation + LTV prediction | 9 | Medium |
| Video ad generation (AI) | 9 | Low |
| White-label / agency mode (sub-accounts) | 10 | High |
| Mobile app (React Native) | 10 | Low |
| Kubernetes production deployment | Ongoing | High |
| Per-service database isolation | Ongoing | Medium |

---

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| Phase 0 | Monorepo | Atomic changes, shared code, small team |
| Phase 0 | Shared PostgreSQL (Phase 1) | Reduce ops overhead; migrate in Phase 4 |
| Phase 0 | Celery + Redis (not RabbitMQ) | Redis already required; simpler stack |
| Phase 0 | DeepSeek primary AI | Cost-efficient; OpenAI/Claude available as premium fallback |
| Phase 0 | JWT RS256 (not HS256) | Public key can be distributed to all services without sharing secret |
| Phase 0 | Fernet for Shopify tokens | Reversible encryption needed (must decrypt to use); not bcrypt |
| Phase 0 | SSE (not WebSocket) | One-way server→client events sufficient; simpler infra |
| Phase 0 | Traefik + FastAPI Gateway | Traefik for routing/TLS; FastAPI for auth middleware logic |
| Phase 0 | MinIO for images | S3-compatible locally; swap endpoint URL for AWS S3 in prod |
