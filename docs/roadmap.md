# ASE — Roadmap de Implementación (Personal Use)

## Resumen de Fases

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
  Arch       Infra +     Product     Marketing   Shopify     Analytics
  Design     Auth +      Hunter      + Images    Publisher   + Notif. +
  ✓DONE      Dashboard   Agent                              Scheduler
             Skeleton
```

Cada fase termina con algo **funcionando de verdad** — no scaffolding.

---

## Phase 0 — Arquitectura y Diseño ✅
**Estado:** Completo

- [x] ARCHITECTURE.md con 9 diagramas Mermaid
- [x] docs/technical-design.md
- [x] docs/database-schema.sql (11 tablas, personal use)
- [x] docs/folder-structure.md
- [x] docs/api-contracts.md
- [x] docs/roadmap.md

---

## Phase 1 — Infraestructura + Auth + Dashboard Skeleton

**Goal:** `docker compose up` → puedes hacer login y ver el dashboard vacío. Tiendas Shopify conectadas.

### Backend Foundation
- [ ] Scaffolding del monorepo (directorios de servicios, paquete shared)
- [ ] `shared/python/ase_shared`:
  - `database/` — SQLAlchemy async + Alembic
  - `cache/redis.py` — aioredis factory
  - `messaging/celery_config.py` — app factory + queues
  - `logging/config.py` — structlog JSON
  - `security/encryption.py` — Fernet para tokens Shopify
  - `security/hashing.py` — bcrypt helpers
  - `exceptions.py`
- [ ] Migración Alembic inicial (todas las tablas)
- [ ] Auth Service (`services/auth/`):
  - `POST /login` — verifica password vs env, crea session en Redis
  - `POST /logout` — revoca session
  - `GET /verify` — valida session token (usado por otros servicios)
  - `GET/POST/PUT/DELETE /stores` — CRUD tiendas Shopify
  - `POST /stores/{id}/test-connection` — verifica token Shopify
- [ ] Nginx config (`infra/nginx/nginx.conf`)

### Frontend
- [ ] Next.js 15 setup (TypeScript, TailwindCSS, shadcn/ui, Zustand, React Query)
- [ ] Pantalla de login (password único)
- [ ] Dashboard layout (sidebar, header, store switcher)
- [ ] Overview page (widgets placeholder)
- [ ] Settings page (gestión de tiendas)
- [ ] BFF proxy (`app/api/[...proxy]/route.ts`)
- [ ] Hook `useSSE.ts` para eventos en tiempo real

### Docker
- [ ] `docker-compose.yml` (postgres, redis, minio, nginx, todos los servicios stub)
- [ ] `docker-compose.dev.yml` (hot-reload para frontend y servicios)
- [ ] `services/*/Dockerfile` (base para todos los servicios — stubs que arrancan OK)
- [ ] `scripts/setup.sh` — clona + configura `.env.local` + levanta stack
- [ ] `scripts/generate-keys.sh` — genera FERNET_KEY + SECRET_KEY + ADMIN_PASSWORD_HASH
- [ ] `scripts/migrate.sh` — ejecuta Alembic

**Definition of Done:**
- `./scripts/setup.sh && docker compose up` funciona sin errores
- Login con contraseña, ver dashboard, conectar una tienda Shopify
- `GET /health` en todos los servicios responde OK

---

## Phase 2 — Product Hunter Agent

**Goal:** El sistema descubre productos automáticamente, los puntúa con IA, aparecen en el dashboard.

### Semana A — Scraping
- [ ] `BaseScraper` ABC + `PlaywrightScraper` base (pool de browsers)
- [ ] Scrapers:
  - TikTok Creative Center (Playwright)
  - AliExpress (HTTP)
  - Amazon Movers & Shakers (HTTP)
  - Facebook Ad Library (Playwright)
  - Google Trends (API)
  - Reddit (HTTP/API)
- [ ] Normalizer: salida de scrapers → `ScrapedProduct` estándar
- [ ] Deduplicator: hash SHA-256 + Redis para check O(1)
- [ ] Celery worker para `products.scrape`

### Semana B — Scoring + UI
- [ ] DeepSeek integration:
  - Prompt template de análisis de producto
  - Extracción de 7 dimensiones de score
  - Cálculo de `success_score` ponderado
- [ ] Celery tasks: `hunt_products`, `score_candidate`
- [ ] Product Hunter API routes (candidatos + jobs)
- [ ] Dashboard: Productos page
  - Tabla de candidatos con filtros (status, fuente, score)
  - Detalle de candidato (scores, análisis IA, imágenes)
  - Botones Aprobar / Rechazar
  - Progreso en tiempo real via SSE
- [ ] Scheduler: job `hunt_products` cada 6h por defecto

**Definition of Done:**
- Trigger manual de scraping desde el dashboard
- Candidatos aparecen con score en < 5 min
- Aprobar/rechazar funciona, status persiste

---

## Phase 3 — Marketing Agent + Image Pipeline

**Goal:** Producto aprobado → assets de marketing y 7 imágenes generados automáticamente.

### Semana C — Marketing Agent
- [ ] `LLMProvider` abstraction (DeepSeek + OpenAI + Anthropic)
- [ ] Templates Jinja2:
  - `branding.j2` — nombre, tagline
  - `description.j2` — short/long description, bullets, FAQs
  - `seo.j2` — meta title, description, keywords
  - `ad_copy.j2` — hooks, headlines, CTAs, copies
  - `ads_platform.j2` — variantes por plataforma
- [ ] Context builder: producto → contexto rico para LLM
- [ ] Output parser: JSON estructurado desde respuesta LLM
- [ ] Quality validator (longitud, campos requeridos)
- [ ] Marketing Service API + worker `marketing.generate`
- [ ] Dashboard: Marketing page (lista assets, editor de copy)

### Semana D — Image Pipeline
- [ ] `ImageProvider` abstraction (DALL·E 3 + Stability AI)
- [ ] Prompt generator por tipo de imagen
- [ ] 7 tipos: hero, lifestyle, infographic, before_after, banner, ad_square, ad_story
- [ ] CLIP score quality check
- [ ] Upload a MinIO + URL CDN
- [ ] Image Pipeline API + worker `images.generate`
- [ ] Dashboard: galería de imágenes por producto (aprobar / regenerar)
- [ ] SSE progress durante generación

**Definition of Done:**
- Aprobar producto → marketing + imágenes generados sin intervención
- Editar copy desde el dashboard y guardar
- Regenerar imagen individual funciona

---

## Phase 4 — Shopify Publisher

**Goal:** Un click publica el producto completo en Shopify (imágenes + copy + precio + SEO).

- [ ] Async Shopify Admin API client con rate limiter por tienda
- [ ] Publish checklist (validación pre-publicación)
- [ ] Flujo completo:
  - Upload de imágenes a Shopify CDN
  - Crear producto con variantes
  - Asignar colecciones + tags
  - Configurar SEO
  - Establecer precios
- [ ] Update + archivar producto
- [ ] Shopify webhook receiver (actualizaciones externas)
- [ ] Publisher API + worker `publish.shopify`
- [ ] Dashboard:
  - Botón "Publicar en Shopify" en detalle de producto
  - Estado en tiempo real (SSE)
  - Lista de productos publicados con sync status
  - Gestión de múltiples tiendas
- [ ] Tests unitarios del publisher (mocked Shopify API)

**Definition of Done:**
- Flujo end-to-end completo: scrape → aprobar → generar → publicar en Shopify real
- Producto aparece en Shopify con imágenes, descripción y precio correcto
- Multi-tienda: publicar en tienda A y tienda B funciona

---

## Phase 5 — Analytics + Notificaciones + Scheduler UI

**Goal:** Sistema corre solo 24/7 y me notifica cuando hay algo que atender.

### Analytics
- [ ] Shopify Analytics integration (órdenes, revenue, sesiones)
- [ ] KPI calculator (CTR, CPC, CPA, ROAS, CVR, AOV, profit)
- [ ] Decision engine (scale/optimize/pause)
- [ ] Refresh de vista materializada (job diario)
- [ ] Analytics API
- [ ] Dashboard: Performance page
  - ROAS chart 30 días
  - Revenue + profit widgets
  - Tabla de campañas con decisiones recomendadas

### Notificaciones
- [ ] Notification dispatcher
- [ ] Channels: Email (SMTP), Discord (webhook), Telegram (Bot API), Slack (webhook)
- [ ] Retry (3x con 5 min de espera)
- [ ] Todos los eventos conectados:
  - Nuevo producto ganador
  - Error crítico de agente
  - Producto publicado
  - ROAS < 1 (alerta pause)
  - ROAS > 3 (alerta scale)
- [ ] Dashboard: bell de notificaciones + contador no leídas
- [ ] Settings: configurar canales por tipo de evento

### Scheduler + Agentes
- [ ] Celery Beat con scheduler de DB
- [ ] Dashboard: Agents page
  - Estado actual de cada agente
  - Última ejecución + duración media
  - Errores recientes
  - Coste de IA acumulado
  - Trigger manual
- [ ] Dashboard: Logs page (filtro por agente, nivel, fecha)
- [ ] Settings: editar frecuencia de jobs programados

**Definition of Done:**
- Sistema corre 48h sin intervención y encuentra candidatos
- Recibo notificación en Telegram cuando hay nuevo ganador
- Dashboard muestra ROAS real de productos publicados

---

## Estimación de Tiempo

| Phase | Semanas | Complejidad |
|---|---|---|
| Phase 0 (Arch) | 1 | ✅ Hecho |
| Phase 1 (Infra + Auth) | 1.5 | Media |
| Phase 2 (Product Hunter) | 2 | Alta (scraping) |
| Phase 3 (Marketing + Images) | 2 | Media |
| Phase 4 (Publisher) | 1.5 | Media |
| Phase 5 (Analytics + Notif) | 2 | Media |
| **Total** | **~10 semanas** | — |

---

## Orden de Prioridad si Hay Restricciones de Tiempo

Si quieres tener algo útil lo antes posible, este es el orden de valor:

1. **Phase 1** — Sin esto nada funciona
2. **Phase 2** — El core del sistema. Sin scraping no hay nada que publicar
3. **Phase 4** — Publicar en Shopify es el objetivo principal
4. **Phase 3** — El contenido manual funciona de momento; los agentes lo automatizan
5. **Phase 5** — Sin analytics puedes revisar Shopify directamente mientras tanto

---

## Decision Log

| Decisión | Razón |
|---|---|
| Sin API Gateway | Overhead innecesario para 1 usuario |
| Auth por password en .env | Máxima simplicidad; no hay gestión de cuentas |
| Sin audit_log / api_keys | Features SaaS que no aportan valor personal |
| Sin RLS | Un solo usuario = sin aislamiento de datos necesario |
| Nginx en vez de Traefik | Más simple, bien conocido, suficiente para uso personal |
| HS256 no RS256 para JWT | Sin distribución de clave pública entre servicios externos |
| Session token opaco en Redis | Más simple y revocable al instante vs JWT |
| Docker Compose sin K8s | Hardware personal no necesita orquestación |
| Cobertura de tests razonable | Foco en funcionalidad, no en métricas corporativas |
