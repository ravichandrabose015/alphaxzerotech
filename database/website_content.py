from datetime import datetime, timezone

from database.database import get_db


DEFAULT_CONTENT = {
    ("home", "hero_title_primary"): ("Hero", "Securing Your"),
    ("home", "hero_title_accent"): ("Hero", "Digital Future."),
    ("home", "hero_description"): ("Hero", "AlphaX ZeroTech delivers advanced cybersecurity services to protect your business, data, and digital future with next-generation security technologies."),
    ("services", "hero_title_primary"): ("Hero", "Our Cyber Security"),
    ("services", "hero_title_accent"): ("Hero", "Services"),
    ("services", "hero_description"): ("Hero", "End-to-end cyber security services engineered to protect your business, data, people, and digital future."),
    ("contact", "page_title"): ("Hero", "Talk to Our Security Experts"),
    ("contact", "page_description"): ("Hero", "Send a secure enquiry and our cyber security team will contact you using your preferred method."),
}


def seed_content() -> None:
    database = get_db()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for (page, key), (section, value) in DEFAULT_CONTENT.items():
        database.execute(
            """INSERT OR IGNORE INTO website_content
            (page_name, section_name, content_key, content_value, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            (page, section, key, value, timestamp),
        )
    database.commit()


def content_for_page(page_name: str) -> dict:
    rows = get_db().execute(
        "SELECT content_key, content_value FROM website_content WHERE page_name = ?",
        (page_name,),
    ).fetchall()
    return {row["content_key"]: row["content_value"] for row in rows}


def all_content():
    return get_db().execute(
        "SELECT * FROM website_content ORDER BY page_name, section_name, content_key"
    ).fetchall()


def update_content(content_id: int, value: str, admin_id: int) -> None:
    database = get_db()
    database.execute(
        "UPDATE website_content SET content_value = ?, updated_by = ?, updated_at = ? WHERE id = ?",
        (
            value[:5000], admin_id,
            datetime.now(timezone.utc).isoformat(timespec="seconds"), content_id,
        ),
    )
    database.commit()
