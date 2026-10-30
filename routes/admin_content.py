from flask import Blueprint, flash, redirect, render_template, request, url_for

from database.content_hub import (
    add_taxonomy, admin_taxonomy, content_action, create_item, delete_taxonomy, get_item,
    list_admin_items, module_counts, update_item,
)
from database.marketplace_database import MarketplaceUnavailable, is_configured
from routes.admin import audit
from security.auth import current_admin, super_admin_required
from security.csrf import validate_csrf
from services.content_storage import save_multiple, save_upload
from utils.content_validators import MODULE_METADATA_FIELDS, validate_content_form


admin_content_blueprint = Blueprint("admin_content", __name__, url_prefix="/admin/content")

MODULE_LABELS = {
    "threat": "Threat Intelligence",
    "resource": "Resources",
    "training": "Training",
}

FILE_FIELDS = {
    "threat": {"single": ("report_pdf", "ioc_file"), "multiple": ("screenshots",)},
    "resource": {"single": ("resource_file",), "multiple": ("supporting_files", "videos")},
    "training": {"single": ("certificate_template",), "multiple": ("videos", "course_notes", "assignments", "lab_files", "course_resources")},
}


def _valid_module(module):
    if module not in MODULE_LABELS:
        return None
    return module


def _save_files(module):
    assets = {}
    for kind in ("thumbnail", "banner"):
        saved = save_upload(request.files.get(kind), module, kind)
        if saved:
            assets[kind] = saved["path"]
            assets[f"{kind}_meta"] = saved
    gallery = save_multiple(request.files.getlist("gallery"), module, "gallery")
    if gallery:
        assets["gallery"] = gallery
    for kind in FILE_FIELDS[module]["single"]:
        saved = save_upload(request.files.get(kind), module, kind)
        if saved:
            assets[kind] = saved
    for kind in FILE_FIELDS[module]["multiple"]:
        saved = save_multiple(request.files.getlist(kind), module, kind)
        if saved:
            assets[kind] = saved
    return assets


@admin_content_blueprint.get("/<module>/")
@super_admin_required
def index(module):
    if not _valid_module(module):
        return render_template("404.html"), 404
    query = request.args.get("q", "").strip()[:120]
    status = request.args.get("status", "").strip()[:20]
    category = request.args.get("category", "").strip()[:120]
    try:
        items = list_admin_items(module, query, status, category)
        counts = module_counts(module)
        categories, tags = admin_taxonomy(module)
        database_ready, error = True, None
    except MarketplaceUnavailable as exception:
        items, categories, tags = [], [], []
        counts = {"total": 0, "published": 0, "draft": 0, "unpublished": 0, "archived": 0, "deleted": 0}
        database_ready, error = False, str(exception)
    return render_template(
        "admin/content/index.html", module=module, module_label=MODULE_LABELS[module], items=items,
        counts=counts, categories=categories, tags=tags, query=query, selected_status=status,
        selected_category=category, database_ready=database_ready, database_configured=is_configured(), error=error,
    )


@admin_content_blueprint.route("/<module>/new", methods=["GET", "POST"])
@super_admin_required
def create(module):
    if not _valid_module(module):
        return render_template("404.html"), 404
    values, errors = {}, []
    try:
        categories, tags = admin_taxonomy(module)
    except MarketplaceUnavailable as error:
        flash(str(error), "error")
        return redirect(url_for("admin_content.index", module=module))
    if request.method == "POST":
        validate_csrf()
        values, errors = validate_content_form(request.form, module)
        assets = None
        if not errors:
            try:
                assets = _save_files(module)
            except ValueError as error:
                errors.append(str(error))
        if not errors and assets is not None:
            try:
                item = create_item(values, assets, current_admin()["id"])
            except MarketplaceUnavailable as error:
                errors.append(str(error))
            else:
                audit("content_created", module, str(item["id"]), item["title"])
                flash(f"{item['title']} created successfully.", "success")
                return redirect(url_for("admin_content.index", module=module))
    return render_template(
        "admin/content/form.html", module=module, module_label=MODULE_LABELS[module], item=None,
        values=values, errors=errors, creating=True, categories=categories, tags=tags,
        metadata_fields=MODULE_METADATA_FIELDS[module], file_fields=FILE_FIELDS[module],
    )


@admin_content_blueprint.route("/<module>/<int:item_id>/edit", methods=["GET", "POST"])
@super_admin_required
def edit(module, item_id):
    if not _valid_module(module):
        return render_template("404.html"), 404
    try:
        item = get_item(item_id)
        categories, tags = admin_taxonomy(module)
    except MarketplaceUnavailable as error:
        flash(str(error), "error")
        return redirect(url_for("admin_content.index", module=module))
    if not item or item["module"] != module:
        return render_template("404.html"), 404
    values, errors = {}, []
    if request.method == "POST":
        validate_csrf()
        values, errors = validate_content_form(request.form, module)
        assets = None
        if not errors:
            try:
                assets = _save_files(module)
            except ValueError as error:
                errors.append(str(error))
        if not errors and assets is not None:
            try:
                item = update_item(item_id, values, assets, current_admin()["id"])
            except MarketplaceUnavailable as error:
                errors.append(str(error))
            else:
                audit("content_updated", module, str(item_id), item["title"])
                flash(f"{item['title']} updated successfully.", "success")
                return redirect(url_for("admin_content.index", module=module))
    return render_template(
        "admin/content/form.html", module=module, module_label=MODULE_LABELS[module], item=item,
        values=values, errors=errors, creating=False, categories=categories, tags=tags,
        metadata_fields=MODULE_METADATA_FIELDS[module], file_fields=FILE_FIELDS[module],
    )


@admin_content_blueprint.post("/<module>/<int:item_id>/action")
@super_admin_required
def action(module, item_id):
    if not _valid_module(module):
        return render_template("404.html"), 404
    validate_csrf()
    action_name = request.form.get("action", "")
    try:
        changed = content_action(
            item_id, action_name, current_admin()["id"],
            request.form.get("display_order") if action_name == "order" else None,
        )
    except (MarketplaceUnavailable, ValueError) as error:
        flash(str(error), "error")
    else:
        if changed:
            audit(f"content_{action_name}", module, str(item_id))
            flash(f"Content action '{action_name}' completed.", "success")
        else:
            flash("Content record was not found.", "error")
    return redirect(url_for("admin_content.index", module=module))


@admin_content_blueprint.post("/<module>/taxonomy")
@super_admin_required
def taxonomy_add(module):
    if not _valid_module(module):
        return render_template("404.html"), 404
    validate_csrf()
    kind = request.form.get("kind", "")
    try:
        value = add_taxonomy(module, kind, request.form.get("name", ""))
    except (MarketplaceUnavailable, ValueError) as error:
        flash(str(error), "error")
    else:
        audit("taxonomy_created", module, str(value["id"]), f"{kind}: {value['name']}")
        flash(f"{kind.title()} saved.", "success")
    return redirect(url_for("admin_content.index", module=module))


@admin_content_blueprint.post("/<module>/taxonomy/<kind>/<int:taxonomy_id>/delete")
@super_admin_required
def taxonomy_delete(module, kind, taxonomy_id):
    if not _valid_module(module):
        return render_template("404.html"), 404
    validate_csrf()
    try:
        deleted = delete_taxonomy(module, kind, taxonomy_id)
    except (MarketplaceUnavailable, ValueError) as error:
        flash(str(error), "error")
    else:
        if deleted:
            audit("taxonomy_deleted", module, str(taxonomy_id), kind)
            flash(f"{kind.title()} removed.", "success")
    return redirect(url_for("admin_content.index", module=module))
