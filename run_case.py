"""End-to-end run without the backend: customer text -> C3 -> C4 -> C5 -> C6 -> C7.

    LLM_MOCK=1 python run_case.py                 # example text, mock LLM
    python run_case.py "Wir wollen ..." de        # real Claude (needs ANTHROPIC_API_KEY)

Semyon: the backend does exactly these calls in this order. Since 18.10 the engine is the gates engine:
pass C3.attributes in C4.
"""
import sys
import uuid

from contracts.models import ExplainInput, ExtractInput, ScoreInput
from engine import score_methods
from llm import explain, extract
from llm.client import example

text = sys.argv[1] if len(sys.argv) > 1 else example("C2_extract_input.example.json")["text"]
lang = sys.argv[2] if len(sys.argv) > 2 else "de"
case_id = "case-" + uuid.uuid4().hex[:8]

c3 = extract(ExtractInput(case_id=case_id, text=text, language=lang))           # step A
c5 = score_methods(ScoreInput(case_id=case_id, features=c3.features,             # engine (gates)
                              attributes=c3.attributes))
c7 = explain(ExplainInput(case_id=case_id, language=lang, summary=c3.summary,    # step B
                          parameters=c3.parameters, features=c3.features, scoring=c5))

print("Summary:", c3.summary)
print("Ranked:", [(r.method, r.probe, r.confidence) for r in c5.ranked])
print("Rejected:", [(r.method, r.rule_id) for r in c5.rejected])
print("Questions:", [q.text for q in c7.questions])
print("Experiment:", c7.experiment.goal)
a = c5.assessment
if a is not None:
    print("Gates (v0.3):", a.decision_status, "| selected:", a.selected)
    print("  premises:", [(p.rule_id, p.verdict) for p in a.premise_flags] or "none")
    print("  method questions:", [q.attribute for q in a.questions if q.kind == "method"] or "none")
    print("  plan questions:", [q.attribute for q in a.questions if q.kind == "plan"] or "none")
    print("  lab checks (step 0):", [q.attribute for q in a.lab_checks] or "none")
