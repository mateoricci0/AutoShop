# ASE — Technical Design (Personal Use)

## 1. Decisiones Arquitectónicas

### 1.1 Monorepo
**Decisión:** Repo único con `services/`, `shared/`, `infra/`.

**Razón:** Cambios atómicos entre servicios, paquete shared Python sin gestión de versiones entre repos. Ideal para un solo desarrollador.

---

### 1.2 Sin API Gateway separado
**Decisión:** Next.js BFF (API routes) hace de proxy hacia los servicios. Nginx como reverse proxy simple.

**Razón:** Un API Gateway independiente es overhead innecesario para uso personal.
- Nginx enruta `/api/auth/*` → auth:8001, `/api/hunter/*` → product-hunter:8002, etc.
- Next.js API routes (`/api/[...proxy]/route.ts`) hacen forward con el session token
- Sin rate limiting complejo (uso personal = tráfico predecible)

**Nginx config base:**
```nginx
location /api/auth/     { proxy_pass http://auth:8001/; }
location /api/hunter/   { proxy_pass http://product-hunter:8002/; }
location /api/marketing/{ proxy_pass http://marketing:8003/; }
location /api/images/   { proxy_pass http://image-pipeline:8004/; }
location /api/publisher/{ proxy_pass http://shopify-publisher:8005/; }
location /api/analytics/{ proxy_pass http://analytics:8006/; }
location /api/notif/    { proxy_pass http://notifications:8007/; }
location /              { proxy_pass http://dashboard:3000/; }
```

---

### 1.3 Auth Simplificada (Single User)
**Decisión:** Sin tabla `users`. Una contraseña de admin en `.env`. Session tokens opacos en Redis.

**Implementación:**
```python
# Auth Service — solo 3 endpoints:
# POST /login    → verifica bcrypt(password) vs ADMIN_PASSWORD_HASH del .env
# POST /logout   → revoca session token en Redis
# GET  /verify   → valida session token (usado por otros servicios)

ADMIN_PASSWORD_HASH = bcrypt(env.ADMIN_PASSWORD)

# Session token: UUID aleatorio → almacenado en Redis con TTL 30 días
# Cookie: HttpOnly, Secure, SameSite=Strict
```

**Ventaja:** Sin complejidad de JWT, RS256, refresh tokens, roles. El token es simplemente una clave Redis.

---

### 1.4 Base de Datos — Sin Multi-Tenancy
**Decisión:** PostgreSQL único. Sin RLS. Sin roles de DB complejos. Un solo `ase_app` role.

Sin `user_id` en las tablas (no hay usuarios, solo un admin). `store_id` sigue siendo útil para separar datos entre tiendas Shopify personales.

Tablas eliminadas vs diseño SaaS:
- ~~`users`~~ → reemplazado por variable de entorno
- ~~`refresh_tokens`~~ → reemplazado por `admin_session` simple
- ~~`api_keys`~~ → no necesario para uso personal
- ~~`audit_log`~~ → overhead innecesario
- ~~`user_role` enum~~ → no hay roles

---

### 1.5 Celery Queues
**Decisión:** Mismas colas nombradas por dominio. Un worker por dominio en Docker Compose.

```python
QUEUES = {
    "products.scrape",    # scraping workers (CPU/network bound)
    "products.analyze",   # DeepSeek scoring
    "marketing.generate", # copy generation
    "images.generate",    # imagen (más lento, separado)
    "publish.shopify",    # rate-limited API calls
    "analytics.collect",  # métricas
    "notifications.send", # dispatch rápido
}
```

En `docker-compose.yml` cada worker consume solo su cola:
```yaml
ph-worker:
  command: celery -A app.tasks.celery_app worker -Q products.scrape,products.analyze
img-worker:
  command: celery -A app.tasks.celery_app worker -Q images.generate --concurrency=2
```

---

### 1.6 Abstracción LLM
```python
class LLMProvider(ABC):
    async def complete(self, messages, model, temperature, max_tokens) -> LLMResponse: ...

class DeepSeekProvider(LLMProvider): ...   # Principal (más barato)
class OpenAIProvider(LLMProvider): ...     # Fallback premium
class AnthropicProvider(LLMProvider): ...  # Fallback premium

# Selección vía env:
# LLM_PRIMARY=deepseek
# LLM_PREMIUM=openai (o anthropic)
```

Token usage y coste se registran en `agent_logs.ai_cost` para llevar control del gasto.

---

### 1.7 Shopify Client — Rate Limiting
Shopify REST Admin API: 2 req/s (Basic), 4 req/s (Advanced).

```python
class ShopifyClient:
    _limiters: dict[str, AsyncLeakyBucket]  # uno por store_id
    
    async def request(self, store_id, method, endpoint, **kwargs):
        async with self._limiters[store_id]:
            resp = await self._session.request(...)
            if resp.status == 429:
                retry_after = float(resp.headers.get("Retry-After", 2))
                await asyncio.sleep(retry_after)
                return await self.request(store_id, method, endpoint, **kwargs)
```

Retry policy: tenacity, exponential backoff 1s→2s→4s→8s→16s, max 5 intentos.

---

### 1.8 Image Pipeline
**Providers:**
```python
class ImageProvider(ABC):
    async def generate(self, prompt, negative_prompt, size) -> ImageResult: ...

class OpenAIDalleProvider(ImageProvider): ...    # DALL·E 3
class StabilityAIProvider(ImageProvider): ...    # SDXL
```

**Quality check:** CLIP score automático. Si < 0.25 → regenera 1 vez → si falla de nuevo → estado `needs_review`.

**Storage:** MinIO bucket `ase-images/{store_id}/{product_id}/{type}/{uuid}.webp`

---

### 1.9 Analytics — Decision Engine
```python
class DecisionEngine:
    SCALE_ROAS    = 3.0
    OPTIMIZE_ROAS = 1.0
    MIN_SPEND     = 20.0  # no decidir con < $20 gastados
    
    def evaluate(self, row: Analytics) -> analytics_decision:
        if row.cost < self.MIN_SPEND:
            return "insufficient_data"
        if row.roas >= self.SCALE_ROAS:
            return "scale"
        if row.roas >= self.OPTIMIZE_ROAS:
            return "optimize"
        return "pause"
```

**v1: Solo recomienda.** El sistema notifica pero no actúa automáticamente. Auto-apply en v2 detrás de flag en `settings`.

---

## 2. Frontend (Next.js 15)

### App Router
```
app/
├── login/page.tsx              # Pantalla de login (password)
├── (dashboard)/
│   ├── layout.tsx              # Sidebar + header
│   ├── page.tsx                # Overview (redirect → /overview)
│   ├── overview/page.tsx       # KPIs + estado agentes
│   ├── products/
│   │   ├── page.tsx            # Tabla candidatos
│   │   └── [id]/page.tsx       # Detalle + aprobar/rechazar
│   ├── published/page.tsx      # Productos en Shopify
│   ├── marketing/
│   │   ├── page.tsx            # Assets de marketing
│   │   └── [id]/page.tsx       # Editor de copy
│   ├── performance/page.tsx    # ROAS + métricas
│   ├── agents/page.tsx         # Estado de agentes + logs
│   └── settings/page.tsx       # Config tiendas + notificaciones + scheduler
└── api/
    └── [...proxy]/route.ts     # BFF proxy a servicios
```

### Estado
- **React Query:** Toda data del servidor. `staleTime: 30s`.
- **Zustand:** Solo estado UI (sidebar abierto, tienda activa, modales).
- **Formularios:** React Hook Form + Zod.

### Real-time
SSE desde el servicio que corresponda:
- `GET /api/hunter/v1/jobs/{id}/stream` → progreso de scraping
- `GET /api/images/v1/jobs/{id}/stream` → progreso de generación
- `GET /api/notif/v1/stream` → notificaciones en tiempo real

---

## 3. Shared Package (`ase_shared`)

```
shared/python/ase_shared/
├── database/
│   ├── base.py        # DeclarativeBase + TimestampMixin
│   ├── session.py     # async_sessionmaker (asyncpg)
│   └── migrations/    # Alembic env + versions
├── models/            # SQLAlchemy ORM (fuente de verdad del schema)
├── security/
│   ├── encryption.py  # Fernet para Shopify tokens en DB
│   └── hashing.py     # bcrypt helpers
├── logging/
│   └── config.py      # structlog JSON, context vars
├── cache/
│   └── redis.py       # aioredis client factory
├── messaging/
│   └── celery_config.py  # Celery app factory + queue defs
└── exceptions.py      # ASEError hierarchy
```

Instalado como paquete editable en cada imagen Docker:
```dockerfile
COPY shared/python /shared
RUN pip install -e /shared
```

---

## 4. Variables de Entorno

```bash
# === INFRAESTRUCTURA ===
DATABASE_URL=postgresql+asyncpg://ase_app:password@postgres:5432/ase
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
ENVIRONMENT=development

# === AUTH ===
ADMIN_PASSWORD=tu_contraseña_segura
SESSION_TTL_DAYS=30
SECRET_KEY=clave_aleatoria_32_chars  # para CSRF y misc
FERNET_KEY=clave_fernet_base64       # para cifrar tokens Shopify

# === AI ===
DEEPSEEK_API_KEY=
OPENAI_API_KEY=         # opcional
ANTHROPIC_API_KEY=      # opcional
LLM_PRIMARY=deepseek
LLM_PREMIUM=openai

# === SCRAPING ===
APIFY_API_KEY=          # opcional
BRIGHTDATA_USERNAME=    # opcional
BRIGHTDATA_PASSWORD=    # opcional

# === IMÁGENES ===
STABILITY_API_KEY=      # opcional (si no usas DALL·E)
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=ase-images

# === SHOPIFY ===
SHOPIFY_API_VERSION=2024-10

# === NOTIFICACIONES ===
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
DISCORD_WEBHOOK=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SLACK_WEBHOOK=
```

---

## 5. Testing

Para uso personal el objetivo es funcionalidad correcta, no cobertura corporativa.

```
Unit tests:   Lógica de dominio (scorer, normalizer, decision engine, parsers)
Integration:  Endpoints API con testcontainers (PostgreSQL + Redis reales)
Manual E2E:   Flujo completo en local antes de cada release
```

Herramientas:
- `pytest` + `pytest-asyncio` + `httpx` (AsyncClient)
- `testcontainers-python` para tests de integración
- `ruff` + `mypy` para linting y tipos
- `vitest` + `@testing-library/react` para frontend

---

## 6. Consideraciones de Rendimiento

| Concern | Solución |
|---|---|
| Playwright lento | Pool de 3-5 browsers, scraping en paralelo |
| DeepSeek latencia | httpx async, timeout 30s, resultados cacheados 24h en Redis |
| Shopify rate limits | Leaky bucket por tienda |
| Generación de imágenes | Worker separado, 2 concurrencias máx (coste) |
| Dashboard load | React Query cache + SSR Next.js para carga inicial |
| Analytics queries | Vista materializada para resúmenes diarios |

---

## 7. Escalabilidad (Personal → Productivo)

Si en el futuro quisieras ofreece esto a más usuarios, los cambios necesarios son:
1. Añadir tabla `users` + JWT estándar + RBAC
2. Añadir `user_id` a todas las tablas + RLS
3. Añadir API Gateway con rate limiting por usuario
4. Separar DB por servicio (schema isolation primero)
5. Kubernetes para escalar workers

La estructura de servicios ya está preparada para este salto — solo hay que añadir la capa de autenticación multi-usuario.
