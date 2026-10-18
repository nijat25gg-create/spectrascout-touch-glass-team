"""CS1 adapter: LLM step A (extract, C2 → C3) and step B (explain, C6 → C7).

Calls llm/ directly. With LLM_MOCK=1 (default in .env.example) llm/ returns the examples
from contracts/examples, so the backend runs without an API key.
"""
import app  # noqa: F401
from llm import explain as _explain
from llm import extract as _extract

from app.schemas.assessment import ExplainInput, Explanation, ExtractInput, Extraction


def extract(payload: ExtractInput) -> Extraction:
    if not isinstance(payload, ExtractInput):
        raise TypeError("adapter payload must be ExtractInput")
    return _extract(payload)


def explain(payload: ExplainInput) -> Explanation:
    if not isinstance(payload, ExplainInput):
        raise TypeError("adapter payload must be ExplainInput")
    return _explain(payload)
