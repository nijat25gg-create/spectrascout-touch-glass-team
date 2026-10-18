"""Attribute vocabulary for step A (v0.3), taken from rules/gates.yaml — one source of truth.

    vocabulary()                  -> {name: {"entity", "values", "kind", "question"}}
    vocabulary_block()            -> markdown table that goes into the extraction prompt
    normalize_attributes(f, text) -> list[AttributeFact], every vocabulary name exactly once
    engine_attrs(facts)           -> {name: value} for the gates engine (known and assumed only)

The same names and values feed the gates engine, the completeness module and the Jev questions,
so the three cannot drift apart.
"""
import re
import unicodedata
from typing import get_args

from contracts.models import AttributeFact, AttributeName
from engine.gates_loader import load_gates

UNKNOWN = "unknown"

# Which of the 16 C3 parameters a question about an attribute belongs to (C7 Question.parameter_id is
# required). Only attributes that can be asked are listed; client premises are never asked.
ATTR_TO_PARAM = {
    "target_defined": "measurand", "target_kind": "measurand", "targets_count": "measurand",
    "target_class": "concentration_range", "concentration_range": "concentration_range",
    "quantitative": "measurand_type", "reference_method": "reference_method",
    "reference_uncertainty": "reference_method", "acceptance_criteria": "required_accuracy",
    "intended_use": "regulatory", "gmp": "regulatory", "domain": "matrix", "optical_density": "matrix",
    "matrix_fluorescence": "matrix", "formulation_changed": "matrix", "physical_variation": "matrix",
    "sample_form": "phase", "heterogeneous": "phase", "matrix_aqueous": "water_content",
    "fluorophore": "measurand", "chromophore": "measurand", "streams": "installation_point",
    "temperature": "temperature", "fouling": "aggressiveness_fouling", "distance": "distance_to_instrument",
    "link_confirmed": "distance_to_instrument", "existing_fiber": "installation_point",
    "own_validation": "samples_available",
}


def vocabulary(g: dict | None = None) -> dict:
    g = g or load_gates()
    qs = g.get("questions", {})
    out = {}
    for name, a in g["attributes"].items():
        q = qs.get(name, {})
        out[name] = {
            "entity": a["entity"],
            "values": [str(v) for v in a["values"] if v != UNKNOWN],
            "kind": q.get("kind", "method"),
            "question": q.get("text", ""),
        }
    return out


def check_sync(g: dict | None = None) -> list[str]:
    """Contract enum AttributeName must equal the attribute list of rules/gates.yaml."""
    names = set(vocabulary(g))
    contract = set(get_args(AttributeName))
    problems = []
    if names - contract:
        problems.append(f"in gates.yaml but not in contracts AttributeName: {sorted(names - contract)}")
    if contract - names:
        problems.append(f"in contracts AttributeName but not in gates.yaml: {sorted(contract - names)}")
    return problems


def vocabulary_block(g: dict | None = None) -> str:
    """Markdown table for the prompt: allowed values plus the question the attribute answers."""
    rows = ["| attribute | about | allowed values (nothing fits → value null, status `unknown`) | what it answers |",
            "|---|---|---|---|"]
    for name, v in vocabulary(g).items():
        vals = ", ".join(f"`{x}`" for x in v["values"])
        meaning = v["question"] or "customer premise: fill only from what the customer writes"
        if v["kind"] == "lab_check":
            meaning = "LAB CHECK (normally measured on samples): " + meaning
        rows.append(f"| `{name}` | {v['entity']} | {vals} | {meaning} |")
    return "\n".join(rows)


# ---------------------------------------------------------------- quote check
_QUOTE_CHARS = str.maketrans({"\u201c": '"', "\u201d": '"', "\u201e": '"', "\u00ab": '"', "\u00bb": '"',
                              "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u2032": "'",
                              "\u2010": "-", "\u2011": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
                              "\u00a0": " ", "\u00ad": None, "\u200b": None, "\u200c": None, "\u200d": None})
_MIN_PART = 3     # every part of a quote (split at ellipses) must have at least 3 characters


def _norm_text(s: str) -> str:
    """Unicode form (NFKC), case, whitespace, typographic quotes, hyphens and dashes do not matter."""
    s = unicodedata.normalize("NFKC", s).translate(_QUOTE_CHARS).casefold()
    s = re.sub(r"\s+", " ", s).strip()
    return s.strip(" .,;:!?\"'()[]")


def _find_word(hay: str, part: str, start: int) -> int:
    """Position of `part` in `hay` from `start`, not inside a longer word; -1 if absent."""
    i = hay.find(part, start)
    while i >= 0:
        before = hay[i - 1] if i > 0 else " "
        after = hay[i + len(part)] if i + len(part) < len(hay) else " "
        if not (part[0].isalnum() and before.isalnum()) and not (part[-1].isalnum() and after.isalnum()):
            return i
        i = hay.find(part, i + 1)
    return -1


def quote_in_text(quote: str | None, text: str) -> bool:
    """True if `quote` is a verbatim piece of `text`, ignoring Unicode form, case, whitespace, quote marks,
    hyphens and dashes. Ellipses ("...", "…") split the quote into parts that must all occur, in order;
    each part needs >= 3 characters and must not start or end inside a word."""
    if not quote or not text:
        return False
    hay = _norm_text(text)
    parts = [_norm_text(x) for x in re.split(r"\.\.\.|…", quote)]
    parts = [x for x in parts if x]
    if not parts or any(len(x) < _MIN_PART for x in parts):
        return False
    pos = 0
    for part in parts:
        i = _find_word(hay, part, pos)
        if i < 0:
            return False
        pos = i + len(part)
    return True


# ---------------------------------------------------------------- value aliases
_ALIASES = {
    "true": "yes", "false": "no",
    "2": "2plus", "2+": "2plus", "two": "2plus", "several": "2plus", "multiple": "2plus", "many": "2plus",
    "more_than_one": "2plus", "one": "1", "single": "1",
    "unknown": UNKNOWN, "n/a": UNKNOWN, "none_stated": UNKNOWN, "not_stated": UNKNOWN, "null": UNKNOWN,
}
# "none" for these means a stated absence ("we have no fiber yet"); silence is not an absence.
_NONE_NEEDS_QUOTE = {"client_method", "existing_fiber", "cited_evidence", "reference_method"}
# Only AFS can confirm these; step A never sets them.
_NEVER_FROM_TEXT = {"link_confirmed"}


def _canon(value, allowed: list[str]):
    """Map a raw value to the vocabulary: exact, then case/space/hyphen-insensitive, then aliases."""
    if value is None:
        return None
    if isinstance(value, bool):
        value = "yes" if value else "no"
    raw = str(value).strip()
    if raw in allowed:
        return raw
    key = re.sub(r"[\s\-]+", "_", raw.casefold())
    for a in allowed:
        if key == a.casefold():
            return a
    alias = _ALIASES.get(key)
    if alias == UNKNOWN:
        return UNKNOWN
    if alias in allowed:
        return alias
    return raw


def _check_entry(f: AttributeFact, allowed: list[str], text: str, notes: list[str]):
    """One raw entry -> (value, status, quote), or None if it carries no usable information."""
    name = f.name
    if f.status == "unknown":
        return None
    if name in _NEVER_FROM_TEXT:
        notes.append(f"{name}: only AFS confirms this, step A value ignored")
        return None
    value = _canon(f.value, allowed)
    if value in (None, "", UNKNOWN):
        return ("", "conflicting", None) if f.status == "conflicting" else None
    if value not in allowed:
        notes.append(f"{name}: value {value!r} is not in the vocabulary -> unknown")
        return ("", "conflicting", None) if f.status == "conflicting" else None
    if f.status == "conflicting":
        return (value, "conflicting", None)
    if f.status == "known":
        if not quote_in_text(f.quote, text):
            notes.append(f"{name}: value {value!r} with a quote that is missing or not in the text -> unknown")
            return None
        return (value, "known", f.quote)
    if name in _NONE_NEEDS_QUOTE and value == "none":   # assumed
        notes.append(f"{name}: 'none' only assumed (silence is not absence) -> unknown")
        return None
    return (value, "assumed", None)


def _merge(name: str, entries: list, notes: list[str]):
    """Valid entries of one attribute -> one (value, status, quote)."""
    first_value = next((v for v, _, _ in entries if v), None)
    if any(st == "conflicting" for _, st, _ in entries):
        return (first_value or None, "conflicting", None)
    known = [e for e in entries if e[1] == "known"]
    known_values = list(dict.fromkeys(v for v, _, _ in known))
    if len(known_values) > 1:
        notes.append(f"{name}: the text supports two values ({known_values[0]!r}, {known_values[1]!r}) -> conflicting")
        return (known_values[0], "conflicting", None)
    if known:
        dropped = sorted({v for v, st, _ in entries if st == "assumed" and v != known[0][0]})
        if dropped:
            notes.append(f"{name}: stated {known[0][0]!r} wins over assumed {dropped}")
        return known[0]
    assumed_values = list(dict.fromkeys(v for v, _, _ in entries))
    if len(assumed_values) > 1:
        notes.append(f"{name}: two different assumptions {assumed_values[:2]} -> conflicting")
        return (assumed_values[0], "conflicting", None)
    return entries[0]


def normalize_attributes(facts: list[AttributeFact] | None, text: str, g: dict | None = None) -> tuple[list[AttributeFact], list[str]]:
    """Make step A output safe for the engine. Returns (facts, notes).

    Each entry is checked on its own first, then entries of the same attribute are merged:
    - values are mapped to the vocabulary (case, hyphens, aliases such as "2+" -> 2plus); outside -> dropped;
    - known needs a quote that is in the text (see quote_in_text), otherwise the entry is dropped:
      a value we cannot point to in the text is a question, not a fact;
    - assumed "none" for client_method / existing_fiber / cited_evidence / reference_method is dropped
      (silence is not absence); link_confirmed is never taken from step A;
    - merge: any conflicting entry -> conflicting; two different stated values -> conflicting;
      a stated value wins over a different assumption; two different assumptions -> conflicting;
    - every vocabulary name exactly once (nothing usable -> unknown); assumed/unknown/conflicting carry no quote;
    - justification assumed without a known client_method -> unknown (nothing to justify).
    """
    vocab = vocabulary(g)
    notes: list[str] = []
    valid: dict[str, list] = {}
    for f in facts or []:
        v = vocab.get(f.name)
        if v is None:
            continue
        e = _check_entry(f, v["values"], text, notes)
        if e is not None:
            valid.setdefault(f.name, []).append(e)
    out = []
    for name in vocab:
        if name not in valid:
            out.append(AttributeFact(name=name, value=None, status="unknown", quote=None))
            continue
        value, status, quote = _merge(name, valid[name], notes)
        out.append(AttributeFact(name=name, value=value or None, status=status, quote=quote))
    by = {f.name: f for f in out}
    j, cm = by.get("justification"), by.get("client_method")
    if j and j.status == "assumed" and not (cm and cm.status == "known" and cm.value not in (None, "none")):
        notes.append("justification: assumed without a proposed client method -> unknown")
        out = [AttributeFact(name=f.name, value=None, status="unknown", quote=None) if f.name == "justification" else f
               for f in out]
    return out, notes


def engine_attrs(facts: list[AttributeFact] | None) -> dict:
    """What the gates engine reads: known and assumed values. conflicting and unknown stay unknown."""
    return {f.name: f.value for f in facts or [] if f.status in ("known", "assumed") and f.value is not None}


def selftest() -> None:
    problems = check_sync()
    assert not problems, problems
    block = vocabulary_block()
    assert "`target_defined`" in block and "`existing_fiber`" in block and "LAB CHECK" in block
    text = "Wir trocknen ein Pulver. Wasser im Öl, kein Fluoreszenzmarker bekannt. Zwei Linien: \u201eKlar\u201c und trüb."
    facts, notes = normalize_attributes([
        AttributeFact(name="sample_form", value="powder", status="known", quote="ein  pulver."),
        AttributeFact(name="domain", value="petroleum", status="known", quote="not in the text"),
        AttributeFact(name="target_kind", value="oil-water", status="known", quote="Wasser im Öl"),
        AttributeFact(name="fluorophore", value="not_identified", status="known", quote="kein Fluoreszenzmarker bekannt"),
        AttributeFact(name="fluorophore", value="named", status="assumed", quote=None),
        AttributeFact(name="streams", value="2+", status="known", quote='Zwei Linien: "Klar" und trüb'),
        AttributeFact(name="streams", value=None, status="unknown", quote=None),
        AttributeFact(name="matrix_aqueous", value="No", status="assumed", quote="x"),
        AttributeFact(name="existing_fiber", value="none", status="assumed", quote=None),
        AttributeFact(name="justification", value="none_given", status="assumed", quote=None),
        AttributeFact(name="quantitative", value="yes", status="known", quote="Wi"),
    ], text)
    by = {f.name: f for f in facts}
    assert len(facts) == len(vocabulary())
    assert by["sample_form"].status == "known"                       # case/whitespace/punctuation ignored
    assert by["domain"].status == "unknown" and by["domain"].value is None   # invented quote is not a fact
    assert by["target_kind"].status == "unknown" and by["target_kind"].value is None
    assert by["fluorophore"].value == "not_identified" and by["fluorophore"].status == "known"   # stated beats assumed
    assert by["streams"].value == "2plus" and by["streams"].status == "known"   # alias, typographic quotes
    assert by["matrix_aqueous"].value == "no" and by["matrix_aqueous"].quote is None
    assert by["existing_fiber"].status == "unknown"                  # silence is not absence
    assert by["justification"].status == "unknown"                   # nothing proposed, nothing to justify
    assert by["quantitative"].status == "unknown"                    # quote shorter than 3 characters
    assert by["temperature"].status == "unknown"
    assert engine_attrs(facts) == {"sample_form": "powder", "streams": "2plus", "matrix_aqueous": "no",
                                   "fluorophore": "not_identified"}
    assert quote_in_text("Wasser ... bekannt", text) and not quote_in_text("bekannt ... Wasser", text)
    # reviewer cases 18.10: validate before merge, Unicode forms, word boundaries
    import unicodedata as _u
    t2 = "Die Probe ist trüb und manchmal klar. Wasser in Öl, in‑line gemessen."
    f2, _ = normalize_attributes([
        AttributeFact(name="optical_density", value="opaque", status="known", quote="invented words"),
        AttributeFact(name="optical_density", value="turbid", status="known", quote="Probe ist trüb"),
        AttributeFact(name="target_kind", value="banana", status="conflicting", quote=None),
        AttributeFact(name="domain", value="Unknown", status="assumed", quote=None),
        AttributeFact(name="domain", value="dairy", status="known", quote="Probe ist trüb"),
        AttributeFact(name="heterogeneous", value="yes", status="known", quote="trüb"),
        AttributeFact(name="heterogeneous", value="no", status="known", quote="klar"),
        AttributeFact(name="reference_method", value="none", status="assumed", quote=None),
        AttributeFact(name="link_confirmed", value="yes", status="known", quote="in-line gemessen"),
    ], _u.normalize("NFD", t2))
    b2 = {f.name: f for f in f2}
    assert b2["optical_density"].value == "turbid" and b2["optical_density"].status == "known"
    assert b2["target_kind"].status == "conflicting" and b2["target_kind"].value is None
    assert b2["domain"].value == "dairy" and b2["domain"].status == "known"
    assert b2["heterogeneous"].status == "conflicting"
    assert b2["reference_method"].status == "unknown" and b2["link_confirmed"].status == "unknown"
    assert quote_in_text("Wasser in Öl", _u.normalize("NFD", t2)) and quote_in_text("in-line", t2)
    assert not quote_in_text("a ... b ... c", t2) and not quote_in_text("asser in", t2)
    from contracts.models import ParameterId
    askable = {n for n, v in vocabulary().items() if v["kind"] != "never"}
    assert askable <= set(ATTR_TO_PARAM), askable - set(ATTR_TO_PARAM)
    assert set(ATTR_TO_PARAM.values()) <= set(get_args(ParameterId))
    print(f"vocab OK: {len(facts)} attributes, {len(notes)} normalisation notes")


if __name__ == "__main__":
    selftest()
