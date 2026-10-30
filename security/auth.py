from functools import wraps

from flask import flash, redirect, request, session, url_for

from database.admin_users import get_admin_by_id


def current_admin():
    admin_id = session.get("admin_user_id")
    return get_admin_by_id(admin_id) if admin_id else None


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_admin() is None:
            session.clear()
            flash("Please sign in to access the private administrator panel.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def super_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        admin = current_admin()
        if admin is None:
            session.clear()
            flash("Please sign in to access the private administrator panel.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        if admin["role"] != "super_admin":
            flash("Super Admin permission is required for dynamic content management.", "error")
            return redirect(url_for("admin.dashboard"))
        return view(*args, **kwargs)
    return wrapped


def init_app(application) -> None:
    application.jinja_env.globals["current_admin"] = current_admin
