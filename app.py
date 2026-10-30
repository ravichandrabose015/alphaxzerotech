from datetime import datetime

from flask import Flask, render_template

from config import Config
from database.database import init_app as init_database
from database.marketplace_database import init_app as init_marketplace_database
from database.website_content import seed_content
from routes.about import about_blueprint
from routes.admin import admin_blueprint
from routes.admin_tools import admin_tools_blueprint
from routes.admin_content import admin_content_blueprint
from routes.content_hub import content_hub_blueprint
from routes.contact import contact_blueprint
from routes.home import home_blueprint
from routes.security_tools import security_tools_blueprint
from routes.services import services_blueprint
from security.auth import init_app as init_auth
from security.csrf import init_app as init_csrf
from security.firewall import init_app as init_firewall


def create_app(test_config=None) -> Flask:
    """Create and configure the AlphaX ZeroTech application."""
    application = Flask(__name__)
    application.config.from_object(Config)
    if test_config:
        application.config.update(test_config)
    application.register_blueprint(home_blueprint)
    application.register_blueprint(about_blueprint)
    application.register_blueprint(services_blueprint)
    application.register_blueprint(contact_blueprint)
    application.register_blueprint(admin_blueprint)
    application.register_blueprint(admin_tools_blueprint)
    application.register_blueprint(admin_content_blueprint)
    application.register_blueprint(security_tools_blueprint)
    application.register_blueprint(content_hub_blueprint)
    init_database(application)
    init_marketplace_database(application)
    init_auth(application)
    init_csrf(application)
    init_firewall(application)
    with application.app_context():
        seed_content()
    application.jinja_env.globals["now_year"] = datetime.now().year

    @application.errorhandler(400)
    def bad_request(error):
        return render_template("500.html", error=error), 400

    @application.errorhandler(404)
    def not_found(error):
        return render_template("404.html", error=error), 404

    @application.errorhandler(429)
    def too_many_requests(error):
        return render_template("500.html", error=error), 429
    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
