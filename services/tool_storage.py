import hashlib
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TOOL_EXTENSIONS = {".zip", ".7z", ".tar", ".gz", ".tgz", ".msi", ".exe", ".deb", ".rpm", ".dmg", ".pkg", ".apk", ".jar", ".whl"}
DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def upload_root() -> Path:
    root = Path(current_app.config["MARKETPLACE_UPLOAD_ROOT"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _extension(file: FileStorage) -> str:
    return Path(secure_filename(file.filename or "")).suffix.lower()


def _valid_image_signature(header: bytes, extension: str) -> bool:
    if extension == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {".jpg", ".jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    if extension == ".webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    return False


def save_upload(file: FileStorage, kind: str, required=False):
    if not file or not file.filename:
        if required:
            raise ValueError(f"{kind.replace('_', ' ').title()} is required.")
        return None
    extension = _extension(file)
    allowed = IMAGE_EXTENSIONS if kind in {"thumbnail", "banner", "gallery", "screenshots"} else DOCUMENT_EXTENSIONS if kind == "documentation" else TOOL_EXTENSIONS
    if extension not in allowed:
        raise ValueError(f"Unsupported {kind.replace('_', ' ')} file type.")
    header = file.stream.read(16)
    file.stream.seek(0)
    if kind in {"thumbnail", "banner", "gallery", "screenshots"} and not _valid_image_signature(header, extension):
        raise ValueError(f"Invalid {kind.replace('_', ' ')} image file.")
    original_name = secure_filename(file.filename)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    relative_path = Path(kind) / stored_name
    target = upload_root() / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with target.open("wb") as output:
        while True:
            chunk = file.stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            output.write(chunk)
    result = {"path": relative_path.as_posix(), "name": original_name, "sha256": digest.hexdigest()}
    return result


def save_multiple(files, kind: str, required=False):
    valid_files = [file for file in files if file and file.filename]
    if required and not valid_files:
        raise ValueError(f"At least one {kind.replace('_', ' ')} image is required.")
    return [save_upload(file, kind, required=True)["path"] for file in valid_files]


def resolve_upload(relative_path: str) -> Path:
    root = upload_root()
    candidate = (root / (relative_path or "")).resolve()
    if candidate == root or root not in candidate.parents:
        raise FileNotFoundError("Invalid marketplace file path.")
    return candidate
