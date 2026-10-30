from flask import Blueprint, render_template

from database.website_content import content_for_page


services_blueprint = Blueprint("services", __name__, url_prefix="/services")


@services_blueprint.get("/")
def index():
    """Render the AlphaX ZeroTech services page."""
    return render_template("services.html", content=content_for_page("services"))


@services_blueprint.get("/services.html")
@services_blueprint.get("/templates/services.html")
def index_file():
    return index()
