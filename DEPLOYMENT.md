# AlphaX ZeroTech publishing release

This release retains Flask, the existing enquiry/admin database, and the existing PostgreSQL marketplace. New public pages and Publishing Studio use the existing SQLite connection. Do not replace the existing production database with a preview database.

## Local development

Install `requirements.txt` in a Python 3.12 virtual environment. Set ALPHAX_DATABASE to a development database path and ALPHAX_SECRET_KEY to a generated local secret. Run `python -m flask --app app run`. Public home: `/`; editor: `/admin/studio`.

For a fresh installation, set ALPHAX_SETUP_TOKEN to a random secret generated on the server. Open `/admin/setup` and enter that installation token and your own administrator credentials. Existing administrators remain in the database. Enable authenticator MFA under Settings. Remove ALPHAX_SETUP_TOKEN after setup. No default admin password is shipped.

## Existing Render service

1. Back up the existing SQLite database using SQLite's backup API and back up uploads. Record the current deployed commit and environment. Rehearse restoring the backup before release.
2. Attach a persistent disk and copy the existing database to `/var/data/alphax.db` using a consistent SQLite backup. Copy existing uploads into the appropriate directories. Do not point at an empty database if this is an existing service.
3. Configure ALPHAX_DATABASE, ALPHAX_SECRET_KEY (retain the existing production secret), ALPHAX_HTTPS=1, ALPHAX_TOOL_UPLOAD_ROOT and ALPHAX_CONTENT_UPLOAD_ROOT. Keep ALPHAX_POSTGRES_URL configured for the original marketplace/content tools. New studio pages do not require PostgreSQL.
4. Use `pip install -r requirements.txt` and `gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT app:app`. Health endpoint: `/healthz`.
5. Verify login/MFA, draft privacy, contact submission, image upload, publish and hide on staging. Enable production from the reviewed commit after the backup and configuration are verified.
6. Review news drafts and publish verified entries. `python scripts/import_news.py` imports the latest seven days from CISA. Source failures do not replace current content; deleted imports are not resurrected. Scheduling requires a job with access to the same database/disk; a separate Render cron service cannot assume this disk is shared.

`render.yaml` is a blueprint for a NEW installation. Do not apply it blindly to an existing paid service: confirm service identity, persistent disk and migration first. Render hosting/billing and login access must be available before a live rollout can be completed.

## Rollback and security boundaries

Database changes are additive. Roll back application code to the previous deployed commit if necessary; preserve database/uploads. The first administrator stays super_admin. The studio requires super_admin, CSRF tokens, optimistic revision checks, and server-side sessions. Logout invalidates the administrator's existing sessions. New image uploads are decoded and rewritten as PNG; SVG upload is not allowed. Official vendor SVGs are bundled as reviewed static artwork.

The limiter uses SQLite and the direct peer address. Do not enable unverified proxy-header trust. On Render, validate the trusted proxy chain before using forwarded client addresses; otherwise visitors behind the same proxy can share limits. This single-instance configuration does not support horizontal scaling of SQLite storage.

Security tests are not a penetration-test certification. Existing PostgreSQL marketplace flows need integration testing against a staging PostgreSQL database. Dependency scans report known advisories only. No third-party tool binaries are executed or redistributed; community tool entries link to their official repositories. The inspiration website has no runtime connection to the new pages.

Admin studio supports company/contact/OTC settings, images, content, order, drafts, previews, publication, hide/show, removal and history. Main navigation labels, local destinations and ordering can be edited as Menu records. Granular editor publishing permissions and scheduled auto-publication are not enabled in this release.
