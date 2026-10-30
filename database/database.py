import sqlite3
from pathlib import Path

from flask import current_app, g

from database.schema import SCHEMA


def get_db() -> sqlite3.Connection:
    if "database_connection" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        g.database_connection = connection
    return g.database_connection


def close_db(_exception=None) -> None:
    connection = g.pop("database_connection", None)
    if connection is not None:
        connection.close()


def init_database() -> None:
    database = get_db()
    database.executescript(SCHEMA)
    database.execute(
        """UPDATE admin_users SET role = 'super_admin'
        WHERE id = (SELECT MIN(id) FROM admin_users)
        AND NOT EXISTS (SELECT 1 FROM admin_users WHERE role = 'super_admin')"""
    )
    database.commit()


def init_app(application) -> None:
    application.teardown_appcontext(close_db)
    with application.app_context():
        init_database()
