from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from database.database import get_db


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def admin_count() -> int:
    return get_db().execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]


def create_admin(username: str, password: str, role: str = "super_admin"):
    database = get_db()
    cursor = database.execute(
        "INSERT INTO admin_users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username.strip(), generate_password_hash(password, method="scrypt"), role, now()),
    )
    database.commit()
    return cursor.lastrowid


def get_admin_by_id(admin_id: int):
    return get_db().execute(
        "SELECT * FROM admin_users WHERE id = ? AND is_active = 1", (admin_id,)
    ).fetchone()


def authenticate_admin(username: str, password: str):
    admin = get_db().execute(
        "SELECT * FROM admin_users WHERE username = ? COLLATE NOCASE AND is_active = 1",
        (username.strip(),),
    ).fetchone()
    return admin if admin and check_password_hash(admin["password_hash"], password) else None


def record_login(admin_id: int) -> None:
    database = get_db()
    database.execute("UPDATE admin_users SET last_login_at = ? WHERE id = ?", (now(), admin_id))
    database.commit()


def update_password(admin_id: int, password: str) -> None:
    database = get_db()
    database.execute(
        "UPDATE admin_users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(password, method="scrypt"), admin_id),
    )
    database.commit()


def set_two_factor(admin_id: int, secret: str | None, enabled: bool) -> None:
    database = get_db()
    database.execute(
        "UPDATE admin_users SET two_factor_secret = ?, two_factor_enabled = ? WHERE id = ?",
        (secret, int(enabled), admin_id),
    )
    database.commit()
