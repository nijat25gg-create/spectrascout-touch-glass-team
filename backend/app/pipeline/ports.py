"""Ports for the three pipeline calls.

The orchestrator depends on these signatures. Adapters hide transport.
"""

from typing import Protocol

from app.schemas.assessment import (
    ExplainInput,
    Explanation,
    ExtractInput,
    Extraction,
    ScoreInput,
    Scoring,
)


class ExtractionPort(Protocol):
    def extract(self, payload: ExtractInput) -> Extraction: ...


class ScoringPort(Protocol):
    def score(self, payload: ScoreInput) -> Scoring: ...


class ExplanationPort(Protocol):
    def explain(self, payload: ExplainInput) -> Explanation: ...
