from database.security_tools import ADMIN_STATUSES, price_to_cents


def clean(value, limit):
    return (value or "").strip()[:limit]


def validate_tool_form(form, creating=True):
    data = {
        "name": clean(form.get("name"), 180),
        "short_description": clean(form.get("short_description"), 320),
        "full_description": clean(form.get("full_description"), 20000),
        "version": clean(form.get("version"), 80),
        "category": clean(form.get("category"), 120),
        "currency": clean(form.get("currency"), 3).upper() or "USD",
        "license_name": clean(form.get("license_name"), 160),
        "operating_system": clean(form.get("operating_system"), 180),
        "platform": clean(form.get("platform"), 180),
        "release_notes": clean(form.get("release_notes"), 10000),
        "status": clean(form.get("status"), 20) or "draft",
        "is_featured": form.get("is_featured") == "1",
        "is_pinned": form.get("is_pinned") == "1",
    }
    errors = []
    required = {
        "name": "Tool name", "short_description": "Short description",
        "full_description": "Full description", "version": "Version",
        "category": "Category", "license_name": "License",
        "operating_system": "Operating system", "platform": "Platform",
        "release_notes": "Release notes",
    }
    for key, label in required.items():
        if not data[key]:
            errors.append(f"{label} is required.")
    if data["status"] not in ADMIN_STATUSES - {"deleted"}:
        errors.append("Choose a valid tool status.")
    if len(data["currency"]) != 3 or not data["currency"].isalpha():
        errors.append("Currency must be a three-letter code.")
    try:
        data["price_cents"] = price_to_cents(form.get("price", "0"))
    except ValueError as error:
        errors.append(str(error))
        data["price_cents"] = 0
    try:
        data["display_order"] = int(form.get("display_order", "0"))
    except ValueError:
        errors.append("Display order must be a whole number.")
        data["display_order"] = 0
    if data["display_order"] < 0:
        errors.append("Display order cannot be negative.")
    return data, errors
