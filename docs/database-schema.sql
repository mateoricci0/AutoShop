-- =============================================================================
-- ASE — PostgreSQL 16 Schema (Personal Use)
-- Version: 1.1.0
-- Sin multi-tenancy, sin RLS, sin audit_log, sin api_keys
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE product_status AS ENUM (
    'pending',
    'analyzing',
    'approved',
    'rejected',
    'publishing',
    'published',
    'archived'
);

CREATE TYPE asset_status AS ENUM (
    'draft', 'generating', 'approved', 'active', 'archived'
);

CREATE TYPE task_status AS ENUM (
    'pending', 'started', 'success', 'failure', 'revoked', 'retry'
);

CREATE TYPE notification_event AS ENUM (
    'new_winner',
    'critical_error',
    'product_published',
    'roas_drop',
    'roas_scale',
    'agent_error',
    'store_connected',
    'weekly_report'
);

CREATE TYPE analytics_decision AS ENUM (
    'scale', 'optimize', 'pause', 'insufficient_data'
);

CREATE TYPE schedule_frequency AS ENUM (
    'hourly', 'every_6h', 'every_12h', 'daily', 'weekly'
);

CREATE TYPE image_type AS ENUM (
    'hero', 'lifestyle', 'infographic', 'before_after',
    'banner', 'ad_square', 'ad_story'
);

CREATE TYPE log_level AS ENUM (
    'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
);

-- =============================================================================
-- AUTH (single user)
-- No tabla de roles, no refresh tokens complejos, no api_keys
-- =============================================================================

CREATE TABLE admin_session (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    ip_address  INET,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_session_token ON admin_session(token_hash) WHERE expires_at > NOW();

-- Cleanup automático via tarea Celery diaria
-- DELETE FROM admin_session WHERE expires_at < NOW();

-- =============================================================================
-- STORES (múltiples tiendas Shopify personales)
-- =============================================================================

CREATE TABLE stores (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    VARCHAR(255) NOT NULL,
    shopify_domain          VARCHAR(255) UNIQUE NOT NULL,  -- mystore.myshopify.com
    shopify_access_token    TEXT        NOT NULL,          -- Fernet encrypted
    shopify_store_id        VARCHAR(100),
    shopify_plan            VARCHAR(100),
    currency                VARCHAR(10)  NOT NULL DEFAULT 'USD',
    timezone                VARCHAR(100) NOT NULL DEFAULT 'UTC',
    is_active               BOOLEAN      NOT NULL DEFAULT true,
    last_synced_at          TIMESTAMPTZ,
    settings                JSONB        NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stores_active ON stores(is_active);

-- =============================================================================
-- PRODUCT CANDIDATES
-- =============================================================================

CREATE TABLE products_candidates (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id            UUID        REFERENCES stores(id) ON DELETE SET NULL,

    -- Identificación
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    source              VARCHAR(100) NOT NULL,
    -- tiktok_creative | tiktok_shop | aliexpress | temu | amazon | facebook_ads | google_trends | reddit
    source_url          TEXT,
    source_product_id   VARCHAR(255),
    source_hash         VARCHAR(64)  UNIQUE,  -- SHA-256 dedup

    -- Precios
    cost                DECIMAL(10,2),
    recommended_price   DECIMAL(10,2),
    estimated_margin    DECIMAL(5,2),

    -- Scores AI (0.00 - 100.00)
    demand_score        DECIMAL(5,2),
    competition_score   DECIMAL(5,2),
    trend_score         DECIMAL(5,2),
    engagement_score    DECIMAL(5,2),
    saturation_score    DECIMAL(5,2),
    branding_score      DECIMAL(5,2),
    margin_score        DECIMAL(5,2),
    success_score       DECIMAL(5,2),

    -- Metadata
    category            VARCHAR(255),
    tags                TEXT[]       NOT NULL DEFAULT '{}',
    images              JSONB        NOT NULL DEFAULT '[]',
    raw_data            JSONB        NOT NULL DEFAULT '{}',
    ai_analysis         JSONB        NOT NULL DEFAULT '{}',
    ai_model            VARCHAR(100),
    ai_tokens_used      INTEGER,
    ai_cost             DECIMAL(10,6),

    -- Estado
    status              product_status NOT NULL DEFAULT 'pending',
    rejection_reason    TEXT,
    approved_at         TIMESTAMPTZ,
    scraped_at          TIMESTAMPTZ,
    analyzed_at         TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pc_status ON products_candidates(status);
CREATE INDEX idx_pc_store_id ON products_candidates(store_id);
CREATE INDEX idx_pc_success_score ON products_candidates(success_score DESC)
    WHERE status = 'approved';
CREATE INDEX idx_pc_source ON products_candidates(source);
CREATE INDEX idx_pc_created_at ON products_candidates(created_at DESC);
CREATE INDEX idx_pc_title_trgm ON products_candidates USING gin(title gin_trgm_ops);

-- =============================================================================
-- PRODUCTS PUBLISHED
-- =============================================================================

CREATE TABLE products_published (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id            UUID        REFERENCES products_candidates(id) ON DELETE SET NULL,
    store_id                UUID        NOT NULL REFERENCES stores(id) ON DELETE CASCADE,

    -- Shopify
    shopify_product_id      VARCHAR(100) UNIQUE,
    shopify_variant_ids     TEXT[]       NOT NULL DEFAULT '{}',
    shopify_collection_ids  TEXT[]       NOT NULL DEFAULT '{}',
    shopify_handle          VARCHAR(500),

    -- Producto
    title                   VARCHAR(500) NOT NULL,
    description_html        TEXT,
    vendor                  VARCHAR(255),
    product_type            VARCHAR(255),
    tags                    TEXT[]       NOT NULL DEFAULT '{}',

    -- Precios
    price                   DECIMAL(10,2) NOT NULL,
    compare_at_price        DECIMAL(10,2),
    cost_per_item           DECIMAL(10,2),

    -- SEO
    seo_title               VARCHAR(255),
    seo_description         TEXT,

    -- Variantes e imágenes
    variants                JSONB        NOT NULL DEFAULT '[]',
    options                 JSONB        NOT NULL DEFAULT '[]',
    images                  JSONB        NOT NULL DEFAULT '[]',

    -- Estado
    status                  VARCHAR(50)  NOT NULL DEFAULT 'draft',
    published_at            TIMESTAMPTZ,
    last_synced_at          TIMESTAMPTZ,

    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pp_store_id ON products_published(store_id);
CREATE INDEX idx_pp_status ON products_published(status);
CREATE INDEX idx_pp_shopify_id ON products_published(shopify_product_id);

-- =============================================================================
-- MARKETING ASSETS
-- =============================================================================

CREATE TABLE marketing_assets (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID        REFERENCES products_candidates(id) ON DELETE CASCADE,
    store_id            UUID        REFERENCES stores(id) ON DELETE CASCADE,

    -- Branding
    brand_name          VARCHAR(255),
    tagline             VARCHAR(500),

    -- Contenido
    short_description   TEXT,
    long_description    TEXT,
    bullet_points       JSONB        NOT NULL DEFAULT '[]',
    faqs                JSONB        NOT NULL DEFAULT '[]',

    -- SEO
    meta_title          VARCHAR(255),
    meta_description    TEXT,
    keywords            TEXT[]       NOT NULL DEFAULT '{}',

    -- Copy variants
    hooks               JSONB        NOT NULL DEFAULT '[]',  -- 10
    headlines           JSONB        NOT NULL DEFAULT '[]',  -- 5
    ctas                JSONB        NOT NULL DEFAULT '[]',  -- 5
    ad_copies           JSONB        NOT NULL DEFAULT '[]',  -- 5

    -- Ads por plataforma
    facebook_ads        JSONB        NOT NULL DEFAULT '{}',
    instagram_ads       JSONB        NOT NULL DEFAULT '{}',
    tiktok_ads          JSONB        NOT NULL DEFAULT '{}',
    google_ads          JSONB        NOT NULL DEFAULT '{}',
    email_campaigns     JSONB        NOT NULL DEFAULT '{}',

    -- Metadata generación
    ai_model            VARCHAR(100),
    generation_cost     DECIMAL(10,6),
    tokens_used         INTEGER,

    status              asset_status NOT NULL DEFAULT 'draft',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ma_candidate_id ON marketing_assets(candidate_id);
CREATE INDEX idx_ma_store_id ON marketing_assets(store_id);
CREATE INDEX idx_ma_status ON marketing_assets(status);

-- =============================================================================
-- GENERATED IMAGES
-- =============================================================================

CREATE TABLE generated_images (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID        REFERENCES products_candidates(id) ON DELETE CASCADE,
    store_id            UUID        REFERENCES stores(id) ON DELETE CASCADE,

    type                image_type  NOT NULL,
    prompt              TEXT        NOT NULL,
    negative_prompt     TEXT,

    -- Storage
    storage_key         TEXT,
    storage_url         TEXT,
    thumbnail_url       TEXT,

    -- Metadata imagen
    width               INTEGER,
    height              INTEGER,
    format              VARCHAR(20),
    file_size_bytes     INTEGER,

    -- Metadata generación
    model               VARCHAR(100),
    provider            VARCHAR(100),
    generation_cost     DECIMAL(10,6),
    generation_time_ms  INTEGER,
    clip_score          DECIMAL(5,4),

    status              VARCHAR(50)  NOT NULL DEFAULT 'pending',
    error_message       TEXT,
    retry_count         INTEGER      NOT NULL DEFAULT 0,

    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gi_candidate_id ON generated_images(candidate_id);
CREATE INDEX idx_gi_type ON generated_images(type);
CREATE INDEX idx_gi_status ON generated_images(status);

-- =============================================================================
-- CAMPAIGNS
-- =============================================================================

CREATE TABLE campaigns (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id                UUID        NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    product_id              UUID        REFERENCES products_published(id) ON DELETE SET NULL,
    marketing_asset_id      UUID        REFERENCES marketing_assets(id) ON DELETE SET NULL,

    name                    VARCHAR(500) NOT NULL,
    platform                VARCHAR(100) NOT NULL,
    campaign_type           VARCHAR(100),

    external_campaign_id    VARCHAR(255),
    external_adset_id       VARCHAR(255),

    budget_daily            DECIMAL(10,2),
    budget_lifetime         DECIMAL(10,2),
    currency                VARCHAR(10)  NOT NULL DEFAULT 'USD',

    targeting               JSONB        NOT NULL DEFAULT '{}',
    start_date              DATE,
    end_date                DATE,

    status                  VARCHAR(50)  NOT NULL DEFAULT 'draft',
    notes                   TEXT,

    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_store_id ON campaigns(store_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- =============================================================================
-- ANALYTICS
-- =============================================================================

CREATE TABLE analytics (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id            UUID        NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    campaign_id         UUID        REFERENCES campaigns(id) ON DELETE SET NULL,
    product_id          UUID        REFERENCES products_published(id) ON DELETE SET NULL,

    date                DATE        NOT NULL,
    hour                SMALLINT,
    granularity         VARCHAR(20) NOT NULL DEFAULT 'daily',
    platform            VARCHAR(100),

    -- Tráfico
    impressions         INTEGER      NOT NULL DEFAULT 0,
    clicks              INTEGER      NOT NULL DEFAULT 0,
    reach               INTEGER      NOT NULL DEFAULT 0,

    -- Conversiones
    add_to_carts        INTEGER      NOT NULL DEFAULT 0,
    checkouts           INTEGER      NOT NULL DEFAULT 0,
    orders              INTEGER      NOT NULL DEFAULT 0,
    revenue             DECIMAL(12,2) NOT NULL DEFAULT 0,
    cost                DECIMAL(12,2) NOT NULL DEFAULT 0,
    refunds             DECIMAL(12,2) NOT NULL DEFAULT 0,

    -- KPIs calculados
    ctr                 DECIMAL(8,6),
    cpc                 DECIMAL(10,2),
    cpa                 DECIMAL(10,2),
    cpm                 DECIMAL(10,2),
    roas                DECIMAL(8,4),
    conversion_rate     DECIMAL(8,6),
    aov                 DECIMAL(10,2),
    profit              DECIMAL(12,2),

    auto_decision       analytics_decision,
    collected_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE(store_id, campaign_id, product_id, date, hour, platform, granularity)
);

CREATE INDEX idx_analytics_store_date ON analytics(store_id, date DESC);
CREATE INDEX idx_analytics_product ON analytics(product_id, date DESC);
CREATE INDEX idx_analytics_roas ON analytics(store_id, roas DESC)
    WHERE date >= CURRENT_DATE - INTERVAL '30 days';

CREATE MATERIALIZED VIEW analytics_daily_summary AS
SELECT
    store_id,
    date,
    SUM(impressions)   AS total_impressions,
    SUM(clicks)        AS total_clicks,
    SUM(orders)        AS total_orders,
    SUM(revenue)       AS total_revenue,
    SUM(cost)          AS total_cost,
    SUM(profit)        AS total_profit,
    CASE WHEN SUM(cost) > 0 THEN SUM(revenue) / SUM(cost) ELSE 0 END AS overall_roas,
    COUNT(DISTINCT campaign_id) AS active_campaigns
FROM analytics
GROUP BY store_id, date;

CREATE UNIQUE INDEX ON analytics_daily_summary(store_id, date);

-- =============================================================================
-- AGENT LOGS (particionado por mes)
-- =============================================================================

CREATE TABLE agent_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name      VARCHAR(100) NOT NULL,
    run_id          UUID        NOT NULL,
    store_id        UUID        REFERENCES stores(id) ON DELETE SET NULL,
    task_id         UUID,

    level           log_level   NOT NULL,
    message         TEXT        NOT NULL,
    context         JSONB       NOT NULL DEFAULT '{}',

    duration_ms     INTEGER,
    tokens_used     INTEGER,
    ai_cost         DECIMAL(10,6),

    error_type      VARCHAR(255),
    error_traceback TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE agent_logs_default PARTITION OF agent_logs DEFAULT;

CREATE INDEX idx_agent_logs_run ON agent_logs(agent_name, run_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at DESC);
CREATE INDEX idx_agent_logs_errors ON agent_logs(level, created_at DESC)
    WHERE level IN ('ERROR', 'CRITICAL');

-- =============================================================================
-- TASKS
-- =============================================================================

CREATE TABLE tasks (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    celery_task_id  VARCHAR(255) UNIQUE,
    task_name       VARCHAR(255) NOT NULL,
    task_queue      VARCHAR(100) NOT NULL DEFAULT 'default',
    store_id        UUID        REFERENCES stores(id) ON DELETE SET NULL,
    parent_task_id  UUID        REFERENCES tasks(id) ON DELETE SET NULL,

    kwargs          JSONB       NOT NULL DEFAULT '{}',
    result          JSONB,

    status          task_status NOT NULL DEFAULT 'pending',

    eta             TIMESTAMPTZ,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,

    retry_count     INTEGER     NOT NULL DEFAULT 0,
    max_retries     INTEGER     NOT NULL DEFAULT 3,
    error_message   TEXT,

    priority        SMALLINT    NOT NULL DEFAULT 5,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_status ON tasks(status)
    WHERE status NOT IN ('success', 'failure');
CREATE INDEX idx_tasks_celery_id ON tasks(celery_task_id);
CREATE INDEX idx_tasks_name ON tasks(task_name, created_at DESC);

-- =============================================================================
-- NOTIFICATIONS
-- =============================================================================

CREATE TABLE notifications (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id        UUID        REFERENCES stores(id) ON DELETE CASCADE,

    title           VARCHAR(500) NOT NULL,
    body            TEXT,
    event_type      notification_event NOT NULL,
    severity        VARCHAR(20)  NOT NULL DEFAULT 'info',

    channels        TEXT[]       NOT NULL DEFAULT '{}',
    delivery_status JSONB        NOT NULL DEFAULT '{}',

    reference_type  VARCHAR(100),
    reference_id    UUID,

    is_read         BOOLEAN      NOT NULL DEFAULT false,
    read_at         TIMESTAMPTZ,

    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_read ON notifications(is_read, created_at DESC);
CREATE INDEX idx_notifications_event ON notifications(event_type, created_at DESC);

-- =============================================================================
-- SETTINGS
-- =============================================================================

CREATE TABLE settings (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id    UUID        REFERENCES stores(id) ON DELETE CASCADE,
    category    VARCHAR(100) NOT NULL,
    -- general | notifications | agents | scoring | publishing | branding | ai
    key         VARCHAR(255) NOT NULL,
    value       JSONB        NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (store_id, category, key)
);

CREATE INDEX idx_settings_store ON settings(store_id, category);

-- =============================================================================
-- SCHEDULED JOBS
-- =============================================================================

CREATE TABLE scheduled_jobs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id        UUID        REFERENCES stores(id) ON DELETE CASCADE,

    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    task_name       VARCHAR(255) NOT NULL,
    task_kwargs     JSONB        NOT NULL DEFAULT '{}',

    frequency       schedule_frequency NOT NULL,
    cron_expression VARCHAR(100),

    is_active       BOOLEAN      NOT NULL DEFAULT true,
    last_run_at     TIMESTAMPTZ,
    last_run_status VARCHAR(50),
    next_run_at     TIMESTAMPTZ,
    run_count       INTEGER      NOT NULL DEFAULT 0,
    failure_count   INTEGER      NOT NULL DEFAULT 0,

    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sched_active ON scheduled_jobs(next_run_at)
    WHERE is_active = true;

-- =============================================================================
-- UPDATED_AT TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'stores', 'products_candidates', 'products_published',
        'marketing_assets', 'generated_images', 'campaigns',
        'tasks', 'settings', 'scheduled_jobs'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_updated_at BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at()', t
        );
    END LOOP;
END;
$$;

-- =============================================================================
-- SINGLE APP ROLE (personal use — no separate roles needed)
-- =============================================================================

CREATE ROLE ase_app WITH LOGIN PASSWORD 'CHANGE_IN_ENV';
GRANT CONNECT ON DATABASE ase TO ase_app;
GRANT USAGE ON SCHEMA public TO ase_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ase_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ase_app;
