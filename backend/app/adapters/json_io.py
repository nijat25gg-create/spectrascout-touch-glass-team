"""JSON round trip used inside adapters.

The orchestrator passes typed models. An adapter serializes them here so the
fake transport still speaks JSON, then validates the result back into a model.
"""

import json
from typing import Any


def as_json_object(payload: Any) -> dict[str, Any]:
    """Return a plain object that survived a JSON round trip."""
    if not isinstance(payload, dict):
        raise TypeError("adapter payload must be a JSON object")
    try:
        encoded = json.dumps(payload)
    except TypeError as exc:
        raise TypeError("adapter payload must be JSON-serializable") from exc
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise TypeError("adapter payload must be a JSON object")
    return decoded
