"""Failures from a pipeline step, after the frontend request has been accepted.

Codes follow contract E: llm_error (steps A or B), engine_error (rules engine),
internal_error (anything else). `status` is the HTTP status the API returns.
"""
from typing import Literal

ErrorCode = Literal["llm_error", "engine_error", "internal_error"]


class IntegrationError(Exception):
    def __init__(self, code: ErrorCode, message: str, status: int = 502) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class EditError(ValueError):
    """An expert edit or answer that does not fit the contract (e.g. unknown feature value)."""
