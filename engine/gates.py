"""Gates engine (v0.3 draft): attributes of the analysis request -> GatesAssessment (inside C5).

Deterministic. Same attributes -> same result. Every effect is traceable to a rule id and its
source page in rules/gates.yaml. The LLM never chooses the method.

    assess(attrs, probs=None)            -> GatesAssessment   (attrs = {name: value}, unknown omitted)
    assess_extraction(c3, probs=None)    -> GatesAssessment   (anything with v0.3 `.attributes`: C3 or C8)
    completeness_score_fn(request)       -> {"selected", "decision_status"}  (for engine.completeness)

Semantics are tested by rules/check_gates.py on eval/golden_cases.yaml (D01-D08 dev, H01-H06 test) and
by engine/test_gates.py. Chemistry is draft-unverified until Nikita confirms (AGENTS.md).

Input hygiene: attribute names outside the vocabulary and values outside an attribute's value list are
ignored (treated as unknown) and reported in result["invalid"]; None, "" and "unknown" mean unknown.
"""
import logging

if __package__:          # engine.gates (normal use)
    from .gates_loader import load_gates
else:                    # plain module, as loaded by rules/check_gates.py without pydantic
    from gates_loader import load_gates

log = logging.getLogger(__name__)

EVID_RANK = {"application": 0, "analogy": 1, "physics_only": 2, "none": 3}
LEVEL = {"low": 0, "average": 1, "high": 2}
BASIC_ATTRS = ("target_kind", "sample_form", "domain", "optical_density",   # asked when nothing is decidable
               "target_class", "quantitative")


def overlap(a: list, b: list) -> float:
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return max(0.0, hi - lo) / (a[1] - a[0])


class Evaluator:
    def __init__(self, g: dict):
        self.g = g
        self.rules = [r for r in g["rules"] if r["step"] != "OUT"]
        self.rows = g["catalog"]
        self.attr_names = list(g["attributes"])
        self.vocab = {k: {str(v) for v in a["values"]} for k, a in g["attributes"].items()}
        self.q2_ids = {r["id"] for r in self.rules if r["step"] == "Q2"}
        fo = g.get("fiber_full_overlap", 1.0)   # a number, or {default: x, <method>: y}
        self.full_overlap = {k: float(v) for k, v in fo.items()} if isinstance(fo, dict) else {"default": float(fo)}
        self.forced_text: dict = {}
        self.lab_checks: list = []
        self.forced: set = set()

    # ------------------------------------------------------------ input
    def clean(self, attrs: dict) -> tuple[dict, list]:
        """Known attribute values only; everything else is unknown (and reported)."""
        a = {k: "unknown" for k in self.attr_names}
        invalid = []
        for k, v in (attrs or {}).items():
            if v is None or v == "" or v == "unknown":
                continue
            if k not in self.vocab:
                invalid.append(f"{k}: not an attribute")
                continue
            if isinstance(v, bool) or str(v) not in self.vocab[k]:
                invalid.append(f"{k}={v!r}: not in the vocabulary")
                continue
            a[k] = str(v)
        return a, invalid

    # ------------------------------------------------------------ rule matching
    def _row_status(self, rid: str, st: dict) -> str:
        flags = st["row_flags"][rid]
        if "exclude" in flags:
            return "excluded"
        reasons = st["row_reasons"][rid]
        need_rules = [x.rsplit(":", 1)[0] for x in reasons if x.endswith(":needs_info")]
        q2_need = any(r in self.q2_ids for r in need_rules)
        other_need = any(r not in self.q2_ids for r in need_rules)
        # an AFS application of the same family covers the signal question (Q2), not interface/fiber gaps
        if other_need or (q2_need and "support_application" not in flags):
            return "needs_info"
        return "candidate"

    def _computed(self, key: str, a: dict, row: str | None, state: dict):
        if key == "sample_form_not_in_row":
            if a["sample_form"] == "unknown":
                return "unknown"
            return a["sample_form"] not in self.rows[row]["sample_types"]
        if key in ("fiber_overlap_none", "fiber_overlap_partial"):
            fib = a["existing_fiber"]
            if fib == "unknown":
                return "unknown"
            if fib == "none":
                return False
            m = self.rows[row]["method"]
            ov = overlap(self.g["methods"][m]["range_nm"], self.g["fibers"][fib]["range_nm"])
            if key == "fiber_overlap_none":
                return ov == 0
            return 0 < ov < self.full_overlap.get(m, self.full_overlap.get("default", 1.0))
        if key == "any_needs_info_on_requested":
            # the configuration the client asks to approve = the client's method WITH the client's assets:
            # it is fine only if at least one row of that method is a candidate that needs no other fiber
            m = a["client_method"]
            if m in ("unknown", "none"):
                return "unknown"
            # 18.10: a candidate without any support (evidence none) cannot be approved either
            req = [rid for rid, r in self.rows.items() if r["method"] == m]
            return not any(self._row_status(x, state) == "candidate"
                           and "exclude_config" not in state["row_flags"][x]
                           and state["row_flags"][x] & {"support_application", "support_physics"} for x in req)
        raise KeyError(key)

    def _match(self, r: dict, a: dict, row: str | None, state: dict):
        """Return 'match', 'nomatch' or 'unknown'. Guard inputs must be known and match."""
        for k, vals in (r.get("guard") or {}).items():
            if a[k] == "unknown" or a[k] not in [str(x) for x in vals]:
                return "nomatch"
        unknown = False
        for k, vals in (r.get("when") or {}).items():
            v = self._computed(k, a, row, state) if k in self.g.get("computed", {}) else a[k]
            if v == "unknown":
                unknown = True
                continue
            if v not in vals and str(v) not in [str(x) for x in vals]:
                return "nomatch"
        return "unknown" if unknown else "match"

    def run(self, attrs: dict) -> dict:
        a, invalid = self.clean(attrs if isinstance(attrs, dict) else {})
        if not isinstance(attrs, dict) and attrs:
            invalid = [f"input of type {type(attrs).__name__} ignored, expected a dict"]
        state = {
            "row_flags": {rid: set() for rid in self.rows},
            "row_reasons": {rid: [] for rid in self.rows},
            "case_effects": [],
            "fired": set(),
            "premises": {},
            "asks": [],
            "trace": [],
        }
        # row and method rules first (Q1..Q4), then case rules: case rules may read final row statuses
        ordered = sorted(self.rules, key=lambda r: (r["applies_to"] == "case", r["step"]))
        for r in ordered:
            if r["applies_to"] == "case":
                units = [None]
            elif r["applies_to"] == "method":
                units = [rid for rid, x in self.rows.items() if x["method"] in r["targets"]]
            else:
                units = [rid for rid in r["targets"] if rid in self.rows]
            for u in units:
                m = self._match(r, a, u, state)
                if m == "nomatch" or (m == "unknown" and r["on_unknown"] == "ignore"):
                    continue
                eff = r["effect"] if m == "match" else r["on_unknown"]
                state["fired"].add(r["id"])
                state["trace"].append({"step": r["step"], "rule_id": r["id"], "target": u, "effect": eff,
                                       "via_unknown": m == "unknown"})
                if r.get("ask"):
                    state["asks"].append((r["ask"]["kind"], r["ask"]["attribute"], eff, r["id"],
                                          m == "unknown", u, bool(r.get("ask_even_if_known"))))
                if m == "match" and r.get("premise"):
                    # a premise is about the client's own proposal: a row rule counts only for the client's method
                    if u is None or self.rows[u]["method"] == a["client_method"]:
                        state["premises"][r["id"]] = r["premise"]
                if eff == "premise_contradicted":
                    state["premises"][r["id"]] = "contradicted"
                elif eff == "premise_not_supported":
                    state["premises"][r["id"]] = "not_supported"
                if u is None:
                    state["case_effects"].append(eff)
                else:
                    state["row_flags"][u].add(eff)
                    state["row_reasons"][u].append(f"{r['id']}:{eff}")
        out = self._summarise(a, state)
        out["invalid"] = invalid
        if invalid:
            log.warning("gates: ignored invalid input: %s", "; ".join(invalid))
        return out

    def _summarise(self, a: dict, st: dict) -> dict:
        rows = {}
        for rid, flags in st["row_flags"].items():
            ev = ("application" if "support_application" in flags else
                  "physics_only" if "support_physics" in flags else "none")
            reasons = st["row_reasons"][rid]
            rows[rid] = {"status": self._row_status(rid, st), "evidence": ev,
                         # a configuration change (other fiber) ranks like a high risk
                         "risk_high": sum(1 for x in reasons if x.endswith(":risk_high"))
                         + (1 if "exclude_config" in flags else 0),
                         "exclude_config": "exclude_config" in flags,
                         "reasons": reasons}
        tb_keys = []   # S01 Table 1 columns that decide ties in this case (tie_break: in gates.yaml)
        for tb in self.g.get("tie_break", []):
            if all(a.get(k) in [str(x) for x in v] for k, v in (tb.get("when") or {}).items()):
                tb_keys.append((tb["column"], -1 if tb["prefer"] == "high" else 1))
        cands = sorted((rid for rid, r in rows.items() if r["status"] == "candidate" and r["evidence"] != "none"),
                       key=lambda rid: (EVID_RANK[rows[rid]["evidence"]], rows[rid]["risk_high"],
                                        sum(1 for x in rows[rid]["reasons"] if x.endswith(":risk")),
                                        *[sign * LEVEL[self.rows[rid][col]] for col, sign in tb_keys], rid))
        ce = st["case_effects"]
        if "case_outside_scope" in ce:
            status = "outside_scope"
        elif "case_insufficient" in ce or not cands:
            status = "insufficient_information"
        else:
            status = "provisional"
        top_methods = {self.rows[rid]["method"] for rid in cands[:3]}
        combos = ([c["pair"] for c in self.g["combinations"] if all(m in top_methods for m in c["pair"])]
                  if status == "provisional" else [])
        return {"status": status, "top": cands[:3], "rows": rows, "fired": st["fired"],
                "premises": st["premises"], "asks": st["asks"], "combinations": combos,
                "trace": st["trace"]}

    # ------------------------------------------------------------ questions
    def signature(self, res: dict):
        # Gadzhi: the decision = selected row(s) and case status; an exclusion that does not touch the
        # selection does not change the decision
        top = res["top"][:1] if self.g.get("question_policy", {}).get("decision") == "top1" else res["top"]
        return (tuple(top), res["status"])

    def _inputs(self) -> set:
        inputs = set()
        for r in self.rules:
            for k in list(r.get("when") or {}) + list(r.get("guard") or {}):
                if k in self.g["attributes"]:
                    inputs.add(k)
                elif k == "sample_form_not_in_row":
                    inputs.add("sample_form")
                elif k.startswith("fiber_overlap"):
                    inputs.add("existing_fiber")
                elif k == "any_needs_info_on_requested":
                    inputs.add("client_method")
        return inputs

    def questions(self, attrs: dict, res: dict, probs: dict | None = None) -> tuple[list, list, dict]:
        """Method questions = enumeration (Gadzhi) + forced asks; plan questions = plan asks.
        Side results: self.lab_checks (step 0 of the plan), self.forced (attributes asked although the
        enumeration did not select them), self.forced_text (the firing rule's more specific text).

        probs: optional {attribute: {value: p}} (Jev, without not_stated). Then strength =
        sum of p(value) over the values that change the decision (value of information);
        without probs every value counts equally (Gadzhi's "2 of 3")."""
        base = self.signature(res)
        full, _ = self.clean(attrs)
        known = {k: v for k, v in full.items() if v != "unknown"}
        qs = self.g.get("questions", {})
        pol = self.g.get("question_policy", {})
        min_strength = pol.get("min_strength", 0)
        strength, weak = {}, {}
        for k in sorted(self._inputs()):
            q = qs.get(k, {})
            if full[k] != "unknown" or q.get("kind") not in {"method", "lab_check"} or q.get("probe") is False:
                continue
            vals = [str(v) for v in self.g["attributes"][k]["values"] if v != "unknown"]
            weights = (probs or {}).get(k) if isinstance(probs, dict) else None
            if isinstance(weights, dict) and weights:
                w = {}
                for v in vals:
                    try:
                        x = float(weights.get(v, 0.0))
                    except (TypeError, ValueError):
                        x = 0.0
                    w[v] = x if x > 0 else 0.0          # negative or NaN weights count as 0
                total = sum(w.values())
                weights = {v: w[v] / total for v in vals} if total > 0 else None
            else:
                weights = None
            score = 0.0
            for v in vals:
                trial = self.signature(self.run({**known, k: v}))
                if trial == base:
                    continue
                if pol.get("ignore_outside_scope_only") and trial[1] == "outside_scope" \
                        and trial[0] == base[0]:
                    continue  # only the scope changes (e.g. 'clinical'): not a method question
                score += weights[v] if weights else 1.0 / len(vals)
            if score > 0:
                weak[k] = round(score, 4)
                if score >= min_strength:
                    strength[k] = round(score, 4)
        kind_of = lambda k: qs.get(k, {}).get("kind")
        method_q = sorted((k for k in strength if kind_of(k) == "method"), key=lambda k: (-strength[k], k))
        lab_q = sorted((k for k in strength if kind_of(k) == "lab_check"), key=lambda k: (-strength[k], k))
        # forced questions (asked even if the enumeration finds no single flip):
        #  - the case cannot be decided (case_insufficient) or a rule asks to clarify (clarify)
        #  - a case-level premise input is unknown
        #  - something blocks or weakens a row that AFS material documents for this application
        forced, forced_lab = [], []
        self.forced_text = {}
        rule_ask = {r["id"]: r["ask"]["text"] for r in self.rules if r.get("ask")}
        for kind, attr, eff, rid, via_unknown, row, even_if_known in res["asks"]:
            if kind not in {"method", "lab_check"}:
                continue
            target = forced if kind == "method" else forced_lab
            # a fact the client already gave is not asked again, unless the rule asks to clarify it
            if full[attr] != "unknown" and eff not in ("case_insufficient", "clarify") and not even_if_known:
                continue
            if eff in ("case_insufficient", "clarify") or (via_unknown and row is None):
                target.append(attr)
                self.forced_text.setdefault(attr, rule_ask.get(rid))
            elif row is not None and res["rows"][row]["evidence"] == "application" \
                    and eff in {"needs_info", "risk", "risk_high", "exclude_config"}:
                target.append(attr)
                self.forced_text.setdefault(attr, rule_ask.get(rid))
        # nothing decidable and nothing to ask: take the enumeration below the threshold, then the basic facts
        # (Gadzhi: unknown phase -> ask it first)
        if res["status"] == "insufficient_information" and not forced and not method_q:
            method_q = sorted((k for k in weak if kind_of(k) == "method"), key=lambda k: (-weak[k], k))
            strength.update({k: weak[k] for k in method_q})
        # an undecidable case always gets up to 3 questions: forced ones first, then the basic facts
        if res["status"] == "insufficient_information" and len(set(forced) | set(method_q)) < 3:
            for attr in BASIC_ATTRS:
                if len(set(forced) | set(method_q)) >= 3:
                    break
                if attr == "optical_density" and full["sample_form"] not in ("liquid", "unknown"):
                    continue  # optical density only decides the geometry for liquids
                if full[attr] == "unknown" and kind_of(attr) == "method" and attr not in forced + method_q:
                    forced.append(attr)
        self.forced = set(forced) | set(forced_lab)
        method = list(dict.fromkeys(forced + method_q))[:pol.get("max_method", 99)]
        # plan questions: unknown facts only, unless the rule asks to clarify a known class (e.g. 'hot' -> numbers)
        plan = list(dict.fromkeys(attr for kind, attr, _e, _r, _vu, _row, even_if_known in res["asks"]
                                  if kind == "plan" and (full[attr] == "unknown" or even_if_known)))
        self.lab_checks = list(dict.fromkeys(forced_lab + lab_q))  # step 0 of the plan, not the client
        return method, plan, strength


# ---------------------------------------------------------------- public API
def _question(g: dict, ev: Evaluator, attr: str, kind: str, strength: dict):
    from contracts.models import GateQuestion
    forced = attr in ev.forced and kind != "plan"
    text = (ev.forced_text.get(attr) if forced else None) or g.get("questions", {}).get(attr, {}).get("text", "")
    return GateQuestion(attribute=attr, kind=kind, strength=None if kind == "plan" else strength.get(attr),
                        forced=forced, text=text)


def assess(attrs: dict, probs: dict | None = None, g: dict | None = None):
    """-> contracts.models.GatesAssessment"""
    from contracts.models import GatesAssessment, PremiseFlag, RowResult, TraceStep
    g = g or load_gates()
    ev = Evaluator(g)
    res = ev.run(attrs)
    method_q, plan_q, strength = ev.questions(attrs, res, probs)
    rules = {r["id"]: r for r in g["rules"]}
    rows = []
    for rid, r in res["rows"].items():
        cat = g["catalog"][rid]
        rows.append(RowResult(row=rid, method=cat["method"], technique=cat["technique"], status=r["status"],
                              evidence=r["evidence"],
                              risks=[x for x in r["reasons"]
                                     if x.endswith((":risk", ":risk_high", ":exclude_config"))],
                              reasons=r["reasons"]))
    flags = [PremiseFlag(rule_id=rid, verdict=verdict, text=rules[rid]["because"], source=rules[rid]["source"])
             for rid, verdict in res["premises"].items()]
    questions = [_question(g, ev, a, "method", strength) for a in method_q] + \
                [_question(g, ev, a, "plan", strength) for a in plan_q]
    labs = [_question(g, ev, a, "lab_check", strength) for a in ev.lab_checks]
    trace = [TraceStep(step=t["step"], rule_id=t["rule_id"], target=t["target"], effect=t["effect"],
                       source=rules[t["rule_id"]]["source"]) for t in res["trace"]]
    # 18.10: rows are only 'selected' for a provisional case; insufficient / outside_scope recommend nothing
    # (res["top"] stays internal: the question signature needs it)
    selected = res["top"] if res["status"] == "provisional" else []
    return GatesAssessment(rules_version=str(g.get("version")), decision_status=res["status"],
                           selected=selected, combinations=res["combinations"], rows=rows,
                           premise_flags=flags, questions=questions, lab_checks=labs, trace=trace,
                           ignored_inputs=res["invalid"] or None)


def assess_extraction(source, probs: dict | None = None, g: dict | None = None):
    """Anything with v0.3 `.attributes` (C3 Extraction or C8 Briefing) -> GatesAssessment.
    Unknown and conflicting attributes stay unknown."""
    from llm.vocab import engine_attrs  # local import: the engine itself does not need the LLM package
    return assess(engine_attrs(getattr(source, "attributes", None)), probs, g)


# Attribute statuses that count as a fact. Both vocabularies are in use: the C3 contract (known / assumed)
# and the unified model spec §6 (stated / inferred). Everything in NOT_FACT_STATUSES stays unknown.
FACT_STATUSES = {"known", "assumed", "stated", "inferred", "explicit"}
NOT_FACT_STATUSES = {"unknown", "conflicting", "not_stated"}


def completeness_score_fn(request: dict) -> dict:
    """Adapter for Gadzhi's engine.completeness: request = {"attributes": {name: {value, status}}}
    or a flat {name: value}. Decision = selected row (top-1) + decision status, as agreed
    (AFS ref §3: method or setup). Uses only the rule pass (no question enumeration): it is called
    once per probed value.

    Status is case- and space-insensitive. known/assumed (C3) and stated/inferred (spec §6) are facts;
    unknown/conflicting/not_stated are not. A missing status with a value counts as a fact. Any other
    status is NOT dropped silently: it is returned in "ignored" (and logged), so a vocabulary mismatch
    shows up instead of turning every case into insufficient_information."""
    attrs = request.get("attributes", request) if isinstance(request, dict) else {}
    known, ignored = {}, []
    for k, v in (attrs or {}).items() if isinstance(attrs, dict) else []:
        if isinstance(v, dict):          # {name: {value, status}} (Gadzhi's format)
            value = v.get("value")
            if value in (None, "", "unknown"):
                continue
            status = v.get("status")
            status = str(status).strip().lower() if status is not None else None
            if status is None or status in FACT_STATUSES:
                known[k] = value
            elif status not in NOT_FACT_STATUSES:
                ignored.append(f"{k}: status {v.get('status')!r} is not a known status")
        elif isinstance(v, str):         # {name: value}
            known[k] = v
    res = Evaluator(load_gates()).run(known)
    ignored += res["invalid"]
    if ignored:
        log.warning("completeness_score_fn ignored: %s", "; ".join(ignored))
    return {"selected": res["top"][:1], "decision_status": res["status"], "ignored": ignored}
