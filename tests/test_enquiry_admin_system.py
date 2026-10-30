import re
import sqlite3

from app import create_app


def csrf(html):
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def test_complete_enquiry_and_admin_workflow(tmp_path):
    database_path = tmp_path / "test.db"
    app = create_app({"TESTING": True, "DATABASE": str(database_path), "SECRET_KEY": "test-secret"})
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/services/").status_code == 200
    contact = client.get("/contact")
    assert contact.status_code == 200
    token = csrf(contact.get_data(as_text=True))
    response = client.post("/contact", data={
        "csrf_token": token, "website": "", "full_name": "Security Lead",
        "company_name": "Example Enterprise", "email_address": "lead@example.com",
        "phone_number": "+91 98765 43210", "country": "India",
        "service_interested": "Security Audit", "subject": "Security assessment",
        "message": "We need a comprehensive security assessment for our enterprise systems.",
        "preferred_contact_method": "Email", "preferred_contact_time": "Morning",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"submitted securely" in response.data

    setup = client.get("/admin/setup")
    response = client.post("/admin/setup", data={
        "csrf_token": csrf(setup.get_data(as_text=True)), "username": "alphaxadmin",
        "password": "StrongAdmin#2026", "confirm_password": "StrongAdmin#2026",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Administrator account created" in response.data

    login = client.get("/admin/login")
    response = client.post("/admin/login", data={
        "csrf_token": csrf(login.get_data(as_text=True)), "username": "alphaxadmin",
        "password": "StrongAdmin#2026", "otp": "", "remember_me": "1",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"System Overview" in response.data
    assert b"Security Lead" in response.data

    enquiries = client.get("/admin/enquiries")
    assert enquiries.status_code == 200
    assert b"Security Lead" in enquiries.data
    export = client.get("/admin/enquiries/export.csv")
    assert export.status_code == 200
    assert export.mimetype == "text/csv"

    with sqlite3.connect(database_path) as connection:
        row = connection.execute("SELECT visitor_ip_address, status FROM enquiries").fetchone()
        assert row[0] == "127.0.0.1"
        assert row[1] == "new"
