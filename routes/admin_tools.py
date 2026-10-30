from flask import Blueprint, flash, redirect, render_template, request, url_for

from database.marketplace_database import MarketplaceUnavailable, is_configured
from database.security_tools import (
    admin_categories, create_tool, get_tool, list_admin_tools, marketplace_counts,
    tool_action, update_tool,
)
from routes.admin import audit
from security.auth import current_admin, super_admin_required
from security.csrf import validate_csrf
from services.tool_storage import save_multiple, save_upload
from utils.tool_validators import validate_tool_form


admin_tools_blueprint = Blueprint("admin_tools", __name__, url_prefix="/admin/security-tools")


def _save_form_files(creating=False):
    thumbnail = save_upload(request.files.get("thumbnail"), "thumbnail", required=creating)
    banner = save_upload(request.files.get("banner"), "banner", required=creating)
    tool_file = save_upload(request.files.get("tool_file"), "tool_file", required=creating)
    documentation = save_upload(request.files.get("documentation"), "documentation", required=creating)
    gallery = save_multiple(request.files.getlist("gallery_images"), "gallery", required=creating)
    screenshots = save_multiple(request.files.getlist("screenshots"), "screenshots", required=creating)
    return {
        "thumbnail": thumbnail["path"] if thumbnail else None,
        "banner": banner["path"] if banner else None,
        "gallery": gallery,
        "tool_file": tool_file["path"] if tool_file else None,
        "tool_file_name": tool_file["name"] if tool_file else None,
        "tool_file_sha256": tool_file["sha256"] if tool_file else None,
        "documentation": documentation["path"] if documentation else None,
        "screenshots": screenshots,
    }


@admin_tools_blueprint.get("/")
@super_admin_required
def index():
    query = request.args.get("q", "").strip()[:120]
    status = request.args.get("status", "").strip()[:20]
    category = request.args.get("category", "").strip()[:120]
    try:
        tools = list_admin_tools(query, status, category)
        categories = admin_categories()
        counts = marketplace_counts()
        database_ready = True
        error = None
    except MarketplaceUnavailable as exception:
        tools, categories, counts = [], [], {"total": 0, "published": 0, "draft": 0, "unpublished": 0, "archived": 0, "deleted": 0}
        database_ready = False
        error = str(exception)
    return render_template(
        "admin/tools/index.html", tools=tools, categories=categories, counts=counts,
        query=query, selected_status=status, selected_category=category,
        database_ready=database_ready, database_configured=is_configured(), error=error,
    )


@admin_tools_blueprint.route("/new", methods=["GET", "POST"])
@super_admin_required
def create():
    errors, values = [], {}
    try:
        marketplace_counts()
    except MarketplaceUnavailable as error:
        flash(str(error), "error")
        return redirect(url_for("admin_tools.index"))
    if request.method == "POST":
        validate_csrf()
        values, errors = validate_tool_form(request.form, creating=True)
        try:
            files = _save_form_files(creating=True)
        except ValueError as error:
            errors.append(str(error))
            files = None
        if not errors and files:
            try:
                tool = create_tool(values, files, current_admin()["id"])
            except MarketplaceUnavailable as error:
                errors.append(str(error))
            else:
                audit("security_tool_created", "security_tool", str(tool["id"]), tool["name"])
                flash(f"{tool['name']} created successfully.", "success")
                return redirect(url_for("admin_tools.index"))
    return render_template("admin/tools/form.html", tool=None, values=values, errors=errors, creating=True)


@admin_tools_blueprint.route("/<int:tool_id>/edit", methods=["GET", "POST"])
@super_admin_required
def edit(tool_id):
    try:
        tool = get_tool(tool_id)
    except MarketplaceUnavailable as error:
        flash(str(error), "error")
        return redirect(url_for("admin_tools.index"))
    if tool is None:
        return render_template("404.html"), 404
    errors, values = [], {}
    if request.method == "POST":
        validate_csrf()
        values, errors = validate_tool_form(request.form, creating=False)
        try:
            files = _save_form_files(creating=False)
        except ValueError as error:
            errors.append(str(error))
            files = None
        if not errors and files is not None:
            try:
                updated = update_tool(tool_id, values, files, current_admin()["id"])
            except MarketplaceUnavailable as error:
                errors.append(str(error))
            else:
                audit("security_tool_updated", "security_tool", str(tool_id), updated["name"])
                flash(f"{updated['name']} updated successfully.", "success")
                return redirect(url_for("admin_tools.index"))
    return render_template("admin/tools/form.html", tool=tool, values=values, errors=errors, creating=False)


@admin_tools_blueprint.post("/<int:tool_id>/action")
@super_admin_required
def action(tool_id):
    validate_csrf()
    action_name = request.form.get("action", "")
    try:
        changed = tool_action(
            tool_id, action_name, current_admin()["id"],
            request.form.get("display_order") if action_name == "order" else None,
        )
    except (MarketplaceUnavailable, ValueError) as error:
        flash(str(error), "error")
    else:
        if changed:
            audit(f"security_tool_{action_name}", "security_tool", str(tool_id))
            flash(f"Tool action '{action_name}' completed.", "success")
        else:
            flash("Security tool was not found.", "error")
    return redirect(url_for("admin_tools.index"))
