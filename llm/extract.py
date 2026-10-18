"""Step A: customer text -> 16 parameters + 12 features (+ v0.3 attributes).  C2 -> C3.

v0.3: with EXTRACT_V03=1 (default) the prompt also asks for `attributes` from the vocabulary in
rules/gates.yaml (llm/prompts/extract_attributes_section.md); llm.vocab.normalize_attributes makes
them safe for the gates engine. EXTRACT_V03=0 gives the v0.2 behaviour.
"""
import os

from pydantic import Field

from contracts.models import AttributeFact, ExtractInput, Extraction, FactB, Features, Parameter, Strict

from .client import MODEL_EXTRACT, example, is_mock, parse, prompt
from .vocab import normalize_attributes, quote_in_text, vocabulary_block


class _ExtractionOutV03(Strict):
    """What Claude fills in v0.3 (private, not a contract): `attributes` required, no `jev`.
    Converted to the C3 contract `Extraction` right after the call."""
    summary: str = Field(description="Customer task in one sentence, in the case language")
    parameters: list[Parameter] = Field(description="All 16 parameter ids exactly once")
    features: Features
    attributes: list[AttributeFact] = Field(description="One entry per vocabulary attribute")


class _ExtractionOutB(_ExtractionOutV03):
    """v0.4: also method B facts. One line per fact, `key | value | status | quote`: objects with four fields
    on top of the v0.3 schema make the structured-output grammar too large (API 400, 18.10)."""
    facts_b: list[str] = Field(description="One line per method B fact key: key | value | status | quote")


_B_STATUS = {"reported", "inferred", "unknown", "conflicting"}


def _fact_line(line: str) -> FactB | None:
    """'key | value | status | quote' -> FactB; 'null' or empty = None; a bad status becomes unknown."""
    parts = [p.strip() for p in line.split("|", 3)]
    if len(parts) < 3 or not parts[0]:
        return None
    parts += [""] * (4 - len(parts))
    key, value, status, quote = (None if p.lower() in ("", "null", "none") else p for p in parts)
    key = key.strip("`")
    status = status if status in _B_STATUS else "unknown"
    return FactB(key=key, value=value, status=status, quote=quote)


PARAM_ORDER = [
    "measurand", "measurand_type", "matrix", "phase", "water_content",
    "concentration_range", "required_accuracy", "temperature", "pressure",
    "aggressiveness_fouling", "installation_point", "distance_to_instrument",
    "measurement_frequency", "reference_method", "samples_available", "regulatory",
]


def _normalize(ex: Extraction, text: str) -> Extraction:
    """Guarantee each of the 16 ids exactly once, in order, and real quotes."""
    by_id = {}
    for p in ex.parameters:
        by_id.setdefault(p.id, p)
    fixed = []
    for pid in PARAM_ORDER:
        p = by_id.get(pid) or Parameter(id=pid, value=None, status="unknown",
                                        evidence_quote=None, source="llm_assumption")
        # a quote that is not in the text is not evidence
        if p.evidence_quote and not quote_in_text(p.evidence_quote, text):
            p = p.model_copy(update={"evidence_quote": None,
                                     "status": "assumed" if p.status == "known" else p.status})
        fixed.append(p)
    return ex.model_copy(update={"parameters": fixed})


def v03_enabled() -> bool:
    return os.getenv("EXTRACT_V03", "1").lower() in ("1", "true", "yes")


def b_enabled() -> bool:
    """EXTRACT_B=1 (default) asks step A for the method B facts too; 0 = engine B bridges from the attributes."""
    return v03_enabled() and os.getenv("EXTRACT_B", "1").lower() in ("1", "true", "yes")


def system_prompt() -> str:
    base = prompt("extract_system.md")
    if not v03_enabled():
        return base
    section = prompt("extract_attributes_section.md").replace("{{VOCABULARY}}", vocabulary_block())
    out = base + "\n\n" + section
    if b_enabled():
        from .facts_b import block
        out += "\n\n" + prompt("extract_facts_b_section.md").replace("{{FACTS_B}}", block())
    return out


def _normalize_v03(ex: Extraction, text: str) -> Extraction:
    if not v03_enabled():
        return ex.model_copy(update={"attributes": None, "jev": None})
    facts, notes = normalize_attributes(ex.attributes, text)
    for n in notes:
        print(f"[llm] A/attributes: {n}")
    update = {"attributes": facts, "jev": None}   # jev is filled by the backend
    if ex.facts_b is not None:
        from .facts_b import normalize
        fb, notes_b = normalize(ex.facts_b, text)
        for n in notes_b:
            print(f"[llm] A/facts_b: {n}")
        update["facts_b"] = fb
    return ex.model_copy(update=update)


def extract(inp: ExtractInput) -> Extraction:
    if is_mock():
        ex = Extraction.model_validate(example("C3_extraction.example.json"))
        if not v03_enabled():
            ex = ex.model_copy(update={"attributes": None, "jev": None})
        return ex   # the example is already normalised for its own text
    user = f"Case language: {inp.language}\n\nCustomer message:\n<customer_text>\n{inp.text}\n</customer_text>"
    if b_enabled():
        out = parse(system_prompt(), user, _ExtractionOutB, max_tokens=10000, step="A/extract", model=MODEL_EXTRACT)
        ex = Extraction(summary=out.summary, parameters=out.parameters, features=out.features,
                        attributes=out.attributes, jev=None,
                        facts_b=[f for f in map(_fact_line, out.facts_b) if f])
    elif v03_enabled():
        out = parse(system_prompt(), user, _ExtractionOutV03, max_tokens=9000, step="A/extract", model=MODEL_EXTRACT)
        ex = Extraction(summary=out.summary, parameters=out.parameters, features=out.features,
                        attributes=out.attributes, jev=None)
    else:
        ex = parse(system_prompt(), user, Extraction, max_tokens=4000, step="A/extract", model=MODEL_EXTRACT)
    return _normalize_v03(_normalize(ex, inp.text), inp.text)
