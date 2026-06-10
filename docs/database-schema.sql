-- =============================================================================
-- ASE — PostgreSQL 16 Schema
-- Version: 1.0.0
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- for fuzzy title search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- for JSONB + composite indexes

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE user_role AS ENUM ('admin', 'operator', 'viewer');

CREATE TYPE product_status AS ENUM (
    'pending',
    'analyzing',
    'approved',
    'rejected',
    'publishing',
    'published',
    'archived'
);

CREATE TYPE asset_status AS ENUM ('draft', 'generating', 'approved', 'active', 'archived');

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
    'store_disconnected',
    'weekly_report'
);

CREATE TYPE analytics_decision AS ENUM ('scale', 'optimize', 'pause', 'insufficient_data');

CREATE TYPE schedule_frequency AS ENUM (
    'hourly', 'every_6h', 'every_12h', 'daily', 'weekly'
);

CREATE TYPE image_type AS ENUM (
    'hero', 'lifestyle', 'infographic', 'before_after',
    'banner', 'ad_square', 'ad_story'
);

CREATE TYPE log_level AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');

-- =============================================================================
-- USERS & AUTHENTICATION
-- =============================================================================

CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    role            user_role   NOT NULL DEFAULT 'operator',
    is_active       BOOLEAN     NOT NULL DEFAULT true,
    is_verified     BOOLEAN     NOT NULL DEFAULT false,
    avatar_url      TEXT,
    timezone        VARCHAR(100) DEFAULT 'UTC',
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role) WHERE is_active = true;

-- ---------------------------------------------------------------------------

CREATE TABLE refresh_tokens (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL UNIQUE,
    jti             VARCHAR(255) NOT NULL UNIQUE, -- JWT ID for revocation
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked         BOOLEAN     NOT NULL DEFAULT false,
    revoked_at      TIMESTAMPTZ,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_jti ON refresh_tokens(jti) WHERE revoked = false;

-- Auto-cleanup expired tokens (requires pg_cron in prod or application-level job)

-- ---------------------------------------------------------------------------

CREATE TABLE api_keys (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    key_hash        VARCHAR(255) NOT NULL UNIQUE,
    key_prefix      VARCHAR(12)  NOT NULL, -- e.g. "ase_k_abc1" for UI display
    scopes          TEXT[]       NOT NULL DEFAULT '{}',
    expires_at      TIMESTAMPTZ,
    last_used_at    TIMESTAMPTZ,
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = true;

-- =============================================================================
-- STORES
-- =============================================================================

CREATE TABLE stores (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                    VARCHAR(255) NOT NULL,
    shopify_domain          VARCHAR(255) UNIQUE NOT NULL, -- mystore.myshopify.com
    shopify_access_token    TEXT        NOT NULL,         -- Fernet encrypted
    shopify_store_id        VARCHAR(100),
    shopify_plan            VARCHAR(100),                 -- basic, shopify, advanced
    currency                VARCHAR(10)  NOT NULL DEFAULT 'USD',
    timezone                VARCHAR(100) NOT NULL DEFAULT 'UTC',
    is_active               BOOLEAN      NOT NULL DEFAULT true,
    last_synced_at          TIMESTAMPTZ,
    settings                JSONB        NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stores_user_id ON stores(user_id);
CREATE INDEX idx_stores_domain ON stores(shopify_domain);
CREATE INDEX idx_stores_active ON stores(user_id) WHERE is_active = true;

-- =============================================================================
-- PRODUCT CANDIDATES
-- =============================================================================

CREATE TABLE products_candidates (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id            UUID        REFERENCES stores(id) ON DELETE SET NULL,

    -- Identity
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    source              VARCHAR(100) NOT NULL, -- tiktok_creative, tiktok_shop, aliexpress, amazon, facebook_ads, google_trends, reddit, temu
    source_url          TEXT,
    source_product_id   VARCHAR(255),
    source_hash         VARCHAR(64)  UNIQUE, -- SHA-256 dedup key

    -- Pricing
    cost                DECIMAL(10,2),
    recommended_price   DECIMAL(10,2),
    estimated_margin    DECIMAL(5,2),         -- percentage 0-100

    -- AI Scoring (0.00 - 100.00)
    demand_score        DECIMAL(5,2),
    competition_score   DECIMAL(5,2),         -- 100 = no competition
    trend_score         DECIMAL(5,2),
    engagement_score    DECIMAL(5,2),
    saturation_score    DECIMAL(5,2),         -- 100 = not saturated
    branding_score      DECIMAL(5,2),
    margin_score        DECIMAL(5,2),
    success_score       DECIMAL(5,2),         -- weighted composite

    -- Metadata
    category            VARCHAR(255),
    tags                TEXT[]       NOT NULL DEFAULT '{}',
    images              JSONB        NOT NULL DEFAULT '[]',  -- [{url, alt, source}]
    raw_data            JSONB        NOT NULL DEFAULT '{}',  -- original scraped payload
    ai_analysis         JSONB        NOT NULL DEFAULT '{}',  -- full DeepSeek response
    ai_model            VARCHAR(100),
    ai_tokens_used      INTEGER,
    ai_cost             DECIMAL(10,6),

    -- Status & Workflow
    status              product_status NOT NULL DEFAULT 'pending',
    rejection_reason    TEXT,
    approved_by         UUID        REFERENCES users(id),
    approved_at         TIMESTAMPTZ,
    scraped_at          TIMESTAMPTZ,
    analyzed_at         TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pc_user_id ON products_candidates(user_id);
CREATE INDEX idx_pc_store_id ON products_candidates(store_id);
CREATE INDEX idx_pc_status ON products_candidates(status);
CREATE INDEX idx_pc_success_score ON products_candidates(success_score DESC) WHERE status = 'approved';
CREATE INDEX idx_pc_source ON products_candidates(source);
CREATE INDEX idx_pc_created_at ON products_candidates(created_at DESC);
CREATE INDEX idx_pc_title_trgm ON products_candidates USING gin(title gin_trgm_ops);

-- =============================================================================
-- PRODUCTS PUBLISHED (Shopify)
-- =============================================================================

CREATE TABLE products_published (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id            UUID        REFERENCES products_candidates(id) ON DELETE SET NULL,
    store_id                UUID        NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_id                 UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Shopify IDs
    shopify_product_id      VARCHAR(100) UNIQUE,
    shopify_variant_ids     TEXT[]       NOT NULL DEFAULT '{}',
    shopify_collection_ids  TEXT[]       NOT NULL DEFAULT '{}',
    shopify_handle          VARCHAR(500),

    -- Product data
    title                   VARCHAR(500) NOT NULL,
    description_html        TEXT,
    vendor                  VARCHAR(255),
    product_type            VARCHAR(255),
    tags                    TEXT[]       NOT NULL DEFAULT '{}',

    -- Pricing
    price                   DECIMAL(10,2) NOT NULL,
    compare_at_price        DECIMAL(10,2),
    cost_per_item           DECIMAL(10,2),

    -- SEO
    seo_title               VARCHAR(255),
    seo_description         TEXT,

    -- Variants & Options
    variants                JSONB        NOT NULL DEFAULT '[]',
    options                 JSONB        NOT NULL DEFAULT '[]',
    images                  JSONB        NOT NULL DEFAULT '[]',

    -- Status
    status                  VARCHAR(50)  NOT NULL DEFAULT 'draft', -- draft, active, archived
    published_at            TIMESTAMPTZ,
    last_synced_at          TIMESTAMPTZ,

    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pp_store_id ON products_published(store_id);
CREATE INDEX idx_pp_status ON products_published(status);
CREATE INDEX idx_pp_shopify_id ON products_published(shopify_product_id);
CREATE INDEX idx_pp_candidate_id ON products_published(candidate_id);

-- =============================================================================
-- MARKETING ASSETS
-- =============================================================================

CREATE TABLE marketing_assets (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id        UUID        REFERENCES products_candidates(id) ON DELETE CASCADE,
    store_id            UUID        REFERENCES stores(id) ON DELETE CASCADE,
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Branding
    brand_name          VARCHAR(255),
    tagline             VARCHAR(500),

    -- Core Content
    short_description   TEXT,         -- ~50 words
    long_description    TEXT,         -- ~300 words
    bullet_points       JSONB        NOT NULL DEFAULT '[]', -- string[]
    faqs                JSONB        NOT NULL DEFAULT '[]', -- [{question, answer}]

    -- SEO
    meta_title          VARCHAR(255),
    meta_description    TEXT,
    keywords            TEXT[]       NOT NULL DEFAULT '{}',

    -- Ad Copy Variants
    hooks               JSONB        NOT NULL DEFAULT '[]', -- 10 string[]
    headlines           JSONB        NOT NULL DEFAULT '[]', -- 5 string[]
    ctas                JSONB        NOT NULL DEFAULT '[]', -- 5 string[]
    ad_copies           JSONB        NOT NULL DEFAULT '[]', -- 5 string[]

    -- Platform-Specific Assets
    facebook_ads        JSONB        NOT NULL DEFAULT '{}',
    instagram_ads       JSONB        NOT NULL DEFAULT '{}',
    tiktok_ads          JSONB        NOT NULL DEFAULT '{}',
    google_ads          JSONB        NOT NULL DEFAULT '{}',
    email_campaigns     JSONB        NOT NULL DEFAULT '{}',
    sms_campaigns       JSONB        NOT NULL DEFAULT '{}',
    push_notifications  JSONB        NOT NULL DEFAULT '{}',

    -- Generation Metadata
    ai_model            VARCHAR(100),
    generation_cost     DECIMAL(10,6),
    tokens_used         INTEGER,

    status              asset_status NOT NULL DEFAULT 'draft',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Image info
    type                image_type  NOT NULL,
    prompt              TEXT        NOT NULL,
    negative_prompt     TEXT,

    -- Storage
    storage_key         TEXT,         -- MinIO/S3 object key
    storage_url         TEXT,         -- CDN/direct URL
    thumbnail_url       TEXT,
    cdn_url             TEXT,

    -- Image Metadata
    width               INTEGER,
    height              INTEGER,
    format              VARCHAR(20),  -- webp, png, jpg
    file_size_bytes     INTEGER,

    -- Generation Metadata
    model               VARCHAR(100),
    provider            VARCHAR(100), -- openai_dalle3, stability_sdxl, etc.
    generation_cost     DECIMAL(10,6),
    generation_time_ms  INTEGER,
    clip_score          DECIMAL(5,4), -- 0.0 - 1.0 quality metric

    -- Status
    status              VARCHAR(50)  NOT NULL DEFAULT 'pending', -- pending, generating, completed, failed, approved, rejected
    error_message       TEXT,
    retry_count         INTEGER      NOT NULL DEFAULT 0,

    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gi_candidate_id ON generated_images(candidate_id);
CREATE INDEX idx_gi_store_id ON generated_images(store_id);
CREATE INDEX idx_gi_status ON generated_images(status);
CREATE INDEX idx_gi_type ON generated_images(type);

-- =============================================================================
-- CAMPAIGNS
-- =============================================================================

CREATE TABLE campaigns (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id                UUID        NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_id                 UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id              UUID        REFERENCES products_published(id) ON DELETE SET NULL,
    marketing_asset_id      UUID        REFERENCES marketing_assets(id) ON DELETE SET NULL,

    name                    VARCHAR(500) NOT NULL,
    platform                VARCHAR(100) NOT NULL, -- facebook, instagram, tiktok, google
    campaign_type           VARCHAR(100),          -- awareness, traffic, conversion, retargeting

    -- External Platform IDs
    external_campaign_id    VARCHAR(255),
    external_adset_id       VARCHAR(255),
    external_ad_id          VARCHAR(255),

    -- Budget
    budget_daily            DECIMAL(10,2),
    budget_lifetime         DECIMAL(10,2),
    currency                VARCHAR(10)  NOT NULL DEFAULT 'USD',
    bid_strategy            VARCHAR(100),
    bid_amount              DECIMAL(10,2),

    -- Targeting
    targeting               JSONB        NOT NULL DEFAULT '{}',

    -- Schedule
    start_date              DATE,
    end_date                DATE,

    -- Status
    status                  VARCHAR(50)  NOT NULL DEFAULT 'draft', -- draft, active, paused, completed, archived

    -- Notes
    notes                   TEXT,
    metadata                JSONB        NOT NULL DEFAULT '{}',

    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_store_id ON campaigns(store_id);
CREATE INDEX idx_campaigns_product_id ON campaigns(product_id);
CREATE INDEX idx_campaigns_platform ON campaigns(platform);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- =============================================================================
-- ANALYTICS
-- =============================================================================

CREATE TABLE analytics (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id            UUID        NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    campaign_id         UUID        REFERENCES campaigns(id) ON DELETE SET NULL,
    product_id          UUID        REFERENCES products_published(id) ON DELETE SET NULL,

    -- Time dimension
    date                DATE        NOT NULL,
    hour                SMALLINT,               -- 0-23, NULL for daily aggregates
    granularity         VARCHAR(20) NOT NULL DEFAULT 'daily', -- hourly, daily

    -- Source
    platform            VARCHAR(100),
    source              VARCHAR(255),
    medium              VARCHAR(255),

    -- Traffic metrics
    impressions         INTEGER      NOT NULL DEFAULT 0,
    clicks              INTEGER      NOT NULL DEFAULT 0,
    reach               INTEGER      NOT NULL DEFAULT 0,

    -- Conversion metrics
    add_to_carts        INTEGER      NOT NULL DEFAULT 0,
    checkouts           INTEGER      NOT NULL DEFAULT 0,
    orders              INTEGER      NOT NULL DEFAULT 0,
    revenue             DECIMAL(12,2) NOT NULL DEFAULT 0,
    cost                DECIMAL(12,2) NOT NULL DEFAULT 0,
    refunds             DECIMAL(12,2) NOT NULL DEFAULT 0,

    -- Computed KPIs (stored for query performance)
    ctr                 DECIMAL(8,6),   -- clicks / impressions
    cpc                 DECIMAL(10,2),  -- cost / clicks
    cpa                 DECIMAL(10,2),  -- cost / orders
    cpm                 DECIMAL(10,2),  -- (cost / impressions) * 1000
    roas                DECIMAL(8,4),   -- revenue / cost
    conversion_rate     DECIMAL(8,6),   -- orders / clicks
    aov                 DECIMAL(10,2),  -- revenue / orders
    profit              DECIMAL(12,2),  -- revenue - cost - refunds

    -- Decision
    auto_decision       analytics_decision,
    decision_applied    BOOLEAN      NOT NULL DEFAULT false,
    decision_applied_at TIMESTAMPTZ,
    decision_applied_by UUID         REFERENCES users(id),

    -- Snapshot metadata
    collected_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE(store_id, campaign_id, product_id, date, hour, platform, granularity)
);

CREATE INDEX idx_analytics_store_date ON analytics(store_id, date DESC);
CREATE INDEX idx_analytics_campaign ON analytics(campaign_id, date DESC);
CREATE INDEX idx_analytics_product ON analytics(product_id, date DESC);
CREATE INDEX idx_analytics_roas ON analytics(store_id, roas DESC) WHERE date >= CURRENT_DATE - INTERVAL '30 days';

-- Materialized view for dashboard summary (refreshed daily by scheduler)
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
-- AGENT LOGS
-- =============================================================================

CREATE TABLE agent_logs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name      VARCHAR(100) NOT NULL,
    run_id          UUID        NOT NULL,    -- groups all logs for one agent execution

    -- Context
    store_id        UUID        REFERENCES stores(id) ON DELETE SET NULL,
    user_id         UUID        REFERENCES users(id) ON DELETE SET NULL,
    task_id         UUID,                   -- FK to tasks.id (not enforced, tasks may be deleted)

    -- Log entry
    level           log_level   NOT NULL,
    message         TEXT        NOT NULL,
    context         JSONB       NOT NULL DEFAULT '{}',

    -- Performance
    duration_ms     INTEGER,
    tokens_used     INTEGER,
    ai_cost         DECIMAL(10,6),

    -- Error
    error_type      VARCHAR(255),
    error_traceback TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Monthly partitions (create programmatically or via pg_partman)
CREATE TABLE agent_logs_2025_01 PARTITION OF agent_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE agent_logs_2025_06 PARTITION OF agent_logs
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');
CREATE TABLE agent_logs_default PARTITION OF agent_logs DEFAULT;

CREATE INDEX idx_agent_logs_agent_run ON agent_logs(agent_name, run_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at DESC);
CREATE INDEX idx_agent_logs_level ON agent_logs(level) WHERE level IN ('ERROR', 'CRITICAL');
CREATE INDEX idx_agent_logs_store ON agent_logs(store_id, created_at DESC);

-- =============================================================================
-- TASKS (Celery task tracking)
-- =============================================================================

CREATE TABLE tasks (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    celery_task_id  VARCHAR(255) UNIQUE,

    -- Identity
    task_name       VARCHAR(255) NOT NULL,
    task_queue      VARCHAR(100) NOT NULL DEFAULT 'default',

    -- Context
    store_id        UUID        REFERENCES stores(id) ON DELETE SET NULL,
    user_id         UUID        REFERENCES users(id) ON DELETE SET NULL,
    parent_task_id  UUID        REFERENCES tasks(id) ON DELETE SET NULL,

    -- Input / Output
    kwargs          JSONB       NOT NULL DEFAULT '{}',
    result          JSONB,

    -- Status
    status          task_status NOT NULL DEFAULT 'pending',

    -- Timing
    eta             TIMESTAMPTZ,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,

    -- Retries
    retry_count     INTEGER     NOT NULL DEFAULT 0,
    max_retries     INTEGER     NOT NULL DEFAULT 3,
    error_message   TEXT,
    error_traceback TEXT,

    -- Priority (lower = higher priority)
    priority        SMALLINT    NOT NULL DEFAULT 5,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_status ON tasks(status) WHERE status NOT IN ('success', 'failure');
CREATE INDEX idx_tasks_celery_id ON tasks(celery_task_id);
CREATE INDEX idx_tasks_store_id ON tasks(store_id, created_at DESC);
CREATE INDEX idx_tasks_name ON tasks(task_name, created_at DESC);

-- =============================================================================
-- NOTIFICATIONS
-- =============================================================================

CREATE TABLE notifications (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id        UUID        REFERENCES stores(id) ON DELETE CASCADE,

    -- Content
    title           VARCHAR(500) NOT NULL,
    body            TEXT,
    event_type      notification_event NOT NULL,
    severity        VARCHAR(20)  NOT NULL DEFAULT 'info', -- info, warning, error, critical

    -- Channels requested
    channels        TEXT[]       NOT NULL DEFAULT '{}',

    -- Delivery status: {"email": "sent", "discord": "failed", "telegram": "pending"}
    delivery_status JSONB        NOT NULL DEFAULT '{}',

    -- Reference entity
    reference_type  VARCHAR(100),  -- product_candidate, product_published, campaign, agent
    reference_id    UUID,

    -- User-facing state
    is_read         BOOLEAN      NOT NULL DEFAULT false,
    read_at         TIMESTAMPTZ,

    metadata        JSONB        NOT NULL DEFAULT '{}',

    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_store ON notifications(store_id, created_at DESC);
CREATE INDEX idx_notifications_event ON notifications(event_type, created_at DESC);

-- =============================================================================
-- SETTINGS
-- =============================================================================

CREATE TABLE settings (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        REFERENCES users(id) ON DELETE CASCADE,
    store_id    UUID        REFERENCES stores(id) ON DELETE CASCADE,
    category    VARCHAR(100) NOT NULL, -- general, notifications, agents, scoring, publishing, branding
    key         VARCHAR(255) NOT NULL,
    value       JSONB        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE NULLS NOT DISTINCT (user_id, store_id, category, key)
);

CREATE INDEX idx_settings_user ON settings(user_id, category);
CREATE INDEX idx_settings_store ON settings(store_id, category);

-- =============================================================================
-- SCHEDULED JOBS
-- =============================================================================

CREATE TABLE scheduled_jobs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id        UUID        REFERENCES stores(id) ON DELETE CASCADE,

    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    task_name       VARCHAR(255) NOT NULL,
    task_kwargs     JSONB        NOT NULL DEFAULT '{}',

    -- Schedule
    frequency       schedule_frequency NOT NULL,
    cron_expression VARCHAR(100),        -- override if frequency = 'custom' (future)

    -- Execution state
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    last_run_at     TIMESTAMPTZ,
    last_run_status VARCHAR(50),         -- success, failure
    next_run_at     TIMESTAMPTZ,
    run_count       INTEGER      NOT NULL DEFAULT 0,
    failure_count   INTEGER      NOT NULL DEFAULT 0,

    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sched_jobs_user ON scheduled_jobs(user_id);
CREATE INDEX idx_sched_jobs_active ON scheduled_jobs(next_run_at) WHERE is_active = true;

-- =============================================================================
-- AUDIT LOG (append-only)
-- =============================================================================

CREATE TABLE audit_log (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        REFERENCES users(id) ON DELETE SET NULL,
    store_id    UUID        REFERENCES stores(id) ON DELETE SET NULL,
    action      VARCHAR(255) NOT NULL,          -- CREATE_PRODUCT, APPROVE_PRODUCT, DELETE_STORE, etc.
    entity_type VARCHAR(100) NOT NULL,
    entity_id   UUID,
    old_values  JSONB,
    new_values  JSONB,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE audit_log_2025 PARTITION OF audit_log
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE audit_log_2026 PARTITION OF audit_log
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE audit_log_default PARTITION OF audit_log DEFAULT;

CREATE INDEX idx_audit_user ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);

-- =============================================================================
-- UPDATED_AT TRIGGER FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'users', 'stores', 'products_candidates', 'products_published',
        'marketing_assets', 'generated_images', 'campaigns', 'tasks',
        'settings', 'scheduled_jobs', 'api_keys'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION update_updated_at()',
            t
        );
    END LOOP;
END;
$$;

-- =============================================================================
-- ROW LEVEL SECURITY (enable for production multi-tenancy)
-- =============================================================================

-- Enable RLS on tenant-scoped tables
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE products_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE products_published ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (application sets app.current_user_id via SET LOCAL)
-- Services use a dedicated DB role with BYPASSRLS for service-level queries
CREATE POLICY stores_isolation ON stores
    USING (user_id = current_setting('app.current_user_id', true)::uuid);

-- =============================================================================
-- DATABASE ROLES
-- =============================================================================

-- Application role (used by services, has full DML access)
CREATE ROLE ase_app WITH LOGIN PASSWORD 'REPLACE_IN_ENV';
GRANT CONNECT ON DATABASE ase TO ase_app;
GRANT USAGE ON SCHEMA public TO ase_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ase_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ase_app;
ALTER ROLE ase_app BYPASSRLS; -- Services enforce ownership in application layer

-- Read-only role (for analytics/Grafana)
CREATE ROLE ase_readonly WITH LOGIN PASSWORD 'REPLACE_IN_ENV';
GRANT CONNECT ON DATABASE ase TO ase_readonly;
GRANT USAGE ON SCHEMA public TO ase_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ase_readonly;

-- Migration role (for Alembic)
CREATE ROLE ase_migration WITH LOGIN PASSWORD 'REPLACE_IN_ENV' CREATEROLE;
GRANT ALL ON SCHEMA public TO ase_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ase_migration;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ase_migration;
