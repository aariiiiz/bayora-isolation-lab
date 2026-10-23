import os
import re
from typing import Tuple, Optional
from app.core.config import settings
from app.core.errors import FileValidationError

SUPPORTED_EXTENSIONS = {
    ".json": "application/json",
    ".jsonl": "application/x-jsonlines",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
}

DISALLOWED_PATTERNS = [
    r"\.\.",        # Directory traversal
    r"[\0\r\n]",    # Null bytes, CRLF injection
    r"[<>:\"/\\|?*]" # Windows illegal filename characters
]

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes an uploaded filename to prevent directory traversal and path injections.
    """
    # Extract only the base name
    clean_name = os.path.basename(filename)
    # Strip dangerous characters
    clean_name = re.sub(r"[^\w\-.]", "_", clean_name)
    if not clean_name or clean_name.startswith("."):
        clean_name = f"artifact_{clean_name}"
    return clean_name

def validate_uploaded_file(filename: str, file_size: int, mime_type: Optional[str] = None) -> Tuple[str, str]:
    """
    Validates file extension, size, and returns sanitized filename and detected format.
    Raises FileValidationError on any violation.
    """
    if file_size <= 0:
        raise FileValidationError("File is empty (0 bytes).")
    
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise FileValidationError(f"File size exceeds maximum allowable limit of {max_mb} MB.")

    clean_filename = sanitize_filename(filename)
    _, ext = os.path.splitext(clean_filename.lower())

    if ext not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise FileValidationError(
            f"Unsupported file format '{ext}'. Allowed formats: {allowed}."
        )

    # Return clean filename and normalized artifact type
    artifact_type = ext.lstrip(".")
    if artifact_type == "yml":
        artifact_type = "yaml"

    return clean_filename, artifact_type
