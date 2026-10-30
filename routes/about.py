from flask import Blueprint, render_template


about_blueprint = Blueprint("about", __name__)


@about_blueprint.get("/about")
@about_blueprint.get("/about.html")
@about_blueprint.get("/templates/about.html")
def index():
    """Render the AlphaX ZeroTech founder profile page."""
    return render_template("about.html")
