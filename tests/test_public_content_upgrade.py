from pathlib import Path

from app import create_app
from database.catalog_seed import _seed_content, _seed_tools
from routes import content_hub


PUBLIC_PAGES = (
    "/",
    "/security-tools",
    "/courses",
    "/threat-intelligence",
    "/research",
    "/blog",
    "/case-studies",
    "/news",
    "/downloads",
    "/about",
    "/contact",
)


def test_public_pages_render():
    application = create_app({"TESTING": True})
    client = application.test_client()

    for path in PUBLIC_PAGES:
        assert client.get(path).status_code == 200, path


def test_generated_awareness_pdf_can_be_downloaded(monkeypatch):
    application = create_app({"TESTING": True})
    filename = "phishing-identification-checklist.pdf"
    item = {
        "id": 1,
        "title": "Phishing Identification Checklist",
        "access_type": "free",
        "price_cents": 0,
        "asset_paths": {
            "resource_file": {
                "path": f"/static/downloads/{filename}",
                "name": filename,
            }
        },
    }
    monkeypatch.setattr(content_hub, "get_public_item", lambda module, slug: item)
    monkeypatch.setattr(content_hub, "increment_download", lambda item_id: None)

    response = application.test_client().get(
        "/resource/phishing-identification-checklist/download/resource_file/0"
    )

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert filename in response.headers["Content-Disposition"]


def test_static_download_resolver_stays_inside_downloads():
    application = create_app({"TESTING": True})
    with application.app_context():
        resolved = content_hub._resolve_content_path(
            "/static/downloads/password-mfa-security-guide.pdf"
        )
        assert resolved.is_file()
        assert Path(application.static_folder).resolve() in resolved.parents


def test_starter_catalog_sql_parameter_counts_match():
    class CountingCursor:
        def execute(self, query, params):
            assert query.count("%s") == len(params)

    cursor = CountingCursor()
    _seed_tools(cursor)
    _seed_content(cursor)
