SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enquiry_id TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    company_name TEXT,
    email_address TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    country TEXT NOT NULL,
    service_interested TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    preferred_contact_method TEXT NOT NULL,
    preferred_contact_time TEXT NOT NULL,
    visitor_ip_address TEXT NOT NULL,
    submission_date_time TEXT NOT NULL,
    browser_information TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    device_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    admin_notes TEXT NOT NULL DEFAULT '',
    last_updated_time TEXT NOT NULL,
    deleted_status INTEGER NOT NULL DEFAULT 0 CHECK (deleted_status IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_enquiries_status ON enquiries(status);
CREATE INDEX IF NOT EXISTS idx_enquiries_submitted ON enquiries(submission_date_time DESC);
CREATE INDEX IF NOT EXISTS idx_enquiries_email ON enquiries(email_address);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'super_admin',
    two_factor_secret TEXT,
    two_factor_enabled INTEGER NOT NULL DEFAULT 0 CHECK (two_factor_enabled IN (0, 1)),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    ip_address TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (admin_user_id) REFERENCES admin_users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at DESC);

CREATE TABLE IF NOT EXISTS website_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_name TEXT NOT NULL,
    section_name TEXT NOT NULL,
    content_key TEXT NOT NULL,
    content_value TEXT NOT NULL DEFAULT '',
    content_type TEXT NOT NULL DEFAULT 'text',
    updated_by INTEGER,
    updated_at TEXT NOT NULL,
    UNIQUE(page_name, content_key),
    FOREIGN KEY (updated_by) REFERENCES admin_users(id) ON DELETE SET NULL
);
"""
