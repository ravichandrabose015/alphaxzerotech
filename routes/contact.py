import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from database.enquiries import create_enquiry
from database.website_content import content_for_page
from security.csrf import validate_csrf
from security.rate_limit import rate_limit
from utils.validators import CONTACT_METHODS, CONTACT_TIMES, SERVICES, validate_enquiry


contact_blueprint = Blueprint("contact", __name__)


def _client_information() -> dict:
    agent = request.user_agent.string or "Unknown"
    lowered = agent.lower()
    if "windows" in lowered:
        operating_system = "Windows"
    elif "android" in lowered:
        operating_system = "Android"
    elif "iphone" in lowered or "ipad" in lowered:
        operating_system = "iOS"
    elif "mac os" in lowered or "macintosh" in lowered:
        operating_system = "macOS"
    elif "linux" in lowered:
        operating_system = "Linux"
    else:
        operating_system = "Unknown"
    if "edg/" in lowered:
        browser = "Microsoft Edge"
    elif "chrome/" in lowered:
        browser = "Google Chrome"
    elif "firefox/" in lowered:
        browser = "Mozilla Firefox"
    elif "safari/" in lowered:
        browser = "Apple Safari"
    else:
        browser = "Other Browser"
    device = "Mobile" if re.search(r"mobile|android|iphone", lowered) else "Tablet" if "ipad" in lowered else "Desktop"
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return {"ip": forwarded or request.remote_addr or "Unknown", "browser": browser, "os": operating_system, "device": device}


@contact_blueprint.route("/contact", methods=["GET", "POST"])
@contact_blueprint.route("/contact.html", methods=["GET", "POST"])
@contact_blueprint.route("/templates/contact.html", methods=["GET", "POST"])
@rate_limit(8, 60)
def index():
    errors = {}
    values = {}
    tool_name = request.args.get("tool", "").strip()[:180]
    if request.method == "GET" and tool_name:
        values = {
            "service_interested": "Other",
            "subject": f"Tool purchase request: {tool_name}",
            "message": f"I would like to purchase {tool_name}. Please share the secure payment and download process.",
        }
    if request.method == "POST":
        validate_csrf()
        if request.form.get("website"):
            return redirect(url_for("contact.index"))
        values, errors = validate_enquiry(request.form)
        if not errors:
            enquiry_id = create_enquiry(values, _client_information())
            flash(f"Your enquiry {enquiry_id} was submitted securely. Our team will contact you soon.", "success")
            return redirect(url_for("contact.index"))
    return render_template(
        "contact.html", errors=errors, values=values,
        services=sorted(SERVICES), contact_methods=sorted(CONTACT_METHODS),
        contact_times=sorted(CONTACT_TIMES), content=content_for_page("contact"),
    )
