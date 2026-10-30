CREATE TABLE IF NOT EXISTS security_tools (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(180) NOT NULL,
    slug VARCHAR(220) NOT NULL UNIQUE,
    thumbnail_path TEXT NOT NULL,
    banner_path TEXT NOT NULL,
    gallery_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    short_description VARCHAR(320) NOT NULL,
    full_description TEXT NOT NULL,
    version VARCHAR(80) NOT NULL,
    category VARCHAR(120) NOT NULL,
    price_cents BIGINT NOT NULL DEFAULT 0 CHECK (price_cents >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    license_name VARCHAR(160) NOT NULL,
    operating_system VARCHAR(180) NOT NULL,
    platform VARCHAR(180) NOT NULL,
    tool_file_path TEXT NOT NULL,
    tool_file_name TEXT NOT NULL,
    tool_file_sha256 CHAR(64) NOT NULL,
    documentation_path TEXT NOT NULL,
    screenshot_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    release_notes TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'published', 'unpublished', 'archived', 'deleted')),
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    display_order INTEGER NOT NULL DEFAULT 0,
    view_count BIGINT NOT NULL DEFAULT 0,
    download_count BIGINT NOT NULL DEFAULT 0,
    created_by BIGINT NOT NULL,
    updated_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_security_tools_public
    ON security_tools(status, is_pinned DESC, display_order, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_tools_category
    ON security_tools(category);
CREATE INDEX IF NOT EXISTS idx_security_tools_popular
    ON security_tools(download_count DESC, view_count DESC);

CREATE TABLE IF NOT EXISTS security_tool_events (
    id BIGSERIAL PRIMARY KEY,
    tool_id BIGINT REFERENCES security_tools(id) ON DELETE SET NULL,
    admin_user_id BIGINT,
    event_type VARCHAR(80) NOT NULL,
    event_details TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_tool_events_tool
    ON security_tool_events(tool_id, created_at DESC);
