"""Small helpers and exceptions used by repository implementations."""

from typing import Any


class NotFoundError(Exception):
    """Raised when a repository lookup fails to find the requested entity."""
    pass


class ConflictError(Exception):
    """Raised when a repository operation fails due to a uniqueness or integrity conflict."""
    pass


def to_json_text(obj: Any) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)


def from_json_text(text: str):
    import json

    if text is None:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text
