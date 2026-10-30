CREATE TABLE IF NOT EXISTS content_categories (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(24) NOT NULL CHECK (module IN ('threat', 'resource', 'training')),
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(140) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(module, slug)
);

CREATE TABLE IF NOT EXISTS content_tags (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(24) NOT NULL CHECK (module IN ('threat', 'resource', 'training')),
    name VARCHAR(80) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(module, slug)
);

CREATE TABLE IF NOT EXISTS content_items (
    id BIGSERIAL PRIMARY KEY,
    module VARCHAR(24) NOT NULL CHECK (module IN ('threat', 'resource', 'training')),
    title VARCHAR(220) NOT NULL,
    slug VARCHAR(240) NOT NULL,
    short_description VARCHAR(420) NOT NULL,
    full_description TEXT NOT NULL,
    category VARCHAR(120) NOT NULL,
    tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    author_name VARCHAR(180) NOT NULL DEFAULT '',
    severity VARCHAR(24) NOT NULL DEFAULT '',
    difficulty VARCHAR(24) NOT NULL DEFAULT '',
    access_type VARCHAR(24) NOT NULL DEFAULT 'free',
    price_cents BIGINT NOT NULL DEFAULT 0 CHECK (price_cents >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    version VARCHAR(80) NOT NULL DEFAULT '',
    thumbnail_path TEXT,
    banner_path TEXT,
    asset_paths JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'unpublished', 'archived', 'deleted')),
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    display_order INTEGER NOT NULL DEFAULT 0,
    view_count BIGINT NOT NULL DEFAULT 0,
    download_count BIGINT NOT NULL DEFAULT 0,
    publish_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_by BIGINT NOT NULL,
    updated_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(module, slug)
);

CREATE INDEX IF NOT EXISTS idx_content_items_public
    ON content_items(module, status, is_pinned DESC, display_order, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_items_category ON content_items(module, category);
CREATE INDEX IF NOT EXISTS idx_content_items_tags ON content_items USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_content_items_search
    ON content_items USING GIN(to_tsvector('english', title || ' ' || short_description || ' ' || full_description));

CREATE TABLE IF NOT EXISTS content_events (
    id BIGSERIAL PRIMARY KEY,
    content_id BIGINT REFERENCES content_items(id) ON DELETE SET NULL,
    admin_user_id BIGINT,
    event_type VARCHAR(80) NOT NULL,
    event_details TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_events_item ON content_events(content_id, created_at DESC);
