# Autonomous Shopify Engine (ASE) — Architecture

> **Uso personal:** Un único usuario administrador, 1-3 tiendas Shopify propias.
> Sin overhead de SaaS: sin multi-tenancy complejo, sin RBAC, sin API Gateway.

---

## 1. System Overview

ASE es una plataforma multiagente para uso personal que descubre productos ganadores,
genera contenido de marketing, publica en Shopify y monitoriza el rendimiento —
todo desde un dashboard local.

**Principios de diseño:**
- Cada agente es un servicio independiente con su propio worker Celery
- Toda operación asíncrona va por Celery/Redis
- El dashboard Next.js actúa como BFF (proxy directo a los servicios)
- Un solo usuario; sin gestión de cuentas ni permisos complejos
- Corre completo en una sola máquina con Docker Compose

---

## 2. System Topology

```mermaid
graph TB
    subgraph EXTERNAL["External Systems"]
        TT[TikTok Creative Center]
        AE[AliExpress / Temu]
        AM[Amazon]
        FB[Facebook Ad Library]
        GT[Google Trends]
        RD[Reddit]
        SH[Shopify Admin API]
        DS[DeepSeek API]
        IM[Image Model APIs<br/>DALL·E · Stability AI]
        NT[Notification Channels<br/>Email · Discord · Telegram · Slack]
    end

    subgraph CLIENT["Browser"]
        WEB[Next.js 15 Dashboard<br/>:3000]
    end

    subgraph PROXY["Nginx :80"]
        NG[Reverse Proxy]
    end

    subgraph SERVICES["Agent Services"]
        AUTH[Auth Service<br/>:8001]
        HUNTER[Product Hunter<br/>:8002]
        MARKET[Marketing<br/>:8003]
        IMGPIPE[Image Pipeline<br/>:8004]
        PUBLISH[Shopify Publisher<br/>:8005]
        ANALYT[Analytics<br/>:8006]
        NOTIF[Notifications<br/>:8007]
        SCHED[Scheduler<br/>Celery Beat]
    end

    subgraph INFRA["Infrastructure"]
        PG[(PostgreSQL 16)]
        RD2[(Redis 7)]
        MN[MinIO S3]
        PR[Prometheus]
        GF[Grafana :3001]
    end

    WEB -->|/api/*| NG
    NG --> AUTH & HUNTER & MARKET & IMGPIPE & PUBLISH & ANALYT & NOTIF
    WEB -->|BFF Next.js API routes| AUTH

    HUNTER -->|scrape| TT & AE & AM & FB & GT & RD
    HUNTER -->|AI scoring| DS
    MARKET -->|generate| DS
    IMGPIPE -->|generate| IM
    PUBLISH -->|publish| SH
    ANALYT -->|fetch| SH
    NOTIF -->|send| NT

    HUNTER & MARKET & IMGPIPE & PUBLISH & ANALYT & NOTIF & SCHED -->|tasks| RD2
    HUNTER & MARKET & IMGPIPE & PUBLISH & ANALYT & NOTIF & AUTH -->|read/write| PG
    IMGPIPE -->|assets| MN
    AUTH -->|session cache| RD2
    SERVICES -->|metrics| PR
    PR --> GF
```

---

## 3. Product Lifecycle

```mermaid
flowchart LR
    A([Scheduler<br/>6h]) --> B[Product Hunter<br/>Workers]
    B --> C{Dedup +<br/>Normalize}
    C --> D[DeepSeek<br/>Score 0-100]
    D --> E[(products_candidates)]
    E --> F{Score ><br/>threshold?}
    F -->|Manual approve| G[Approved]
    F -->|Low score| H[Rejected]
    G --> I[Marketing Agent<br/>Copy + SEO]
    G --> J[Image Pipeline<br/>7 tipos de imagen]
    I --> K[(marketing_assets)]
    J --> L[(generated_images + MinIO)]
    K & L --> M[Shopify Publisher]
    M --> N[Shopify Store]
    N --> O[Analytics Agent<br/>Métricas cada 6h]
    O --> P{ROAS?}
    P -->|> 3| Q[Scale]
    P -->|1-3| R[Optimize]
    P -->|< 1| S[Pause]
    Q & R & S --> T[Notificación]
```

---

## 4. Agent Orchestration

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant MQ as Redis/Celery
    participant PH as Product Hunter
    participant MA as Marketing
    participant IP as Image Pipeline
    participant SP as Shopify Publisher
    participant AN as Analytics
    participant NO as Notifications

    SCH->>MQ: hunt_products (cada 6h)
    MQ->>PH: scrape + normalize + deduplicate
    PH->>PH: DeepSeek scoring
    PH->>MQ: notify (nuevos candidatos)
    MQ->>NO: "X nuevos productos encontrados"

    Note over PH,MA: Usuario aprueba desde dashboard

    PH->>MQ: generate_marketing(product_id)
    PH->>MQ: generate_images(product_id)
    MQ->>MA: branding + copy + SEO + ads
    MQ->>IP: 7 tipos de imagen → MinIO

    Note over MA,SP: Ambos assets listos

    MQ->>SP: publish_to_shopify
    SP->>SP: upload images + create product
    MQ->>NO: "Producto publicado en Shopify"

    loop Cada 6h
        SCH->>MQ: collect_analytics
        MQ->>AN: fetch Shopify metrics + calcular ROAS
        AN->>AN: decision engine
        MQ->>NO: alerta si ROAS cruza umbral
    end
```

---

## 5. Auth Flow (Personal Use — Simplified)

```mermaid
sequenceDiagram
    participant B as Browser
    participant N as Next.js BFF
    participant A as Auth Service
    participant R as Redis

    B->>N: POST /api/auth/login {password}
    N->>A: Verify password vs ADMIN_PASSWORD_HASH
    A->>R: Store session token (TTL 30d)
    A-->>B: Set HttpOnly cookie (session_token)

    Note over B,N: Requests autenticados

    B->>N: GET /api/products (cookie)
    N->>A: Validate session_token
    A->>R: GET session_token → valid/invalid
    A-->>N: OK
    N->>N: Forward a service con token interno
```

---

## 6. Infrastructure (Docker Compose — Personal)

```mermaid
graph TB
    subgraph docker["Docker Network: ase"]
        NG[nginx:80]
        FE[dashboard:3000]
        AU[auth:8001]
        PH[product-hunter:8002]
        MA[marketing:8003]
        IP[image-pipeline:8004]
        SP[shopify-publisher:8005]
        AN[analytics:8006]
        NO[notifications:8007]
        SC[scheduler/beat]

        PH_W[ph-worker]
        MA_W[mkt-worker]
        IP_W[img-worker]
        SP_W[pub-worker]
        AN_W[ana-worker]
        NO_W[notif-worker]

        PG[(postgres:5432)]
        RD[(redis:6379)]
        MN[(minio:9000)]
        PR[prometheus:9090]
        GF[grafana:3001]
    end

    NG --> FE & AU & PH & MA & IP & SP & AN & NO
    PH --> PH_W
    MA --> MA_W
    IP --> IP_W
    SP --> SP_W
    AN --> AN_W
    NO --> NO_W
    SC --> RD
    PH_W & MA_W & IP_W & SP_W & AN_W & NO_W --> RD
    PH_W & MA_W & IP_W & SP_W & AN_W & NO_W & AU --> PG
    IP_W --> MN
    AU --> RD
    PR & GF -.->|monitoring| SERVICES
```

---

## 7. Service Summary

| Service | Port | Función |
|---|---|---|
| Nginx | 80 | Reverse proxy simple |
| Dashboard (Next.js) | 3000 | UI + BFF |
| Auth Service | 8001 | Login único, session tokens |
| Product Hunter | 8002 | Scraping + scoring |
| Marketing | 8003 | Copy + SEO + ads con DeepSeek |
| Image Pipeline | 8004 | Generación de imágenes + MinIO |
| Shopify Publisher | 8005 | Shopify Admin API |
| Analytics | 8006 | Métricas + decisiones ROAS |
| Notifications | 8007 | Email/Discord/Telegram/Slack |
| Scheduler | — | Celery Beat (tareas programadas) |
| PostgreSQL | 5432 | Base de datos principal |
| Redis | 6379 | Broker Celery + cache sesiones |
| MinIO | 9000 | Storage S3-compatible |
| Prometheus | 9090 | Métricas |
| Grafana | 3001 | Dashboards de métricas |

---

## 8. Security (Personal Use)

- **Auth:** Una sola contraseña de admin hasheada con bcrypt en `.env`
- **Session:** Token opaco almacenado en Redis, HttpOnly cookie
- **Red:** Todos los servicios en red Docker privada; solo Nginx expuesto en :80
- **Secrets:** Variables de entorno en `.env.local` (git-ignored)
- **Shopify tokens:** Cifrados con Fernet antes de almacenar en DB
- **Transport:** Nginx con certificado auto-firmado local (Let's Encrypt opcional con dominio)

---

## 9. Observability

Cada servicio expone:
- `GET /health` — liveness
- `GET /metrics` — Prometheus scrape

Grafana dashboards:
- ASE Overview (ROAS, revenue, agent status)
- Celery Workers (queue depth, task rate)
- Product Hunter Pipeline (candidates/hour, score distribution)
