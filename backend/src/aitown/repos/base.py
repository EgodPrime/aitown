from typing import Any


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
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
