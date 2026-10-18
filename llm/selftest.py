"""Quick check of the LLM module.

    LLM_MOCK=1 python -m llm.selftest        # no key, no cost
    python -m llm.selftest                   # real call to Claude, needs ANTHROPIC_API_KEY in .env
"""
import json

from contracts.models import ExplainInput, ExtractInput

from llm import explain, extract
from llm.client import example, is_mock

c2 = ExtractInput.model_validate(example("C2_extract_input.example.json"))
c3 = extract(c2)
print("step A ok:", c3.summary)
for p in c3.parameters:
    print(f"  {p.id:24} {p.status:8} {p.value}")
print("  features:", json.dumps({k: v["value"] for k, v in c3.features.model_dump().items()}))

c6 = ExplainInput.model_validate(example("C6_explain_input.example.json"))
c7 = explain(c6)
print("step B ok:", len(c7.questions), "questions,", len(c7.rationale), "rationales")
print("mode:", "MOCK" if is_mock() else "REAL")

# v0.3: vocabulary from rules/gates.yaml, attribute normalisation, Jev merge (mock, no key)
from llm import jev, vocab  # noqa: E402
vocab.selftest()
jev.selftest()
if c3.attributes:
    filled = [a for a in c3.attributes if a.status != "unknown"]
    print(f"  attributes (v0.3): {len(filled)} of {len(c3.attributes)} filled")

# v0.3 step B: readable gates view and the post-check (no key needed)
from contracts.models import Claim, Explanation  # noqa: E402
from llm.explain import AFS_SOURCE_CARD, _card_ids, _check, _gates_view  # noqa: E402

view, sources = _gates_view(c6)
assert '"decision_status"' in view and sources, "gates view must list status and sources"
c7x = Explanation.model_validate(example("C7_explanation.example.json"))
r0 = c7x.rationale[0]
bad = c7x.model_copy(update={
    "rationale": [r0.model_copy(update={"claims": [
        Claim(claim="ok", kb_card="card-nir", source="S99 p.1"),               # invented source -> removed
        Claim(claim="afs only", kb_card="card-unknown", source=sorted(sources)[0]),
        Claim(claim="nothing", kb_card="card-unknown", source=None)]}),       # dropped
        r0.model_copy(update={"method": "fluorescence"})],                   # not ranked -> dropped
    "questions": [c7x.questions[0].model_copy(update={"attribute": "colour"})]})
methods = [r.method for r in c6.scoring.ranked] + [r.method for r in c6.scoring.rejected]
chk = _check(bad, c6, _card_ids(methods), sources)
claims = chk.rationale[0].claims
assert len(chk.rationale) == 1 and len(claims) == 2, chk.rationale
assert claims[0].source is None and claims[1].kb_card == AFS_SOURCE_CARD
assert chk.questions[0].attribute is None
print(f"  step B check (v0.3) OK: gates view {len(view)} chars, {len(sources)} citable sources")
