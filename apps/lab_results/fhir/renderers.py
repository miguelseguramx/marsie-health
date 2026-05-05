"""DRF renderer that emits FHIR JSON.

Used by views under /fhir/ so responses carry the application/fhir+json
content type that downstream FHIR tooling expects. The renderer accepts
either a `fhir.resources` Pydantic model (which it serializes via
`model_dump(exclude_none=True, by_alias=True)`) or any JSON-serialisable
mapping (so OperationOutcome dicts, etc., still work).
"""

from __future__ import annotations

import json
from typing import Any

from rest_framework.renderers import JSONRenderer


def _to_jsonable(data: Any) -> Any:
    # fhir.resources.fhirtypes models all expose `model_dump`. mode='json'
    # converts dates/datetimes/Decimals to JSON primitives.
    if hasattr(data, "model_dump"):
        return data.model_dump(exclude_none=True, by_alias=True, mode="json")
    return data


class FHIRJSONRenderer(JSONRenderer):
    media_type = "application/fhir+json"
    format = "fhir+json"
    charset = "utf-8"

    def render(self, data: Any, accepted_media_type: str | None = None, renderer_context=None) -> bytes:
        if data is None:
            return b""
        payload = _to_jsonable(data)
        return json.dumps(payload, ensure_ascii=False, allow_nan=False).encode(self.charset)
