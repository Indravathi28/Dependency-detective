"""Input and file validation. Raises ValueError with a user-friendly message."""
from backend.config import MAX_UPLOAD_BYTES


def validate_text(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("The input is empty. Paste requirements or upload a file.")
    if "\x00" in text:
        raise ValueError("This looks like a binary file, not a requirements text file.")
    if len(text.encode("utf-8")) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Input is too large (limit {MAX_UPLOAD_BYTES // 1024} KB).")
    return text


def validate_upload(name: str, data: bytes) -> str:
    if not name.lower().endswith(".txt"):
        raise ValueError("Unsupported file type. Upload a requirements .txt file.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File is too large (limit {MAX_UPLOAD_BYTES // 1024} KB).")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("File must be UTF-8 text.")
    return validate_text(text)
