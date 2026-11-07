from flask import current_app, request

def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if current_app.config.get('SESSION_COOKIE_SECURE'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' "
        "https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'self'; "
        "base-uri 'self'; form-action 'self'; object-src 'none'"
    )
    if request.blueprint in ('studio','home','contact') or request.path.startswith('/admin'):
        response.headers['Content-Security-Policy'] = response.headers['Content-Security-Policy'].replace("script-src 'self' 'unsafe-inline'", "script-src 'self'")
    if response.headers.get("Content-Type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-store"
    return response


def init_app(application) -> None:
    application.after_request(apply_security_headers)
