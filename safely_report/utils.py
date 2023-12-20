import json
import os
import uuid
from datetime import date
from typing import Any, Optional, Type


def check_dict_required_fields(
    data: dict, required_fields: list[tuple[str, Type]]
):
    """
    Check if the given data dictionary has all required fields
    with expected data types.
    """
    for field_name, field_type in required_fields:
        field_value = data.get(field_name)
        if field_value is None:
            raise KeyError(f"Missing field: {field_name}")
        if not isinstance(field_value, field_type):
            raise ValueError(f"{field_name} should contain {field_type}")


def get_env_var(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise KeyError(f"Missing environment variable: {name}")
    return value


def generate_uuid4() -> str:
    return str(uuid.uuid4())


def serialize(data: Any) -> str:
    """
    Transform Python object into JSON string.
    """
    return json.dumps(data, default=_default)


def deserialize(data: str) -> Any:
    """
    Transform JSON string into Python object.
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
