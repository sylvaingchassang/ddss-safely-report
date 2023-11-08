import json
from datetime import date
from typing import Any, Optional


def serialize_dict(data: dict) -> str:
    """
    Transform Python dictionary into JSON string.
    """
    return json.dumps(data, default=_default)


def deserialize_json(data: str) -> dict:
    """
    Transform JSON string into Python dictionary.
    """
    return json.loads(data, object_hook=_object_hook)


def _default(obj: Any) -> Optional[dict]:
    """
    Custom method to serialize otherwise non-serializable data types.
    """
    if isinstance(obj, date):
        return {"_isoformat": obj.isoformat()}
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _object_hook(obj: Any) -> Any:
    """
    Hook to deserialize data that have been serialized by custom method.
    """
    _isoformat = obj.get("_isoformat")
    if _isoformat is not None:
        return date.fromisoformat(_isoformat)
    return obj
