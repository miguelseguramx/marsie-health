"""DRF exception handler that emits FHIR OperationOutcome on errors.

Wired per-view via `get_exception_handler` so it only applies under /fhir/.
Maps common HTTP statuses to the `issue.code` codes specified by FHIR R5.
"""

from __future__ import annotations

from typing import Any

from fhir.resources.operationoutcome import OperationOutcome, OperationOutcomeIssue
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

# Status -> FHIR issue.code mapping (issue.severity is always "error" here).
_ISSUE_CODE_BY_STATUS = {
    http_status.HTTP_400_BAD_REQUEST: "invalid",
    http_status.HTTP_401_UNAUTHORIZED: "security",
    http_status.HTTP_403_FORBIDDEN: "security",
    http_status.HTTP_404_NOT_FOUND: "not-found",
    http_status.HTTP_405_METHOD_NOT_ALLOWED: "not-supported",
    http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "not-supported",
    http_status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
}


def _diagnostics_from(detail: Any) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "; ".join(str(d) for d in detail)
    if isinstance(detail, dict):
        return "; ".join(f"{k}: {v}" for k, v in detail.items())
    return str(detail)


def fhir_exception_handler(exc, context):
    response = drf_default_handler(exc, context)
    if response is None:
        return None

    code = _ISSUE_CODE_BY_STATUS.get(response.status_code, "exception")
    diagnostics = _diagnostics_from(response.data)
    issue_kwargs: dict[str, Any] = {"severity": "error", "code": code}
    if diagnostics:
        issue_kwargs["diagnostics"] = diagnostics

    outcome = OperationOutcome(issue=[OperationOutcomeIssue(**issue_kwargs)])
    return Response(
        outcome,
        status=response.status_code,
        headers={k: v for k, v in response.items()},
    )
