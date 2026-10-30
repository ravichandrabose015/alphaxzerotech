from flask import (
    Blueprint, abort, current_app, redirect, render_template, request,
    send_file, url_for,
)

from database.marketplace_database import MarketplaceUnavailable
from database.security_tools import (
    get_public_tool, increment_download, list_public_tools, public_categories,
)
from services.tool_storage import resolve_upload


security_tools_blueprint = Blueprint("security_tools", __name__)


def _marketplace_data(query="", category="", sort="latest"):
    try:
        return list_public_tools(query, category, sort), public_categories(), True
    except MarketplaceUnavailable:
        return [], [], False


@security_tools_blueprint.get("/security-tools")
@security_tools_blueprint.get("/security_tools.html")
@security_tools_blueprint.get("/templates/security_tools.html")
def marketplace():
    query = request.args.get("q", "").strip()[:120]
    category = request.args.get("category", "").strip()[:120]
    sort = request.args.get("sort", "latest")
    tools, categories, database_ready = _marketplace_data(query, category, sort)
    return render_template(
        "security_tools.html", tools=tools, categories=categories,
        query=query, selected_category=category, selected_sort=sort,
        database_ready=database_ready,
    )


@security_tools_blueprint.get("/security-tools/<slug>")
def product(slug):
    try:
        tool = get_public_tool(slug[:220], count_view=True)
    except MarketplaceUnavailable:
        tool = None
    if tool is None:
        return render_template("404.html"), 404
    return render_template("security_tool_detail.html", tool=tool)


@security_tools_blueprint.get("/security-tools/<slug>/buy")
def buy(slug):
    try:
        tool = get_public_tool(slug[:220])
    except MarketplaceUnavailable:
        tool = None
    if tool is None:
        abort(404)
    if tool["price_cents"] == 0:
        return redirect(url_for("security_tools.download", slug=slug))
    return redirect(url_for("contact.index", tool=tool["name"], intent="purchase"))


@security_tools_blueprint.get("/security-tools/<slug>/download")
def download(slug):
    try:
        tool = get_public_tool(slug[:220])
    except MarketplaceUnavailable:
        tool = None
    if tool is None:
        abort(404)
    if tool["price_cents"] > 0:
        abort(403, description="Purchase verification is required before download.")
    try:
        file_path = resolve_upload(tool["tool_file_path"])
    except FileNotFoundError:
        abort(404)
    if not file_path.is_file():
        abort(404)
    increment_download(tool["id"])
    return send_file(file_path, as_attachment=True, download_name=tool["tool_file_name"])


@security_tools_blueprint.get("/marketplace/media/<path:relative_path>")
def media(relative_path):
    allowed_directories = {"thumbnail", "banner", "gallery", "screenshots", "documentation"}
    if relative_path.split("/", 1)[0] not in allowed_directories:
        abort(404)
    try:
        path = resolve_upload(relative_path)
    except FileNotFoundError:
        abort(404)
    if not path.is_file():
        abort(404)
    return send_file(path, conditional=True, max_age=3600)
