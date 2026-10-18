"""
Contract checks. Run: python contracts/check_contracts.py
Exit code 0 = all good. Use it after every change to models.py or examples.

Checks:
  1. Every example validates against its Pydantic model AND its exported JSON Schema.
  2. Chain consistency: data that passes C1 -> C8 stays the same where it must.
  3. C3 and C7 are compatible with Claude structured outputs (they are sent to Claude as output schemas).
  4. Business rules: 16 parameters exactly once, every method placed once, score sums, ranks, links.
  5. Recompute path: C1b edits produce a valid C4 for the engine.
The reference assembly of C8 below is only a test oracle for the examples, not product code.
"""
import json, pathlib, sys, typing, datetime
from jsonschema import Draft202012Validator

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import models as m

EX, SC = HERE / "examples", HERE / "schemas"
errors: list[str] = []
def check(cond, msg):
    if not cond: errors.append(msg)

def load(name): return json.loads((EX / f"{name}.example.json").read_text(encoding="utf-8"))
def schema(prefix): return json.loads(next(SC.glob(f"{prefix}_*.schema.json")).read_text(encoding="utf-8"))

ex = {k: load(n) for k, n in [("C1","C1_analyze_request"),("C2","C2_extract_input"),("C3","C3_extraction"),
       ("C4","C4_score_input"),("C5","C5_scoring"),("C6","C6_explain_input"),("C7","C7_explanation"),("E","E_error_response")]}

# ---------- reference assembly (test oracle) -> C8 and C1b examples
def reference_assemble(c2, c3, c5, c7, recomputed=False, changes=None):
    rat = {r["method"]: r["claims"] for r in c7["rationale"]}
    ranked = [{**s, "claims": rat.get(s["method"], [])} for s in c5["ranked"]]
    flags = [{"target": f"parameters.{p['id']}", "reason": "Annahme, nicht vom Kunden bestätigt"}
             for p in c3["parameters"] if p["status"] == "assumed"]
    flags += [{"target": f"methods.ranked[{i}]", "reason": f"Sicherheit: {s['confidence']}"}
              for i, s in enumerate(c5["ranked"]) if s["confidence"] != "high"]
    return {"schema_version": m.SCHEMA_VERSION, "case_id": c2["case_id"], "language": c2["language"],
            "summary": c3["summary"], "parameters": c3["parameters"], "features": c3["features"],
            "questions": [{**q, "answer": None} for q in c7["questions"]],
            "methods": {"ranked": ranked, "rejected": c5["rejected"]},
            "experiment": c7["experiment"], "risks": c7["risks"], "expert_flags": flags,
            "changes": changes or [],
            "meta": {"model": "claude-sonnet-5-5", "generated_at": "2026-10-17T10:00:00Z",
                     "rules_version": c5["rules_version"], "kb_version": "kb-draft-0", "recomputed": recomputed},
            # v0.3 (optional): carried unchanged from C3 and C5 when present
            **({"attributes": c3["attributes"]} if c3.get("attributes") is not None else {}),
            **({"assessment": c5["assessment"]} if c5.get("assessment") is not None else {})}

ex["C8"] = reference_assemble(ex["C2"], ex["C3"], ex["C5"], ex["C7"])
ex["C1b"] = {"briefing": ex["C8"],
             "edits": [{"feature": "distance_class", "value": "long", "note": "Spektrometer im Technikraum, ca. 30 m"}],
             "answers": [{"question_id": "q4", "answer": "Ja, ATEX Zone 22", "feature_value": "yes"}]}
for cid, name in [("C8", "C8_briefing"), ("C1b", "C1b_recompute_request")]:
    (EX / f"{name}.example.json").write_text(json.dumps(ex[cid], ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- 1. Pydantic + JSON Schema validation
for cid, model in m.CONTRACTS.items():
    try: model.model_validate(ex[cid])
    except Exception as e: check(False, f"[1] {cid} Pydantic: {str(e).splitlines()[0]}")
    v = Draft202012Validator(schema(cid))
    for err in v.iter_errors(ex[cid]): check(False, f"[1] {cid} JSON Schema at {err.json_path}: {err.message}")
    # schema file is up to date with models.py
    fresh = model.model_json_schema(); fresh["$id"] = schema(cid)["$id"]
    check(fresh == schema(cid), f"[1] {cid} schema file is stale, run export_schemas.py")

# negative tests: contracts must reject bad data
for bad, why in [({"text": "zu kurz", "language": "de"}, "short text"),
                 ({"text": "x" * 50, "language": "fr"}, "unsupported language"),
                 ({"text": "x" * 50, "language": "de", "extra": 1}, "unknown field")]:
    try: m.AnalyzeRequest.model_validate(bad); check(False, f"[1] C1 accepted bad input: {why}")
    except Exception: pass

# ---------- 2. chain consistency
c1, c2, c3, c4, c5, c6, c7, c8 = (ex[k] for k in ["C1","C2","C3","C4","C5","C6","C7","C8"])
check(c2["text"] == c1["text"] and c2["language"] == c1["language"], "[2] C2 must carry C1 text/language unchanged")
check(c4["features"] == c3["features"], "[2] C4.features must equal C3.features")
check(c4.get("attributes") == c3.get("attributes"), "[2] C4.attributes must equal C3.attributes (v0.3)")
check(c4["case_id"] == c2["case_id"] == c6["case_id"] == c8["case_id"], "[2] case_id must stay the same along the chain")
check(c6["parameters"] == c3["parameters"] and c6["features"] == c3["features"], "[2] C6 must carry C3 data unchanged")
check(c6["scoring"] == c5, "[2] C6.scoring must equal C5")
check(c8["methods"]["rejected"] == c5["rejected"], "[2] C8 rejected must equal C5 rejected")
check([s["method"] for s in c8["methods"]["ranked"]] == [s["method"] for s in c5["ranked"]], "[2] C8 ranked order must equal C5")
check(c8.get("assessment") == c5.get("assessment"), "[2] C8.assessment must equal C5.assessment (v0.3)")
check(c8.get("attributes") == c3.get("attributes"), "[2] C8.attributes must equal C3.attributes (v0.3)")
_vocab = set(typing.get_args(m.AttributeName))
for q in c7["questions"]:
    check(q.get("attribute") is None or q["attribute"] in _vocab, f"[2] C7 question {q['id']}: attribute {q.get('attribute')!r} not in AttributeName")

# ---------- 3. structured outputs compatibility (C3, C7 go to Claude)
UNSUPPORTED = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minLength", "maxLength"}
def walk(node, path, found):
    if isinstance(node, dict):
        if node.get("type") == "object" or "properties" in node:
            if node.get("additionalProperties") is not False: found["addl"].append(path)
            req = set(node.get("required", []))
            found["optional"] += len([p for p in node.get("properties", {}) if p not in req])
        found["unions"] += 1 if "anyOf" in node else 0
        for k in UNSUPPORTED & node.keys(): found["bad"].append(f"{path}.{k}")
        if node.get("minItems", 0) > 1: found["bad"].append(f"{path}.minItems")
        for k, v in node.items(): walk(v, f"{path}.{k}", found)
    elif isinstance(node, list):
        for i, v in enumerate(node): walk(v, f"{path}[{i}]", found)
for cid in ["C3", "C7"]:
    f = {"addl": [], "optional": 0, "unions": 0, "bad": []}
    walk(schema(cid), cid, f)
    check(not f["addl"], f"[3] {cid} objects without additionalProperties:false: {f['addl'][:3]}")
    check(f["optional"] <= 24, f"[3] {cid} has {f['optional']} optional properties (limit 24)")
    check(f["unions"] <= 16, f"[3] {cid} has {f['unions']} anyOf unions (limit 16)")
    check(not f["bad"], f"[3] {cid} uses keywords Claude structured outputs reject: {f['bad']}")
    print(f"    {cid}: optional={f['optional']} unions={f['unions']}")
# v0.3: step A sends a private output model (attributes required, no jev); same limits apply
try:
    sys.path.insert(0, str(HERE.parent))
    from llm.extract import _ExtractionOutV03
    f = {"addl": [], "optional": 0, "unions": 0, "bad": []}
    walk(_ExtractionOutV03.model_json_schema(), "C3out", f)
    check(not f["addl"] and f["optional"] <= 24 and f["unions"] <= 16 and not f["bad"],
          f"[3] llm.extract._ExtractionOutV03 breaks structured-output limits: {f}")
    print(f"    C3 v0.3 output model: optional={f['optional']} unions={f['unions']}")
except ImportError as e:
    check(False, f"[3] cannot import llm.extract to check the v0.3 output model: {e}")

# ---------- 4. business rules
ids = [p["id"] for p in c3["parameters"]]
check(sorted(ids) == sorted(typing.get_args(m.ParameterId)), "[4] C3 must contain all 16 parameter ids exactly once")
for p in c3["parameters"]:
    check((p["status"] == "known") == (p["evidence_quote"] is not None) or p["status"] == "assumed",
          f"[4] {p['id']}: known needs a quote, unknown must not have one")
    check(not (p["status"] == "unknown" and p["value"] is not None), f"[4] {p['id']}: unknown must have value null")
placed = [s["method"] for s in c5["ranked"]] + [r["method"] for r in c5["rejected"]]
check(sorted(placed) == sorted(typing.get_args(m.Method)), "[4] every method must be ranked or rejected exactly once")
check([s["rank"] for s in c5["ranked"]] == list(range(1, len(c5["ranked"]) + 1)), "[4] ranks must be 1..n")
check(1 <= len(c5["ranked"]) <= 3, "[4] 1-3 ranked methods")
for s in c5["ranked"]:
    check(abs(sum(x["score"] for x in s["scores"]) - s["score_total"]) < 1e-9, f"[4] {s['method']}: score_total != sum of scores")
check(sorted(r["method"] for r in c7["rationale"]) == sorted(s["method"] for s in c5["ranked"]), "[4] C7 rationale must cover exactly the ranked methods")
check(set(c7["experiment"]["methods_compared"]) <= {s["method"] for s in c5["ranked"]}, "[4] experiment may compare only ranked methods")
pid_status = {p["id"]: p["status"] for p in c3["parameters"]}
for q in c7["questions"]:
    check(q["parameter_id"] in pid_status, f"[4] question {q['id']} refers to a parameter missing in C3")
    check(pid_status.get(q["parameter_id"]) != "known", f"[4] question {q['id']} asks about a parameter that is already known")
    if q["feature"]: check(c3["features"][q["feature"]]["status"] != "known", f"[4] question {q['id']} targets a known feature")
check(len({q["id"] for q in c7["questions"]}) == len(c7["questions"]), "[4] question ids must be unique")

# ---------- 5. recompute path
fields = m.Features.model_fields
def allowed(feature):
    inner = fields[feature].annotation.model_fields["value"].annotation
    return set(typing.get_args(inner))
feats = json.loads(json.dumps(c8["features"]))
qmap = {q["id"]: q for q in c8["questions"]}
for e in ex["C1b"]["edits"]:
    check(e["value"] in allowed(e["feature"]), f"[5] edit {e['feature']}={e['value']} is not an allowed value")
    feats[e["feature"]] = {"value": e["value"], "status": "known"}
for a in ex["C1b"]["answers"]:
    q = qmap.get(a["question_id"]); check(q is not None, f"[5] answer to unknown question {a['question_id']}")
    if q and q["feature"]:
        check(a["feature_value"] in allowed(q["feature"]), f"[5] answer {a['question_id']} value not allowed for {q['feature']}")
        feats[q["feature"]] = {"value": a["feature_value"], "status": "known"}
try: m.ScoreInput.model_validate({"case_id": c8["case_id"], "features": feats})
except Exception as e: check(False, f"[5] recompute produced invalid C4: {e}")

print("\nRESULT:", "OK, all checks passed" if not errors else f"{len(errors)} problem(s)")
for e in errors: print(" -", e)
sys.exit(1 if errors else 0)
