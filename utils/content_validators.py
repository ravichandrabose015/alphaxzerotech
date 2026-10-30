from datetime import datetime

from database.content_hub import MODULES, STATUSES, money_to_cents


MODULE_METADATA_FIELDS = {
    "threat": (
        "threat_type", "threat_level", "vendor", "affected_products", "affected_systems", "operating_system",
        "technical_analysis", "indicators_of_compromise", "cve_id", "cvss_score", "mitre_attack", "risk_impact",
        "mitigation_steps", "remediation_steps", "patch_information", "release_date", "source", "timeline",
        "references", "malware_sample_metadata", "detection_rules", "attack_vector", "vulnerability_type",
        "target_industries",
    ),
    "resource": (
        "resource_type", "summary", "topics_covered", "target_audience", "file_format", "file_size", "pages",
        "reading_time", "language", "access_level", "seo_title", "seo_description", "download_enabled",
    ),
    "training": (
        "instructor", "course_category", "duration", "level", "discount_price", "course_overview", "learning_objectives",
        "prerequisites", "syllabus", "modules", "lessons", "assignments", "labs", "certificate",
        "course_language", "total_videos", "total_hours", "course_access", "enrollment", "seo_title",
        "seo_description",
    ),
}


def clean(value, limit):
    return (value or "").strip()[:limit]


def validate_content_form(form, module):
    if module not in MODULES:
        return {}, ["Unsupported content module."]
    status = clean(form.get("status"), 20) or "draft"
    data = {
        "module": module,
        "title": clean(form.get("title"), 220),
        "short_description": clean(form.get("short_description"), 420),
        "full_description": clean(form.get("full_description"), 50000),
        "category": clean(form.get("category"), 120),
        "tags": [clean(tag, 80) for tag in (form.get("tags") or "").split(",") if clean(tag, 80)],
        "author_name": clean(form.get("author_name"), 180),
        "severity": clean(form.get("severity"), 24).lower(),
        "difficulty": clean(form.get("difficulty"), 24).lower(),
        "access_type": clean(form.get("access_type"), 24).lower() or "free",
        "currency": clean(form.get("currency"), 3).upper() or "USD",
        "version": clean(form.get("version"), 80),
        "status": status,
        "is_featured": form.get("is_featured") == "1",
        "is_pinned": form.get("is_pinned") == "1",
        "publish_at": clean(form.get("publish_at"), 32) or None,
        "metadata": {},
    }
    errors = []
    for key, label in (("title", "Title"), ("short_description", "Short description"), ("full_description", "Full description"), ("category", "Category")):
        if not data[key]:
            errors.append(f"{label} is required.")
    if status not in STATUSES - {"deleted"}:
        errors.append("Choose a valid publishing status.")
    if data["severity"] and data["severity"] not in {"critical", "high", "medium", "low", "informational"}:
        errors.append("Choose a valid severity.")
    if data["difficulty"] and data["difficulty"] not in {"beginner", "intermediate", "advanced", "expert"}:
        errors.append("Choose a valid difficulty level.")
    if data["access_type"] not in {"free", "premium", "paid"}:
        errors.append("Choose a valid access type.")
    if data["publish_at"]:
        try:
            datetime.fromisoformat(data["publish_at"])
        except ValueError:
            errors.append("Scheduled publish time is invalid.")
    if len(data["currency"]) != 3 or not data["currency"].isalpha():
        errors.append("Currency must be a three-letter code.")
    try:
        data["price_cents"] = money_to_cents(form.get("price", "0"))
    except ValueError as error:
        errors.append(str(error))
        data["price_cents"] = 0
    try:
        data["display_order"] = max(0, int(form.get("display_order", "0")))
    except ValueError:
        data["display_order"] = 0
        errors.append("Display order must be a whole number.")
    for field in MODULE_METADATA_FIELDS[module]:
        if field in {"download_enabled"}:
            data["metadata"][field] = form.get(field) == "1"
        else:
            data["metadata"][field] = clean(form.get(field), 30000)
    return data, errors
