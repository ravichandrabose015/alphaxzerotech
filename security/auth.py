from functools import wraps
import hashlib
import secrets
import time

from flask import flash, redirect, request, session, url_for

from database.admin_users import get_admin_by_id
from database.database import get_db

def open_session(admin_id):
    token = secrets.token_urlsafe(32)
    db = get_db()
    db.execute('DELETE FROM admin_sessions WHERE expires < ?', (time.time(),))
    db.execute('INSERT INTO admin_sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(),admin_id,time.time()+28800))
    db.commit()
    session['admin_token'] = token

def revoke_sessions(admin_id):
    db = get_db()
    db.execute('DELETE FROM admin_sessions WHERE admin_id=?',(admin_id,))
    db.commit()


def current_admin():
    admin_id = session.get("admin_user_id")
    token = session.get('admin_token','')
    if not admin_id or not token:
        return None
    row = get_db().execute('SELECT 1 FROM admin_sessions WHERE token_hash=? AND admin_id=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(),admin_id,time.time())).fetchone()
    if not row:
        return None
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
