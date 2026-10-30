from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g


class MarketplaceUnavailable(RuntimeError):
    pass


def _driver():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as error:
        raise MarketplaceUnavailable(
            "PostgreSQL driver is not installed. Run pip install -r requirements.txt."
        ) from error
    return psycopg, dict_row


def is_configured() -> bool:
    return bool(current_app.config.get("MARKETPLACE_DATABASE_URL"))


def get_marketplace_db():
    if not is_configured():
        raise MarketplaceUnavailable(
            "Set ALPHAX_POSTGRES_URL to enable the dynamic PostgreSQL content systems."
        )
    if "marketplace_connection" not in g:
        psycopg, dict_row = _driver()
        try:
            connection = psycopg.connect(
                current_app.config["MARKETPLACE_DATABASE_URL"],
                row_factory=dict_row,
                connect_timeout=5,
            )
        except Exception as error:
            raise MarketplaceUnavailable("Unable to connect to the marketplace PostgreSQL database.") from error
        g.marketplace_connection = connection
        _ensure_schema(connection)
    return g.marketplace_connection


def _ensure_schema(connection) -> None:
    if getattr(g, "marketplace_schema_ready", False):
        return
    schema_paths = (
        Path(__file__).with_name("postgresql_security_tools.sql"),
        Path(__file__).with_name("postgresql_content_hub.sql"),
    )
    try:
        with connection.cursor() as cursor:
            for schema_path in schema_paths:
                cursor.execute(schema_path.read_text(encoding="utf-8"))
        connection.commit()
        g.marketplace_schema_ready = True
    except Exception as error:
        connection.rollback()
        raise MarketplaceUnavailable("Unable to initialize the marketplace PostgreSQL schema.") from error


def close_marketplace_db(_exception=None) -> None:
    connection = g.pop("marketplace_connection", None)
    g.pop("marketplace_schema_ready", None)
    if connection is not None:
        connection.close()


@contextmanager
def marketplace_cursor():
    connection = get_marketplace_db()
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def init_app(application) -> None:
    application.teardown_appcontext(close_marketplace_db)
