"""Build frontend fakes from the real gates engine (night state of 18.10).

    python3 frontend/tools/make_gates_fakes.py . frontend      (from the repo root, engine/gates.py present)

For D01 and H04: golden attributes -> engine.gates.assess -> C8 fake with
`attributes` + `assessment`, plus `_fake_whatif`: for every method question,
the engine output for each possible answer (used only by the fake recompute).
The C7 texts (reasoning) are kept from the existing fake.
"""
import json, sys
from pathlib import Path
repo, fe = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo))
from engine.gates import assess
from engine.gates_loader import load_gates, load_yaml

g = load_gates()
golden = load_yaml(repo / "eval/golden_cases.yaml")["cases"]

def attrs_of(cid):
    c = golden[cid]
    a = dict(c["attrs"])
    if c.get("subcases"):
        a.update(next(iter(c["subcases"].values())).get("attrs", {}))
    return {k: v for k, v in a.items() if v != "unknown"}

def dump(x):
    return x.model_dump(mode="json")

vocab = {k: [v for v in a["values"] if v != "unknown"] for k, a in g["attributes"].items()}
for cid, fname in [("D01", "fake-d01.json"), ("H04", "fake-h04.json")]:
    attrs = attrs_of(cid)
    a = assess(attrs)
    old = json.loads((fe / fname).read_text())
    whatif = {}
    for q in a.questions:
        if q.kind != "method":
            continue
        whatif[q.attribute] = {v: dump(assess({**attrs, q.attribute: v})) for v in vocab[q.attribute]}
    reasoning = {k: v for k, v in old["reasoning"].items() if k not in ("recommendation", "questions")}
    fake = {
        "_note": f"FAKE for the screen. assessment = output of engine.gates (night state 18.10) on the golden "
                 f"attributes of {cid} (written by hand, not a live extraction). reasoning = placeholder C7 texts. "
                 f"_fake_whatif = engine output per answer, read only by the fake recompute.",
        "schema_version": "0.2",
        "case_id": old["case_id"],
        "language": old["language"],
        "summary": old["summary"],
        "attributes": [{"name": k, "value": str(v), "status": "known", "quote": None} for k, v in attrs.items()],
        "assessment": dump(a),
        "reasoning": reasoning,
        "expert_flags": old.get("expert_flags", []),
        "changes": [],
        "meta": {"model": "fake", "generated_at": "2026-10-18T08:00:00Z", "rules_version": a.rules_version,
                 "kb_version": "draft", "recomputed": False},
        "_fake_whatif": whatif,
    }
    (fe / fname).write_text(json.dumps(fake, ensure_ascii=False, indent=1) + "\n")
    print(cid, "selected", a.selected, a.decision_status, "| q:", [(q.attribute, q.strength, q.forced) for q in a.questions],
          "| labs:", [q.attribute for q in a.lab_checks], "| whatif:", {k: len(v) for k, v in whatif.items()},
          "| trace", len(a.trace), "| size", (fe / fname).stat().st_size)

# vocabulary for the answer lists: same code as tools/make_vocab.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_vocab import build_vocab
(fe / "vocab.json").write_text(json.dumps(build_vocab(g), ensure_ascii=False, indent=1) + "\n")
print("vocab", len(vocab))
