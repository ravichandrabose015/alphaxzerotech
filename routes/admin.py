import csv
import io
import secrets

from flask import (
    Blueprint, Response, flash, redirect, render_template, request, session, url_for,
)

from database.activity_logs import recent_logs, write_log
from database.admin_users import (
    admin_count, authenticate_admin, create_admin, record_login, set_two_factor,
    update_password,
)
from database.enquiries import (
    enquiry_counts, get_enquiry, list_enquiries, recent_enquiries,
    soft_delete_enquiry, update_enquiry,
)
from database.website_content import all_content, update_content
from security.auth import admin_required, current_admin
from security.csrf import validate_csrf
from security.otp import generate_secret, provisioning_uri, verify_code
from security.rate_limit import rate_limit
from utils.validators import validate_password


admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")


def client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return forwarded or request.remote_addr or "Unknown"


def audit(action, entity_type="admin", entity_id=None, details=""):
    admin = current_admin()
    write_log(admin["id"] if admin else None, action, entity_type, entity_id, client_ip(), details)


@admin_blueprint.route("/setup", methods=["GET", "POST"])
@rate_limit(6, 300)
def setup():
    if admin_count() > 0:
        return redirect(url_for("admin.login"))
    errors = []
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirm_password", "")
        if len(username) < 4 or len(username) > 50:
            errors.append("Username must contain 4 to 50 characters.")
        errors.extend(validate_password(password))
        if password != confirmation:
            errors.append("Passwords do not match.")
        if not errors:
            admin_id = create_admin(username, password)
            write_log(admin_id, "admin_setup", "admin", str(admin_id), client_ip(), "Initial administrator created")
            flash("Administrator account created. Sign in to continue.", "success")
            return redirect(url_for("admin.login"))
    return render_template("admin/setup.html", errors=errors)


@admin_blueprint.route("/login", methods=["GET", "POST"])
@rate_limit(10, 300)
def login():
    if admin_count() == 0:
        return redirect(url_for("admin.setup"))
    if current_admin():
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        validate_csrf()
        admin = authenticate_admin(request.form.get("username", ""), request.form.get("password", ""))
        otp = request.form.get("otp", "").strip()
        if not admin or (admin["two_factor_enabled"] and not verify_code(admin["two_factor_secret"], otp)):
            write_log(admin["id"] if admin else None, "login_failed", "admin", None, client_ip(), "Invalid credentials or OTP")
            error = "Invalid username, password, or authentication code."
        else:
            session.clear()
            session["admin_user_id"] = admin["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = request.form.get("remember_me") == "1"
            record_login(admin["id"])
            audit("login_success", entity_id=str(admin["id"]))
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html", error=error)


@admin_blueprint.post("/logout")
@admin_required
def logout():
    validate_csrf()
    audit("logout")
    session.clear()
    return redirect(url_for("admin.login"))


@admin_blueprint.get("/")
@admin_blueprint.get("/dashboard")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html", counts=enquiry_counts(),
        enquiries=recent_enquiries(), logs=recent_logs(),
    )


@admin_blueprint.get("/enquiries")
@admin_required
def enquiries():
    query = request.args.get("q", "").strip()[:100]
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "newest")
    include_deleted = request.args.get("deleted") == "1"
    rows = list_enquiries(query, status, sort, include_deleted)
    return render_template(
        "admin/enquiries.html", enquiries=rows, counts=enquiry_counts(),
        query=query, selected_status=status, selected_sort=sort,
        include_deleted=include_deleted,
    )


@admin_blueprint.route("/enquiries/<enquiry_id>", methods=["GET", "POST"])
@admin_required
def enquiry_details(enquiry_id):
    enquiry = get_enquiry(enquiry_id)
    if enquiry is None:
        return render_template("404.html"), 404
    if request.method == "POST":
        validate_csrf()
        try:
            update_enquiry(enquiry_id, request.form.get("status", ""), request.form.get("admin_notes", "")[:5000])
        except ValueError as error:
            flash(str(error), "error")
        else:
            audit("enquiry_updated", "enquiry", enquiry_id, f"Status: {request.form.get('status')}")
            flash("Enquiry status and notes updated.", "success")
            return redirect(url_for("admin.enquiry_details", enquiry_id=enquiry_id))
    return render_template("admin/enquiry_details.html", enquiry=enquiry)


@admin_blueprint.post("/enquiries/<enquiry_id>/delete")
@admin_required
def delete_enquiry(enquiry_id):
    validate_csrf()
    soft_delete_enquiry(enquiry_id)
    audit("enquiry_deleted", "enquiry", enquiry_id, "Soft deleted")
    flash(f"Enquiry {enquiry_id} moved to Deleted.", "warning")
    return redirect(url_for("admin.enquiries"))


@admin_blueprint.get("/enquiries/export.csv")
@admin_required
def export_enquiries():
    rows = list_enquiries(request.args.get("q", ""), request.args.get("status", ""), "newest", request.args.get("deleted") == "1")
    output = io.StringIO()
    writer = csv.writer(output)
    columns = ["enquiry_id", "full_name", "company_name", "email_address", "phone_number", "country", "service_interested", "subject", "message", "preferred_contact_method", "preferred_contact_time", "visitor_ip_address", "submission_date_time", "browser_information", "operating_system", "device_type", "status", "admin_notes", "last_updated_time", "deleted_status"]
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row[column] for column in columns])
    audit("enquiries_exported", "enquiry", details=f"Rows: {len(rows)}")
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=alphax-enquiries.csv"})


@admin_blueprint.route("/website-management", methods=["GET", "POST"])
@admin_required
def website_management():
    if request.method == "POST":
        validate_csrf()
        content_id = request.form.get("content_id", type=int)
        update_content(content_id, request.form.get("content_value", ""), current_admin()["id"])
        audit("website_content_updated", "website_content", str(content_id))
        flash("Website content updated successfully.", "success")
        return redirect(url_for("admin.website_management"))
    return render_template("admin/website_management.html", content_rows=all_content())


@admin_blueprint.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    admin = current_admin()
    setup_secret = session.get("pending_2fa_secret")
    setup_uri = provisioning_uri(setup_secret, admin["username"]) if setup_secret else None
    if request.method == "POST":
        validate_csrf()
        action = request.form.get("action")
        if action == "password":
            errors = validate_password(request.form.get("new_password", ""))
            if request.form.get("new_password") != request.form.get("confirm_password"):
                errors.append("Passwords do not match.")
            if errors:
                for error in errors:
                    flash(error, "error")
            else:
                update_password(admin["id"], request.form["new_password"])
                audit("password_changed")
                flash("Password updated.", "success")
        elif action == "start_2fa":
            session["pending_2fa_secret"] = generate_secret()
            flash("Enter the secret into your authenticator, then verify a code.", "warning")
        elif action == "enable_2fa":
            secret = session.get("pending_2fa_secret", "")
            if secret and verify_code(secret, request.form.get("otp", "")):
                set_two_factor(admin["id"], secret, True)
                session.pop("pending_2fa_secret", None)
                audit("two_factor_enabled")
                flash("Two-factor authentication enabled.", "success")
            else:
                flash("Invalid authentication code.", "error")
        elif action == "disable_2fa":
            set_two_factor(admin["id"], None, False)
            audit("two_factor_disabled")
            flash("Two-factor authentication disabled.", "warning")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", admin=admin, setup_secret=setup_secret, setup_uri=setup_uri)
