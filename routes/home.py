from flask import Blueprint, render_template

from database.website_content import content_for_page
from database.marketplace_database import MarketplaceUnavailable
from database.security_tools import homepage_groups
from database.content_hub import homepage_content


home_blueprint = Blueprint("home", __name__)


@home_blueprint.get("/")
def index():
    """Render the AlphaX ZeroTech home page."""
    try:
        tool_groups = homepage_groups()
        hub_groups = homepage_content()
        marketplace_ready = True
    except MarketplaceUnavailable:
        tool_groups = {"featured": [], "latest": [], "popular": []}
        hub_groups = {"threats": [], "featured_resources": [], "blogs": [], "whitepapers": [], "courses": [], "featured_courses": []}
        marketplace_ready = False
    return render_template(
        "index.html", content=content_for_page("home"),
        marketplace_groups=tool_groups, marketplace_ready=marketplace_ready,
        content_hub_groups=hub_groups,
    )


@home_blueprint.get("/index.html")
@home_blueprint.get("/templates/index.html")
def index_file():
    return index()


@home_blueprint.get("/templates/services.html")
def services_file():
    from routes.services import index as services_index
    return services_index()


@home_blueprint.get("/<path:page_name>.html")
def static_template_page(page_name):
    allowed = {"pricing"}
    if page_name not in allowed:
        return render_template("404.html"), 404
    return render_template(f"{page_name}.html")
