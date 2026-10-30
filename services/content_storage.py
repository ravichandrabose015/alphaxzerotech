import hashlib
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".md", ".doc", ".docx", ".ppt", ".pptx", ".csv", ".json"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".tar", ".gz", ".tgz"}


def upload_root() -> Path:
    root = Path(current_app.config["CONTENT_HUB_UPLOAD_ROOT"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _allowed(kind, extension):
    if kind in {"thumbnail", "banner", "gallery", "screenshots"}:
        return extension in IMAGE_EXTENSIONS
    if kind in {"videos"}:
        return extension in VIDEO_EXTENSIONS
    if kind in {"lab_files", "course_resources", "supporting_files", "resource_file"}:
        return extension in DOCUMENT_EXTENSIONS | ARCHIVE_EXTENSIONS | VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
    return extension in DOCUMENT_EXTENSIONS | ARCHIVE_EXTENSIONS


def _valid_image(header, extension):
    if extension == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {".jpg", ".jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    if extension == ".webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    if extension == ".gif":
        return header.startswith((b"GIF87a", b"GIF89a"))
    return False


def save_upload(file, module, kind):
    if not file or not file.filename:
        return None
    extension = Path(secure_filename(file.filename)).suffix.lower()
    if not _allowed(kind, extension):
        raise ValueError(f"Unsupported {kind.replace('_', ' ')} file type.")
    header = file.stream.read(16)
    file.stream.seek(0)
    if kind in {"thumbnail", "banner", "gallery", "screenshots"} and not _valid_image(header, extension):
        raise ValueError(f"Invalid {kind.replace('_', ' ')} image file.")
    original_name = secure_filename(file.filename)
    relative_path = Path(module) / kind / f"{uuid.uuid4().hex}{extension}"
    target = upload_root() / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with target.open("wb") as output:
        while chunk := file.stream.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
    return {
        "path": relative_path.as_posix(),
        "name": original_name,
        "sha256": digest.hexdigest(),
        "size": target.stat().st_size,
    }


def save_multiple(files, module, kind):
    saved = []
    for file in files:
        result = save_upload(file, module, kind)
        if result:
            saved.append(result)
    return saved


def resolve_upload(relative_path):
    root = upload_root()
    candidate = (root / (relative_path or "")).resolve()
    if candidate == root or root not in candidate.parents:
        raise FileNotFoundError("Invalid content file path.")
    return candidate
