import json
from datetime import date
from typing import Any, Optional


def _default(obj: Any) -> Optional[dict]:
    """
    Custom method to serialize otherwise non-serializable data types
    """
    if isinstance(obj, date):
        return {"_isoformat": obj.isoformat()}
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _object_hook(obj: Any) -> Any:
    """
    Hook to deserialize data that have been serialized by custom method
    """
    _isoformat = obj.get("_isoformat")
    if _isoformat is not None:
        return date.fromisoformat(_isoformat)
    return obj


def serialize_response_data(response_data: dict) -> str:
    return json.dumps(response_data, default=_default)


def deserialize_response_data(response_data: str) -> dict:
    return json.loads(response_data, object_hook=_object_hook)
