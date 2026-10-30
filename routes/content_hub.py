from datetime import date

from flask import Blueprint, abort, redirect, render_template, request, send_file, url_for

from database.content_hub import (
    get_public_item, global_search, increment_download, list_public_items, public_taxonomy, related_items,
)
from database.marketplace_database import MarketplaceUnavailable
from services.content_storage import resolve_upload


content_hub_blueprint = Blueprint("content_hub", __name__)

MODULES = {
    "threat": {"title": "Threat Intelligence", "template": "threat_intelligence.html", "prefix": "threat-intelligence"},
    "resource": {"title": "Resources", "template": "resources.html", "prefix": "resources"},
    "training": {"title": "Training", "template": "training.html", "prefix": "training"},
}


def _collections(module, items):
    featured = [item for item in items if item["is_featured"]]
    popular = sorted(items, key=lambda item: (item["view_count"], item["download_count"]), reverse=True)
    if module == "threat":
        groups = [
            ("Critical Threats", [item for item in items if item["severity"] == "critical"]),
            ("High Severity", [item for item in items if item["severity"] == "high"]),
            ("Zero-Day", [item for item in items if "zero" in str((item["metadata"] or {}).get("threat_type", "")).lower()]),
            ("Recent CVEs", [item for item in items if (item["metadata"] or {}).get("cve_id")]),
            ("Featured Threats", featured), ("Trending Threats", popular),
        ]
    elif module == "resource":
        groups = [("Featured Resources", featured)]
        for label, value in (("Latest Blogs", "blog"), ("Whitepapers", "whitepaper"), ("Research Papers", "research paper"), ("Case Studies", "case study"), ("Security Guides", "security guide"), ("Documentation", "documentation"), ("Videos", "video")):
            groups.append((label, [item for item in items if str((item["metadata"] or {}).get("resource_type", "")).lower() == value]))
    else:
        groups = [
            ("Featured Courses", featured), ("Free Courses", [item for item in items if item["access_type"] == "free"]),
            ("Premium Courses", [item for item in items if item["access_type"] in {"premium", "paid"}]),
            ("Beginner", [item for item in items if item["difficulty"] == "beginner"]),
            ("Intermediate", [item for item in items if item["difficulty"] == "intermediate"]),
            ("Advanced", [item for item in items if item["difficulty"] in {"advanced", "expert"}]),
            ("Popular Courses", popular),
        ]
    return [(label, records[:3]) for label, records in groups if records]


def _page(module):
    query = request.args.get("q", "").strip()[:120]
    category = request.args.get("category", "").strip()[:120]
    tag = request.args.get("tag", "").strip()[:80]
    sort = request.args.get("sort", "latest")
    date_from = request.args.get("date_from", "").strip()
    try:
        date.fromisoformat(date_from) if date_from else None
    except ValueError:
        date_from = ""
    filters = {
        "severity": request.args.get("severity", "").strip().lower(),
        "difficulty": request.args.get("difficulty", "").strip().lower(),
        "access_type": request.args.get("access", "").strip().lower(),
        "featured": request.args.get("featured", "").strip(),
        "date_from": date_from,
        "cvss": request.args.get("cvss", "").strip(),
    }
    try:
        all_items = list_public_items(module, query, category, tag, sort, filters)
        categories, tags = public_taxonomy(module)
        database_ready = True
    except MarketplaceUnavailable:
        all_items, categories, tags, database_ready = [], [], [], False
    try:
        current_page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        current_page = 1
    per_page = 12
    total_pages = max(1, (len(all_items) + per_page - 1) // per_page)
    current_page = min(current_page, total_pages)
    items = all_items[(current_page - 1) * per_page:current_page * per_page]
    collections = _collections(module, all_items)
    return render_template(
        MODULES[module]["template"], module=module, module_title=MODULES[module]["title"], items=items,
        categories=categories, tags=tags, query=query, selected_category=category, selected_tag=tag,
        selected_sort=sort, filters=filters, database_ready=database_ready,
        current_page=current_page, total_pages=total_pages,
        collections=collections,
    )


@content_hub_blueprint.get("/templates/threat_intelligence.html")
@content_hub_blueprint.get("/threat_intelligence.html")
@content_hub_blueprint.get("/threat-intelligence")
def threats():
    return _page("threat")


@content_hub_blueprint.get("/templates/resources.html")
@content_hub_blueprint.get("/resources.html")
@content_hub_blueprint.get("/resources")
def resources():
    return _page("resource")


@content_hub_blueprint.get("/templates/training.html")
@content_hub_blueprint.get("/training.html")
@content_hub_blueprint.get("/training")
def training():
    return _page("training")


def _detail(module, slug):
    try:
        item = get_public_item(module, slug, count_view=True)
        related = related_items(item) if item else []
    except MarketplaceUnavailable:
        item, related = None, []
    if item is None:
        return render_template("404.html"), 404
    return render_template("content_detail.html", item=item, related=related, module_config=MODULES[module])


@content_hub_blueprint.get("/threat-intelligence/<slug>")
def threat_detail(slug):
    return _detail("threat", slug[:240])


@content_hub_blueprint.get("/resources/<slug>")
def resource_detail(slug):
    return _detail("resource", slug[:240])


@content_hub_blueprint.get("/training/<slug>")
def training_detail(slug):
    return _detail("training", slug[:240])


@content_hub_blueprint.get("/content/media/<path:relative_path>")
def media(relative_path):
    parts = relative_path.split("/")
    if len(parts) < 3 or parts[0] not in MODULES or parts[1] not in {"thumbnail", "banner", "gallery", "screenshots"}:
        abort(404)
    try:
        path = resolve_upload(relative_path)
    except FileNotFoundError:
        abort(404)
    if not path.is_file():
        abort(404)
    return send_file(path, conditional=True, max_age=3600)


@content_hub_blueprint.get("/<module>/<slug>/download/<asset_key>/<int:index>")
def download(module, slug, asset_key, index):
    if module not in MODULES:
        abort(404)
    try:
        item = get_public_item(module, slug)
    except MarketplaceUnavailable:
        item = None
    if not item:
        abort(404)
    if item["access_type"] in {"paid", "premium"} and item["price_cents"] > 0:
        return redirect(url_for("contact.index", content=item["title"], intent="purchase"))
    allowed = {
        "threat": {"report_pdf", "ioc_file"},
        "resource": {"resource_file", "supporting_files", "videos"},
        "training": {"course_notes", "assignments", "lab_files", "course_resources", "certificate_template"},
    }[module]
    if asset_key not in allowed:
        abort(404)
    value = (item["asset_paths"] or {}).get(asset_key)
    records = value if isinstance(value, list) else [value] if value else []
    if index >= len(records) or not records[index]:
        abort(404)
    record = records[index]
    relative_path = record.get("path") if isinstance(record, dict) else record
    try:
        path = resolve_upload(relative_path)
    except FileNotFoundError:
        abort(404)
    if not path.is_file():
        abort(404)
    increment_download(item["id"])
    return send_file(path, as_attachment=True, download_name=record.get("name") if isinstance(record, dict) else path.name)


@content_hub_blueprint.get("/content/<module>/<slug>/asset/<asset_key>/<int:index>")
def view_asset(module, slug, asset_key, index):
    if module not in MODULES:
        abort(404)
    try:
        item = get_public_item(module, slug)
    except MarketplaceUnavailable:
        item = None
    if not item:
        abort(404)
    allowed = {
        "threat": {"report_pdf", "screenshots"},
        "resource": {"resource_file", "supporting_files"},
        "training": {"videos", "course_notes"},
    }[module]
    if asset_key not in allowed:
        abort(404)
    value = (item["asset_paths"] or {}).get(asset_key)
    records = value if isinstance(value, list) else [value] if value else []
    if index >= len(records) or not records[index]:
        abort(404)
    record = records[index]
    relative_path = record.get("path") if isinstance(record, dict) else record
    try:
        path = resolve_upload(relative_path)
    except FileNotFoundError:
        abort(404)
    if not path.is_file():
        abort(404)
    return send_file(path, conditional=True, max_age=3600)


@content_hub_blueprint.get("/search")
def search():
    query = request.args.get("q", "").strip()[:120]
    module = request.args.get("module", "").strip()
    category = request.args.get("category", "").strip()[:120]
    tag = request.args.get("tag", "").strip()[:80]
    sort = request.args.get("sort", "latest")
    try:
        results = global_search(query, module, category, tag, sort) if query else {}
        database_ready = True
    except MarketplaceUnavailable:
        results, database_ready = {}, False
    return render_template(
        "content_search.html", results=results, query=query, selected_module=module,
        selected_category=category, selected_tag=tag, selected_sort=sort, database_ready=database_ready,
    )
