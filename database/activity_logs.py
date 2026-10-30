from datetime import datetime, timezone

from database.database import get_db


def write_log(admin_id, action, entity_type, entity_id, ip_address, details="") -> None:
    database = get_db()
    database.execute(
        """INSERT INTO activity_logs
        (admin_user_id, action, entity_type, entity_id, ip_address, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            admin_id, action, entity_type, entity_id, ip_address, details[:1000],
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ),
    )
    database.commit()


def recent_logs(limit=12):
    return get_db().execute(
        """SELECT activity_logs.*, admin_users.username
        FROM activity_logs LEFT JOIN admin_users
        ON activity_logs.admin_user_id = admin_users.id
        ORDER BY activity_logs.created_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
