from flask import Blueprint, render_template

from database.website_content import content_for_page
from database.marketplace_database import MarketplaceUnavailable
from database.security_tools import homepage_groups
from database.content_hub import homepage_content


home_blueprint = Blueprint("home", __name__)


@home_blueprint.get("/")
def index():
    """Render the AlphaX ZeroTech home page."""
    from routes.studio import context
    return render_template("studio/home.html", **context())



@home_blueprint.get("/index.html")
@home_blueprint.get("/templates/index.html")
def index_file():
    return index()


@home_blueprint.get("/templates/services.html")
def services_file():
    from routes.services import index as services_index
    return services_index()
