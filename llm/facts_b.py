"""Step A for method B: the fact list of rules/b/catalog_b.yaml in the prompt, and the safety check after.

Each fact = value + unit/category + source + status. Missing data stays unknown:
- unknown key -> dropped; value outside the allowed categories -> unknown;
- reported needs a quote that is really in the customer text, else it becomes inferred (no quote);
- inferred never counts as covered in engine B.
"""
from __future__ import annotations

import re

from contracts.models import FactB

from .vocab import quote_in_text

SKIP = {"CustomerRequest.claimed_readiness",   # derived inside the engine, never asked from step A
        "Configuration.operating_envelope.temperature_c"}   # probe data sheet, entered by the expert
_NUM = re.compile(r"(?<![\d.])-?\d+(?:\.\d+)?")


def _nums(v) -> list[float]:
    """'20..180', '20-180', '-10 to 120' -> sorted numbers ('..' first split so 20..180 stays two numbers)."""
    return sorted(float(n) for n in _NUM.findall(str(v or "").replace("..", " ")))


EXTRA = {   # request facts the engine reads that are not technical schema fields
    "CustomerRequest.asks": {"domain": ["assessment", "approve_concept", "exact_config_now", "readiness_proof"],
                             "ask": "What does the customer ask AFS to do?"},
    "CustomerRequest.combination_to_keep_calibration": {"domain": ["yes", "no"],
                             "ask": "Does the customer add a method so that an old calibration stays valid?"},
}


def catalog_facts() -> dict:
    from engine.b.core import load_b
    cat, _ = load_b()
    facts = {k: v for k, v in cat["facts"].items() if k not in SKIP}
    facts.update(EXTRA)
    return facts


def block() -> str:
    rows = ["| key | allowed values (nothing fits → value null, status `unknown`) | what it answers |", "|---|---|---|"]
    for k, v in catalog_facts().items():
        if v.get("numeric"):
            vals = f"number range `min..max` in {v.get('unit', '')} (one value: `x..x`); only numbers the customer writes"
        else:
            vals = ", ".join(f"`{x}`" for x in v["domain"])
        note = " Several targets: comma-separated." if v.get("list") else ""
        rows.append(f"| `{k}` | {vals} | {v.get('ask', '')}{note} |")
    return "\n".join(rows)


def normalize(facts: list[FactB] | None, text: str) -> tuple[list[FactB], list[str]]:
    cat, out, notes, seen = catalog_facts(), [], [], set()
    for f in facts or []:
        spec = cat.get(f.key)
        if spec is None:
            notes.append(f"dropped unknown key {f.key}")
            continue
        if f.key in seen:
            notes.append(f"duplicate {f.key} ignored")
            continue
        seen.add(f.key)
        status, value, quote = f.status, f.value, f.quote
        if spec.get("numeric"):
            nums = _nums(value)
            ok = status == "reported" and len(nums) in (1, 2) and quote and quote_in_text(quote, text)
            if value is not None and not ok:
                notes.append(f"{f.key}: number without a reported quote -> unknown")
            value = f"{nums[0]:g}..{nums[-1]:g}" if ok else None
            status, quote = ("reported", quote) if ok else ("unknown", None)
            out.append(FactB(key=f.key, value=value, unit=spec.get("unit"), status=status, quote=quote,
                             source="client_text" if ok else None))
            continue
        dom = [str(x) for x in spec["domain"]]
        if value is not None and status not in ("unknown", "conflicting"):
            parts = [p.strip() for p in str(value).split(",") if p.strip()] if spec.get("list") else [str(value).strip()]
            bad = [p for p in parts if p not in dom]
            if bad or not parts:
                notes.append(f"{f.key}: value {value!r} outside the categories -> unknown")
                status, value, quote = "unknown", None, None
            else:
                value = ", ".join(parts)
        if status in ("unknown", "conflicting"):
            value = None if status == "unknown" else value
            quote = None if status == "unknown" else quote
        if status == "reported" and not (quote and quote_in_text(quote, text)):
            notes.append(f"{f.key}: quote not in the text -> inferred")
            status, quote = "inferred", None
        if status == "inferred":
            quote = None
        source = "client_text" if status == "reported" else ("step A inference" if status == "inferred" else f.source)
        out.append(FactB(key=f.key, value=value, unit=f.unit or "category", status=status, quote=quote, source=source))
    for k in cat:   # every catalog fact appears, unknown ones explicitly
        if k not in seen:
            out.append(FactB(key=k, value=None, unit="category", status="unknown", quote=None, source=None))
    return out, notes


def to_engine(facts: list[FactB] | None) -> dict:
    """List of FactB -> {key: {value, status, unit, source, quote}} for engine.b.assess_b."""
    cat = catalog_facts()
    out = {}
    for f in facts or []:
        val = f.value
        if val is not None and cat.get(f.key, {}).get("numeric"):
            nums = _nums(val)
            val = [nums[0], nums[-1]] if nums else None
        elif val is not None and cat.get(f.key, {}).get("list"):
            val = [p.strip() for p in val.split(",") if p.strip()]
        out[f.key] = {"value": val, "status": f.status, "unit": f.unit, "source": f.source, "quote": f.quote}
    return out
