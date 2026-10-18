"""CS3 adapter: rules engine (score, C4 → C5). Calls engine.score_methods directly (gates engine since 18.10)."""
import app  # noqa: F401
from engine import score_methods

from app.schemas.assessment import ScoreInput, Scoring


def score(payload: ScoreInput, probs: dict | None = None) -> Scoring:
    if not isinstance(payload, ScoreInput):
        raise TypeError("adapter payload must be ScoreInput")
    return score_methods(payload, probs=probs)
