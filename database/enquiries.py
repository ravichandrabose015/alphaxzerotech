from datetime import datetime, timezone
from secrets import token_hex

from database.database import get_db


ALLOWED_STATUSES = {"new", "contacted", "pending", "in_progress", "closed", "deleted"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_enquiry(data: dict, client: dict) -> str:
    created_at = utc_now()
    enquiry_id = f"AXZ-{datetime.now(timezone.utc):%Y%m%d}-{token_hex(3).upper()}"
    database = get_db()
    database.execute(
        """
        INSERT INTO enquiries (
            enquiry_id, full_name, company_name, email_address, phone_number,
            country, service_interested, subject, message,
            preferred_contact_method, preferred_contact_time,
            visitor_ip_address, submission_date_time, browser_information,
            operating_system, device_type, status, last_updated_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
        """,
        (
            enquiry_id, data["full_name"], data.get("company_name", ""),
            data["email_address"], data["phone_number"], data["country"],
            data["service_interested"], data["subject"], data["message"],
            data["preferred_contact_method"], data["preferred_contact_time"],
            client["ip"], created_at, client["browser"], client["os"],
            client["device"], created_at,
        ),
    )
    database.commit()
    return enquiry_id


def enquiry_counts() -> dict:
    database = get_db()
    rows = database.execute(
        "SELECT status, COUNT(*) AS total FROM enquiries GROUP BY status"
    ).fetchall()
    counts = {status: 0 for status in ALLOWED_STATUSES}
    counts.update({row["status"]: row["total"] for row in rows})
    counts["total"] = database.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]
    counts["active"] = counts["total"] - counts["deleted"]
    counts["visitors"] = database.execute(
        "SELECT COUNT(DISTINCT visitor_ip_address) FROM enquiries"
    ).fetchone()[0]
    return counts


def list_enquiries(query="", status="", sort="newest", include_deleted=False):
    clauses = []
    parameters = []
    if not include_deleted:
        clauses.append("deleted_status = 0")
    if status in ALLOWED_STATUSES:
        clauses.append("status = ?")
        parameters.append(status)
    if query:
        clauses.append(
            "(enquiry_id LIKE ? OR full_name LIKE ? OR email_address LIKE ? "
            "OR service_interested LIKE ? OR subject LIKE ?)"
        )
        term = f"%{query}%"
        parameters.extend([term] * 5)
    order_by = {
        "oldest": "submission_date_time ASC",
        "name": "full_name COLLATE NOCASE ASC",
        "status": "status ASC, submission_date_time DESC",
    }.get(sort, "submission_date_time DESC")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return get_db().execute(
        f"SELECT * FROM enquiries {where} ORDER BY {order_by}", parameters
    ).fetchall()


def recent_enquiries(limit=6):
    return get_db().execute(
        "SELECT * FROM enquiries WHERE deleted_status = 0 "
        "ORDER BY submission_date_time DESC LIMIT ?", (limit,)
    ).fetchall()


def get_enquiry(enquiry_id: str):
    return get_db().execute(
        "SELECT * FROM enquiries WHERE enquiry_id = ?", (enquiry_id,)
    ).fetchone()


def update_enquiry(enquiry_id: str, status: str, notes: str) -> None:
    if status not in ALLOWED_STATUSES - {"deleted"}:
        raise ValueError("Invalid enquiry status")
    database = get_db()
    database.execute(
        "UPDATE enquiries SET status = ?, admin_notes = ?, "
        "last_updated_time = ? WHERE enquiry_id = ? AND deleted_status = 0",
        (status, notes, utc_now(), enquiry_id),
    )
    database.commit()


def soft_delete_enquiry(enquiry_id: str) -> None:
    database = get_db()
    database.execute(
        "UPDATE enquiries SET status = 'deleted', deleted_status = 1, "
        "last_updated_time = ? WHERE enquiry_id = ?",
        (utc_now(), enquiry_id),
    )
    database.commit()
