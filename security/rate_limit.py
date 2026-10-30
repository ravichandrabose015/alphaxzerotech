from collections import defaultdict, deque
from functools import wraps
from threading import Lock
from time import monotonic

from flask import abort, request


_events = defaultdict(deque)
_lock = Lock()


def rate_limit(max_requests: int, window_seconds: int):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            identity = forwarded or request.remote_addr or "unknown"
            key = f"{view.__module__}.{view.__name__}:{identity}"
            now = monotonic()
            with _lock:
                queue = _events[key]
                while queue and now - queue[0] > window_seconds:
                    queue.popleft()
                if len(queue) >= max_requests:
                    abort(429, description="Too many requests. Please try again shortly.")
                queue.append(now)
            return view(*args, **kwargs)
        return wrapped
    return decorator
