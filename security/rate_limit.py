from collections import defaultdict, deque
from functools import wraps
from time import time
from flask import abort, request
from database.database import get_db

_events = defaultdict(deque)  # Retained for existing test integrations.

def rate_limit(max_requests, window_seconds):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            # Do not trust caller-provided forwarding headers.
            identity = request.remote_addr or 'unknown'
            key = f'{view.__module__}.{view.__name__}:{identity}'
            now = time()
            db = get_db()
            db.execute('BEGIN IMMEDIATE')
            try:
                db.execute('DELETE FROM security_limits WHERE stamp < ?', (now-3600,))
                count = db.execute('SELECT count(*) FROM security_limits WHERE bucket=? AND stamp>?', (key,now-window_seconds)).fetchone()[0]
                if count >= max_requests:
                    db.rollback()
                    abort(429, description='Too many requests. Please try again shortly.')
                db.execute('INSERT INTO security_limits VALUES (?,?)', (key,now))
                db.commit()
            except Exception:
                db.rollback()
                raise
            return view(*args, **kwargs)
        return wrapped
    return decorator
