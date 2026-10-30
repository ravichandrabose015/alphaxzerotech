import json
import re
from decimal import Decimal, InvalidOperation

from database.marketplace_database import marketplace_cursor


PUBLIC_STATUS = "published"
ADMIN_STATUSES = {"draft", "published", "unpublished", "archived", "deleted"}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:190] or "security-tool"


def unique_slug(name: str, exclude_id=None) -> str:
    base = slugify(name)
    candidate = base
    suffix = 2
    with marketplace_cursor() as cursor:
        while True:
            cursor.execute(
                "SELECT 1 FROM security_tools WHERE slug = %s AND (%s::bigint IS NULL OR id <> %s)",
                (candidate, exclude_id, exclude_id),
            )
            if cursor.fetchone() is None:
                return candidate
            candidate = f"{base[:180]}-{suffix}"
            suffix += 1


def price_to_cents(value: str) -> int:
    try:
        amount = Decimal((value or "0").strip())
    except InvalidOperation as error:
        raise ValueError("Price must be a valid number.") from error
    if amount < 0:
        raise ValueError("Price cannot be negative.")
    return int((amount * 100).quantize(Decimal("1")))


def list_public_tools(query="", category="", sort="latest", limit=None):
    clauses = ["status = 'published'", "deleted_at IS NULL"]
    parameters = []
    if query:
        clauses.append("(name ILIKE %s OR short_description ILIKE %s OR category ILIKE %s)")
        term = f"%{query[:120]}%"
        parameters.extend([term, term, term])
    if category:
        clauses.append("category = %s")
        parameters.append(category[:120])
    order = {
        "popular": "is_pinned DESC, download_count DESC, view_count DESC, display_order ASC",
        "price_low": "is_pinned DESC, price_cents ASC, display_order ASC",
        "price_high": "is_pinned DESC, price_cents DESC, display_order ASC",
        "name": "is_pinned DESC, name ASC, display_order ASC",
    }.get(sort, "is_pinned DESC, display_order ASC, published_at DESC NULLS LAST, created_at DESC")
    limit_sql = " LIMIT %s" if limit else ""
    if limit:
        parameters.append(limit)
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM security_tools WHERE {' AND '.join(clauses)} ORDER BY {order}{limit_sql}",
            parameters,
        )
        return cursor.fetchall()


def public_categories():
    with marketplace_cursor() as cursor:
        cursor.execute(
            "SELECT category, COUNT(*) AS tool_count FROM security_tools "
            "WHERE status = 'published' AND deleted_at IS NULL "
            "GROUP BY category ORDER BY category"
        )
        return cursor.fetchall()


def homepage_groups(limit=4):
    with marketplace_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM security_tools WHERE status = 'published' AND deleted_at IS NULL "
            "AND is_featured = TRUE ORDER BY is_pinned DESC, display_order ASC, published_at DESC LIMIT %s",
            (limit,),
        )
        featured = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM security_tools WHERE status = 'published' AND deleted_at IS NULL "
            "ORDER BY published_at DESC NULLS LAST, created_at DESC LIMIT %s", (limit,),
        )
        latest = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM security_tools WHERE status = 'published' AND deleted_at IS NULL "
            "ORDER BY download_count DESC, view_count DESC, published_at DESC NULLS LAST LIMIT %s", (limit,),
        )
        popular = cursor.fetchall()
    return {"featured": featured, "latest": latest, "popular": popular}


def get_public_tool(slug: str, count_view=False):
    with marketplace_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM security_tools WHERE slug = %s AND status = 'published' AND deleted_at IS NULL",
            (slug,),
        )
        tool = cursor.fetchone()
        if tool and count_view:
            cursor.execute("UPDATE security_tools SET view_count = view_count + 1 WHERE id = %s", (tool["id"],))
        return tool


def get_tool(tool_id: int):
    with marketplace_cursor() as cursor:
        cursor.execute("SELECT * FROM security_tools WHERE id = %s", (tool_id,))
        return cursor.fetchone()


def list_admin_tools(query="", status="", category=""):
    clauses, parameters = [], []
    if query:
        clauses.append("(name ILIKE %s OR slug ILIKE %s OR category ILIKE %s)")
        term = f"%{query[:120]}%"
        parameters.extend([term, term, term])
    if status in ADMIN_STATUSES:
        clauses.append("status = %s")
        parameters.append(status)
    if category:
        clauses.append("category = %s")
        parameters.append(category[:120])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM security_tools {where} "
            "ORDER BY is_pinned DESC, display_order ASC, updated_at DESC", parameters,
        )
        return cursor.fetchall()


def admin_categories():
    with marketplace_cursor() as cursor:
        cursor.execute("SELECT DISTINCT category FROM security_tools ORDER BY category")
        return [row["category"] for row in cursor.fetchall()]


def create_tool(data: dict, files: dict, admin_id: int):
    slug = unique_slug(data["name"])
    published = data["status"] == "published"
    with marketplace_cursor() as cursor:
        cursor.execute(
            """INSERT INTO security_tools (
                name, slug, thumbnail_path, banner_path, gallery_paths,
                short_description, full_description, version, category,
                price_cents, currency, license_name, operating_system, platform,
                tool_file_path, tool_file_name, tool_file_sha256,
                documentation_path, screenshot_paths, release_notes, status,
                is_featured, is_pinned, display_order, created_by, updated_by,
                published_at
            ) VALUES (
                %s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,
                CASE WHEN %s THEN NOW() ELSE NULL END
            ) RETURNING *""",
            (
                data["name"], slug, files["thumbnail"], files["banner"], json.dumps(files["gallery"]),
                data["short_description"], data["full_description"], data["version"], data["category"],
                data["price_cents"], data["currency"], data["license_name"], data["operating_system"], data["platform"],
                files["tool_file"], files["tool_file_name"], files["tool_file_sha256"], files["documentation"],
                json.dumps(files["screenshots"]), data["release_notes"], data["status"], data["is_featured"],
                data["is_pinned"], data["display_order"], admin_id, admin_id, published,
            ),
        )
        tool = cursor.fetchone()
        _event(cursor, tool["id"], admin_id, "created", f"Status: {data['status']}")
        return tool


def update_tool(tool_id: int, data: dict, files: dict, admin_id: int):
    current = get_tool(tool_id)
    if not current:
        return None
    slug = unique_slug(data["name"], tool_id)
    merged = {
        "thumbnail": files.get("thumbnail") or current["thumbnail_path"],
        "banner": files.get("banner") or current["banner_path"],
        "gallery": files.get("gallery") or current["gallery_paths"],
        "tool_file": files.get("tool_file") or current["tool_file_path"],
        "tool_file_name": files.get("tool_file_name") or current["tool_file_name"],
        "tool_file_sha256": files.get("tool_file_sha256") or current["tool_file_sha256"],
        "documentation": files.get("documentation") or current["documentation_path"],
        "screenshots": files.get("screenshots") or current["screenshot_paths"],
    }
    with marketplace_cursor() as cursor:
        cursor.execute(
            """UPDATE security_tools SET
                name=%s, slug=%s, thumbnail_path=%s, banner_path=%s, gallery_paths=%s::jsonb,
                short_description=%s, full_description=%s, version=%s, category=%s,
                price_cents=%s, currency=%s, license_name=%s, operating_system=%s, platform=%s,
                tool_file_path=%s, tool_file_name=%s, tool_file_sha256=%s,
                documentation_path=%s, screenshot_paths=%s::jsonb, release_notes=%s,
                status=%s, is_featured=%s, is_pinned=%s, display_order=%s,
                updated_by=%s, updated_at=NOW(),
                published_at=CASE WHEN %s='published' THEN COALESCE(published_at,NOW()) ELSE published_at END,
                deleted_at=CASE WHEN %s='deleted' THEN COALESCE(deleted_at,NOW()) ELSE NULL END
            WHERE id=%s RETURNING *""",
            (
                data["name"], slug, merged["thumbnail"], merged["banner"], json.dumps(list(merged["gallery"])),
                data["short_description"], data["full_description"], data["version"], data["category"],
                data["price_cents"], data["currency"], data["license_name"], data["operating_system"], data["platform"],
                merged["tool_file"], merged["tool_file_name"], merged["tool_file_sha256"], merged["documentation"],
                json.dumps(list(merged["screenshots"])), data["release_notes"], data["status"], data["is_featured"],
                data["is_pinned"], data["display_order"], admin_id, data["status"], data["status"], tool_id,
            ),
        )
        tool = cursor.fetchone()
        _event(cursor, tool_id, admin_id, "updated", f"Status: {data['status']}")
        return tool


def tool_action(tool_id: int, action: str, admin_id: int, display_order=None):
    actions = {
        "publish": ("status='published', deleted_at=NULL, published_at=COALESCE(published_at,NOW())", "published"),
        "unpublish": ("status='unpublished'", "unpublished"),
        "delete": ("status='deleted', deleted_at=NOW()", "deleted"),
        "restore": ("status='published', deleted_at=NULL, published_at=COALESCE(published_at,NOW())", "restored"),
        "archive": ("status='archived'", "archived"),
        "feature": ("is_featured=TRUE", "featured"),
        "unfeature": ("is_featured=FALSE", "unfeatured"),
        "pin": ("is_pinned=TRUE", "pinned"),
        "unpin": ("is_pinned=FALSE", "unpinned"),
    }
    if action == "order":
        if display_order is None:
            raise ValueError("Display order is required.")
        set_clause, event = "display_order=%s", "display_order_changed"
        parameters = [int(display_order)]
    elif action in actions:
        set_clause, event = actions[action]
        parameters = []
    else:
        raise ValueError("Unsupported marketplace action.")
    parameters.extend([admin_id, tool_id])
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"UPDATE security_tools SET {set_clause}, updated_by=%s, updated_at=NOW() WHERE id=%s RETURNING id",
            parameters,
        )
        result = cursor.fetchone()
        if result:
            _event(cursor, tool_id, admin_id, event)
        return bool(result)


def marketplace_counts():
    with marketplace_cursor() as cursor:
        cursor.execute("SELECT status, COUNT(*) AS total FROM security_tools GROUP BY status")
        counts = {status: 0 for status in ADMIN_STATUSES}
        counts.update({row["status"]: row["total"] for row in cursor.fetchall()})
        counts["total"] = sum(counts.values())
        return counts


def increment_download(tool_id: int):
    with marketplace_cursor() as cursor:
        cursor.execute("UPDATE security_tools SET download_count=download_count+1 WHERE id=%s", (tool_id,))


def _event(cursor, tool_id, admin_id, event_type, details=""):
    cursor.execute(
        "INSERT INTO security_tool_events (tool_id, admin_user_id, event_type, event_details) VALUES (%s,%s,%s,%s)",
        (tool_id, admin_id, event_type, details[:1000]),
    )
