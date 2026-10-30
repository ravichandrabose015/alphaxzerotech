import json
import re
from decimal import Decimal, InvalidOperation

from database.marketplace_database import marketplace_cursor


MODULES = {"threat", "resource", "training"}
STATUSES = {"draft", "published", "unpublished", "archived", "deleted"}


def _module(value: str) -> str:
    if value not in MODULES:
        raise ValueError("Unsupported content module.")
    return value


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug[:220] or "content"


def unique_slug(module: str, title: str, exclude_id=None) -> str:
    module = _module(module)
    base, candidate, suffix = slugify(title), slugify(title), 2
    with marketplace_cursor() as cursor:
        while True:
            cursor.execute(
                "SELECT 1 FROM content_items WHERE module=%s AND slug=%s "
                "AND (%s::bigint IS NULL OR id<>%s)",
                (module, candidate, exclude_id, exclude_id),
            )
            if cursor.fetchone() is None:
                return candidate
            candidate = f"{base[:208]}-{suffix}"
            suffix += 1


def money_to_cents(value: str) -> int:
    try:
        amount = Decimal((value or "0").strip())
    except InvalidOperation as error:
        raise ValueError("Price must be a valid number.") from error
    if amount < 0:
        raise ValueError("Price cannot be negative.")
    return int((amount * 100).quantize(Decimal("1")))


def _public_clause(module: str):
    return (
        "module=%s AND status='published' AND deleted_at IS NULL "
        "AND (publish_at IS NULL OR publish_at<=NOW())"
    ), [_module(module)]


def list_public_items(module, query="", category="", tag="", sort="latest", filters=None, limit=None):
    base, parameters = _public_clause(module)
    clauses = [base]
    if query:
        term = f"%{query[:120]}%"
        clauses.append("(title ILIKE %s OR short_description ILIKE %s OR full_description ILIKE %s OR category ILIKE %s OR author_name ILIKE %s OR metadata::text ILIKE %s OR array_to_string(tags,' ') ILIKE %s)")
        parameters.extend([term, term, term, term, term, term, term])
    if category:
        clauses.append("category=%s")
        parameters.append(category[:120])
    if tag:
        clauses.append("%s=ANY(tags)")
        parameters.append(tag[:80])
    for field, value in (filters or {}).items():
        if field in {"severity", "difficulty", "access_type"} and value:
            clauses.append(f"{field}=%s")
            parameters.append(value[:24])
        elif field == "featured" and value:
            clauses.append("is_featured=TRUE")
        elif field == "date_from" and value:
            clauses.append("published_at::date >= %s::date")
            parameters.append(value[:10])
        elif field == "cvss" and value:
            clauses.append("metadata->>'cvss_score'=%s")
            parameters.append(value[:12])
    order = {
        "popular": "is_pinned DESC, view_count DESC, download_count DESC, published_at DESC NULLS LAST",
        "title": "is_pinned DESC, title ASC",
        "oldest": "is_pinned DESC, published_at ASC NULLS LAST",
        "critical": "is_pinned DESC, CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, published_at DESC NULLS LAST",
    }.get(sort, "is_pinned DESC, display_order ASC, published_at DESC NULLS LAST, created_at DESC")
    limit_sql = " LIMIT %s" if limit else ""
    if limit:
        parameters.append(int(limit))
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM content_items WHERE {' AND '.join(clauses)} ORDER BY {order}{limit_sql}",
            parameters,
        )
        return cursor.fetchall()


def public_taxonomy(module):
    module = _module(module)
    with marketplace_cursor() as cursor:
        cursor.execute(
            "SELECT category, COUNT(*) AS item_count FROM content_items WHERE module=%s "
            "AND status='published' AND deleted_at IS NULL AND (publish_at IS NULL OR publish_at<=NOW()) "
            "GROUP BY category ORDER BY category", (module,),
        )
        categories = cursor.fetchall()
        cursor.execute(
            "SELECT expanded.tag, COUNT(*) AS item_count FROM content_items "
            "CROSS JOIN LATERAL unnest(tags) AS expanded(tag) WHERE module=%s "
            "AND status='published' AND deleted_at IS NULL AND (publish_at IS NULL OR publish_at<=NOW()) "
            "GROUP BY expanded.tag ORDER BY expanded.tag", (module,),
        )
        tags = cursor.fetchall()
    return categories, tags


def get_public_item(module, slug, count_view=False):
    clause, parameters = _public_clause(module)
    parameters.append(slug[:240])
    with marketplace_cursor() as cursor:
        cursor.execute(f"SELECT * FROM content_items WHERE {clause} AND slug=%s", parameters)
        item = cursor.fetchone()
        if item and count_view:
            cursor.execute("UPDATE content_items SET view_count=view_count+1 WHERE id=%s", (item["id"],))
        return item


def related_items(item, limit=3):
    with marketplace_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM content_items WHERE module=%s AND id<>%s AND category=%s "
            "AND status='published' AND deleted_at IS NULL AND (publish_at IS NULL OR publish_at<=NOW()) "
            "ORDER BY is_featured DESC, published_at DESC NULLS LAST LIMIT %s",
            (item["module"], item["id"], item["category"], limit),
        )
        return cursor.fetchall()


def homepage_content(limit=4):
    return {
        "threats": list_public_items("threat", sort="critical", limit=limit),
        "featured_resources": _metadata_group("resource", featured=True, limit=limit),
        "blogs": _metadata_group("resource", "blog", limit=limit),
        "whitepapers": _metadata_group("resource", "whitepaper", featured=True, limit=limit),
        "courses": list_public_items("training", sort="latest", limit=limit),
        "featured_courses": _metadata_group("training", featured=True, limit=limit),
    }


def _featured_training(limit):
    clause, parameters = _public_clause("training")
    parameters.append(limit)
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM content_items WHERE {clause} AND is_featured=TRUE "
            "ORDER BY is_pinned DESC, display_order ASC, published_at DESC NULLS LAST LIMIT %s", parameters,
        )
        return cursor.fetchall()


def _metadata_group(module, resource_type="", featured=False, limit=4):
    clause, parameters = _public_clause(module)
    additions = []
    if resource_type:
        additions.append("LOWER(metadata->>'resource_type')=%s")
        parameters.append(resource_type.lower())
    if featured:
        additions.append("is_featured=TRUE")
    parameters.append(limit)
    extra = " AND " + " AND ".join(additions) if additions else ""
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM content_items WHERE {clause}{extra} "
            "ORDER BY is_pinned DESC,display_order ASC,published_at DESC NULLS LAST LIMIT %s", parameters,
        )
        return cursor.fetchall()


def global_search(query, module="", category="", tag="", sort="latest"):
    modules = [_module(module)] if module in MODULES else ["threat", "resource", "training"]
    return {name: list_public_items(name, query, category, tag, sort) for name in modules}


def get_item(item_id):
    with marketplace_cursor() as cursor:
        cursor.execute("SELECT * FROM content_items WHERE id=%s", (item_id,))
        return cursor.fetchone()


def list_admin_items(module, query="", status="", category=""):
    module = _module(module)
    clauses, parameters = ["module=%s"], [module]
    if query:
        term = f"%{query[:120]}%"
        clauses.append("(title ILIKE %s OR slug ILIKE %s OR category ILIKE %s)")
        parameters.extend([term, term, term])
    if status in STATUSES:
        clauses.append("status=%s")
        parameters.append(status)
    if category:
        clauses.append("category=%s")
        parameters.append(category[:120])
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM content_items WHERE {' AND '.join(clauses)} "
            "ORDER BY is_pinned DESC, display_order ASC, updated_at DESC", parameters,
        )
        return cursor.fetchall()


def module_counts(module):
    module = _module(module)
    counts = {status: 0 for status in STATUSES}
    with marketplace_cursor() as cursor:
        cursor.execute("SELECT status, COUNT(*) AS total FROM content_items WHERE module=%s GROUP BY status", (module,))
        counts.update({row["status"]: row["total"] for row in cursor.fetchall()})
    counts["total"] = sum(counts.values())
    return counts


def admin_taxonomy(module):
    module = _module(module)
    with marketplace_cursor() as cursor:
        cursor.execute("SELECT * FROM content_categories WHERE module=%s ORDER BY name", (module,))
        categories = cursor.fetchall()
        cursor.execute("SELECT * FROM content_tags WHERE module=%s ORDER BY name", (module,))
        tags = cursor.fetchall()
    return categories, tags


def add_taxonomy(module, kind, name):
    module = _module(module)
    table = "content_categories" if kind == "category" else "content_tags" if kind == "tag" else None
    if not table:
        raise ValueError("Unsupported taxonomy type.")
    name = (name or "").strip()[:120 if kind == "category" else 80]
    if not name:
        raise ValueError("A name is required.")
    slug = slugify(name)[:140 if kind == "category" else 100]
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {table}(module,name,slug) VALUES(%s,%s,%s) "
            "ON CONFLICT(module,slug) DO UPDATE SET name=EXCLUDED.name RETURNING *",
            (module, name, slug),
        )
        return cursor.fetchone()


def delete_taxonomy(module, kind, taxonomy_id):
    module = _module(module)
    table = "content_categories" if kind == "category" else "content_tags" if kind == "tag" else None
    if not table:
        raise ValueError("Unsupported taxonomy type.")
    with marketplace_cursor() as cursor:
        cursor.execute(f"DELETE FROM {table} WHERE id=%s AND module=%s RETURNING id", (taxonomy_id, module))
        return bool(cursor.fetchone())


def create_item(data, assets, admin_id):
    module = _module(data["module"])
    slug = unique_slug(module, data["title"])
    with marketplace_cursor() as cursor:
        cursor.execute(
            """INSERT INTO content_items(
                module,title,slug,short_description,full_description,category,tags,author_name,
                severity,difficulty,access_type,price_cents,currency,version,thumbnail_path,banner_path,
                asset_paths,metadata,status,is_featured,is_pinned,display_order,publish_at,published_at,
                created_by,updated_by
            ) VALUES(
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,
                CASE WHEN %s='published' AND (%s::timestamptz IS NULL OR %s::timestamptz<=NOW()) THEN NOW() ELSE NULL END,
                %s,%s
            ) RETURNING *""",
            (
                module,data["title"],slug,data["short_description"],data["full_description"],data["category"],
                data["tags"],data["author_name"],data["severity"],data["difficulty"],data["access_type"],
                data["price_cents"],data["currency"],data["version"],assets.get("thumbnail"),assets.get("banner"),
                json.dumps(assets),json.dumps(data["metadata"]),data["status"],data["is_featured"],data["is_pinned"],
                data["display_order"],data["publish_at"],data["status"],data["publish_at"],data["publish_at"],
                admin_id,admin_id,
            ),
        )
        item = cursor.fetchone()
        _event(cursor, item["id"], admin_id, "created", data["status"])
        return item


def update_item(item_id, data, assets, admin_id):
    current = get_item(item_id)
    if not current or current["module"] != data["module"]:
        return None
    slug = unique_slug(data["module"], data["title"], item_id)
    merged_assets = dict(current["asset_paths"] or {})
    for key, value in assets.items():
        if value:
            merged_assets[key] = value
    thumbnail = assets.get("thumbnail") or current["thumbnail_path"]
    banner = assets.get("banner") or current["banner_path"]
    with marketplace_cursor() as cursor:
        cursor.execute(
            """UPDATE content_items SET
                title=%s,slug=%s,short_description=%s,full_description=%s,category=%s,tags=%s,
                author_name=%s,severity=%s,difficulty=%s,access_type=%s,price_cents=%s,currency=%s,
                version=%s,thumbnail_path=%s,banner_path=%s,asset_paths=%s::jsonb,metadata=%s::jsonb,
                status=%s,is_featured=%s,is_pinned=%s,display_order=%s,publish_at=%s,
                published_at=CASE WHEN %s='published' AND (%s::timestamptz IS NULL OR %s::timestamptz<=NOW())
                    THEN COALESCE(published_at,NOW()) ELSE published_at END,
                deleted_at=CASE WHEN %s='deleted' THEN COALESCE(deleted_at,NOW()) ELSE NULL END,
                updated_by=%s,updated_at=NOW()
            WHERE id=%s RETURNING *""",
            (
                data["title"],slug,data["short_description"],data["full_description"],data["category"],data["tags"],
                data["author_name"],data["severity"],data["difficulty"],data["access_type"],data["price_cents"],
                data["currency"],data["version"],thumbnail,banner,json.dumps(merged_assets),json.dumps(data["metadata"]),
                data["status"],data["is_featured"],data["is_pinned"],data["display_order"],data["publish_at"],
                data["status"],data["publish_at"],data["publish_at"],data["status"],admin_id,item_id,
            ),
        )
        item = cursor.fetchone()
        _event(cursor, item_id, admin_id, "updated", data["status"])
        return item


def content_action(item_id, action, admin_id, display_order=None):
    actions = {
        "publish": ("status='published',deleted_at=NULL,published_at=CASE WHEN publish_at IS NULL OR publish_at<=NOW() THEN COALESCE(published_at,NOW()) ELSE published_at END", "published"),
        "unpublish": ("status='unpublished'", "unpublished"),
        "delete": ("status='deleted',deleted_at=NOW()", "deleted"),
        "restore": ("status='published',deleted_at=NULL,published_at=COALESCE(published_at,NOW())", "restored"),
        "archive": ("status='archived'", "archived"),
        "feature": ("is_featured=TRUE", "featured"),
        "unfeature": ("is_featured=FALSE", "unfeatured"),
        "pin": ("is_pinned=TRUE", "pinned"),
        "unpin": ("is_pinned=FALSE", "unpinned"),
    }
    if action == "order":
        if display_order is None:
            raise ValueError("Display order is required.")
        clause, event, parameters = "display_order=%s", "display_order_changed", [int(display_order)]
    elif action in actions:
        clause, event = actions[action]
        parameters = []
    else:
        raise ValueError("Unsupported content action.")
    parameters.extend([admin_id, item_id])
    with marketplace_cursor() as cursor:
        cursor.execute(
            f"UPDATE content_items SET {clause},updated_by=%s,updated_at=NOW() WHERE id=%s RETURNING id", parameters,
        )
        result = cursor.fetchone()
        if result:
            _event(cursor, item_id, admin_id, event)
        return bool(result)


def increment_download(item_id):
    with marketplace_cursor() as cursor:
        cursor.execute("UPDATE content_items SET download_count=download_count+1 WHERE id=%s", (item_id,))


def _event(cursor, item_id, admin_id, event_type, details=""):
    cursor.execute(
        "INSERT INTO content_events(content_id,admin_user_id,event_type,event_details) VALUES(%s,%s,%s,%s)",
        (item_id, admin_id, event_type, (details or "")[:1000]),
    )
