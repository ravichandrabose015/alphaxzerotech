import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def provisioning_uri(secret: str, username: str) -> str:
    label = quote(f"AlphaX ZeroTech:{username}")
    return f"otpauth://totp/{label}?secret={secret}&issuer=AlphaX%20ZeroTech&digits=6&period=30"


def _code(secret: str, counter: int) -> str:
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def verify_code(secret: str, supplied: str) -> bool:
    if not supplied.isdigit() or len(supplied) != 6:
        return False
    counter = int(time.time() // 30)
    return any(hmac.compare_digest(_code(secret, counter + drift), supplied) for drift in (-1, 0, 1))
