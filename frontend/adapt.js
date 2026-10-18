// Translator: backend briefing (C8 v0.2 today, v0.3 draft, or a fake) -> one "view" for the screen.
// render.js only reads the view. When the real v0.3 contract arrives, only this file changes.
//
// v0.3 fields read here are a DRAFT taken from plan v4 (C5 MethodAssessment, C7 Reasoning):
//   decision_status {code, reason, sources}
//   assessment {excluded[], scores[], selected[], premise_flags[], questions[]}   (C5)
//   reasoning {requirements, questions[], recommendation[], measurement_concept,
//              spectral_range, risks[], feasibility_plan, sources[]}                (C7)
//   meta.completeness (0..1)
//   assessment.scores[].relations / excluded[].relations: the six compatibility relations
//   of docs/decision-model.md, each "fit" | "part" | "no" | "block" | "?"
// Every field is optional: a missing field gives null / [] and its block is hidden.

const asList = (x) => (Array.isArray(x) ? x : []);

// "S01 p.17" or {ref: "S01 p.17", quote: "..."} -> {ref, quote}
function source(s) {
  if (!s) return null;
  if (typeof s === "string") return { ref: s, quote: null };
  return { ref: s.ref ?? s.source ?? s.id ?? "", quote: s.quote ?? null };
}
function sources(x) {
  const list = Array.isArray(x) ? x : x ? [x] : [];
  return list.map(source).filter((s) => s && s.ref);
}

// "nir:diffuse reflection probe" -> {method: "nir", technique: "diffuse reflection probe"}
function splitKey(key) {
  const [method, ...rest] = String(key ?? "").split(":");
  return { method, technique: rest.join(":") || null };
}
const keyOf = (method, technique) => (technique ? `${method}:${technique}` : method);

function textBlock(x) {
  if (!x) return null;
  if (typeof x === "string") return { text: x, sources: [] };
  return x.text ? { text: x.text, sources: sources(x.sources ?? x.source) } : null;
}

// --- v0.3 draft -------------------------------------------------------------

function methodsV3(b) {
  const a = b.assessment ?? {};
  const selected = new Set(asList(a.selected));
  const recText = new Map(asList(b.reasoning?.recommendation).map((r) => [r.key, r]));
  const order = { strong: 0, possible: 1, weak: 2 };
  return asList(a.scores).map((s) => {
    const key = keyOf(s.method, s.technique);
    const rec = recText.get(key);
    return {
      key,
      method: s.method,
      technique: s.technique ?? null,
      category: s.category ?? null,            // strong | possible | weak
      score: s.score ?? null,
      selected: selected.has(key),
      matched: asList(s.matched),
      missing: asList(s.missing),
      text: rec?.text ?? null,
      sources: sources(rec?.sources ?? s.source),
      specs: null,
      criteria: [],
      claims: [],
      confidence: null,
      relations: s.relations ?? null,
    };
  })
    // selected first, then strong -> possible -> weak, then by score
    .sort((x, y) => (y.selected - x.selected) || ((order[x.category] ?? 3) - (order[y.category] ?? 3))
      || ((y.score ?? 0) - (x.score ?? 0)));
}

function questionsV3(b) {
  const strength = new Map(asList(b.assessment?.questions).map((q) => [q.attribute, q]));
  const texts = asList(b.reasoning?.questions);
  const fromText = texts.map((q, i) => {
    const s = strength.get(q.attribute) ?? {};
    return {
      id: q.id ?? `q${i + 1}`,
      text: q.text,
      why: q.why ?? null,
      priority: q.priority ?? null,
      attribute: q.attribute ?? null,
      kind: s.kind ?? q.kind ?? null,          // method | status | plan
      flips: s.flips ?? null,                  // "1/3"
      changesTo: asList(s.changes_to).map(splitKey),
      answer: q.answer ?? null,
    };
  });
  // questions found by the completeness module but not worded by step B yet
  const worded = new Set(texts.map((q) => q.attribute));
  const bare = [...strength.values()].filter((s) => !worded.has(s.attribute)).map((s, i) => ({
    id: `a${i + 1}`, text: null, why: null, priority: null, attribute: s.attribute,
    kind: s.kind ?? null, flips: s.flips ?? null, changesTo: asList(s.changes_to).map(splitKey), answer: null,
  }));
  return [...fromText, ...bare];
}

function fromV3(b) {
  const r = b.reasoning ?? {};
  const a = b.assessment ?? {};
  const plan = r.feasibility_plan ?? null;
  return {
    status: b.decision_status ? {
      code: b.decision_status.code ?? b.decision_status,
      reason: b.decision_status.reason ?? null,
      sources: sources(b.decision_status.sources),
    } : null,
    premises: asList(a.premise_flags).map((p) => ({ id: p.id ?? null, text: p.text, sources: sources(p.source ?? p.sources) })),
    requirements: r.requirements ? { stated: asList(r.requirements.stated), unknowns: asList(r.requirements.unknowns) } : null,
    questions: questionsV3(b),
    methods: methodsV3(b),
    excluded: asList(a.excluded).map((x) => ({
      method: x.method, technique: x.technique ?? null, reason: x.reason, hard: true, ruleId: x.rule_id ?? null,
      sources: sources(x.source ?? x.sources), relations: x.relations ?? null,
    })),
    concept: textBlock(r.measurement_concept),
    spectralRange: textBlock(r.spectral_range),
    risks: asList(r.risks).map((x) => (typeof x === "string" ? { text: x, severity: null, sources: [] }
      : { text: x.text, severity: x.severity ?? null, sources: sources(x.sources ?? x.source) })),
    plan: plan ? { goal: plan.goal ?? null, steps: asList(plan.steps), decisionBasis: plan.decision_basis ?? null, details: null } : null,
    sources: sources(r.sources),
  };
}

// --- v0.2 (and v0.1) --------------------------------------------------------

function fromV2(b) {
  const e = b.experiment;
  return {
    status: null,
    premises: [],
    requirements: null,
    questions: asList(b.questions).map((q) => ({
      id: q.id, text: q.text, why: q.why ?? null, priority: q.priority ?? null,
      attribute: q.attribute ?? q.feature ?? q.parameter_id ?? null, kind: null, flips: null, changesTo: [], answer: q.answer ?? null,
    })),
    methods: asList(b.methods?.ranked).map((m) => ({
      key: m.method,
      method: m.method,
      technique: null,
      category: null,
      score: m.score_total ?? null,
      selected: m.rank === 1,
      matched: [],
      missing: [],
      text: null,
      sources: [],
      specs: { mode: m.mode, range: m.spectral_range, fiber: m.fiber, probe: m.probe },
      criteria: asList(m.scores),
      claims: asList(m.claims ?? m.rationale),   // v0.2 "claims", v0.1 "rationale"
      confidence: m.confidence ?? null,
      rank: m.rank,
    })),
    excluded: asList(b.methods?.rejected).map((r) => ({
      method: r.method, technique: null, reason: r.reason, hard: Boolean(r.blocker), ruleId: r.rule_id ?? null, sources: [],
    })),
    concept: null,
    spectralRange: null,
    risks: asList(b.risks).map((x) => ({ text: x.text, severity: x.severity ?? null, sources: [] })),
    plan: e ? { goal: e.goal ?? null, steps: asList(e.steps), decisionBasis: e.success_criterion ?? null, details: e } : null,
    sources: [],
  };
}

const isV3 = (b) => Boolean(b.reasoning || b.assessment || b.decision_status);

// --- gates engine (C5.assessment / C8.assessment, contracts v0.3 GatesAssessment) -----
// {rules_version, decision_status, selected[], combinations[], rows[], premise_flags[],
//  questions[], lab_checks[], trace[], ignored_inputs?}. Recognised by assessment.rows.
// It is laid over the v0.2 / draft body: the engine decides status, rows, questions;
// the C7 texts (concept, risks, plan) stay from the body. assessment = null -> no overlay.

const isGates = (b) => Array.isArray(b.assessment?.rows);
const ROW_ORDER = { candidate: 0, needs_info: 1, excluded: 2 };
// Steps of the decision path and the effects that explain a decision (as engine/paths.py).
export const PATH_STEPS = ["Q1", "Q2", "Q3", "Q4"];
const KEY_EFFECTS = new Set(["exclude", "exclude_config", "premise_contradicted", "premise_not_supported",
  "case_insufficient", "case_outside_scope", "split_case", "cap_provisional", "support_application"]);
const FOCUS_EFFECTS = new Set(["needs_info", "risk_high", "support_physics", "fit"]);

const ruleOf = (reason) => String(reason).split(":")[0];      // "I-OPAQUE:risk" -> "I-OPAQUE"
// trace effects that speak FOR a row ("why it fits") and AGAINST it ("still to check")
const SUPPORT_EFFECTS = new Set(["support_physics", "support_application", "fit"]);
const CHECK_EFFECTS = new Set(["risk", "risk_high", "needs_info", "exclude_config"]);
// one entry per rule id, sources merged
function byRule(steps) {
  const out = new Map();
  for (const s of steps) {
    const e = out.get(s.rule_id) ?? { ruleId: s.rule_id, effect: s.effect, sources: [] };
    for (const src of asList(s.source)) if (!e.sources.includes(src)) e.sources.push(src);
    out.set(s.rule_id, e);
  }
  return [...out.values()].map((e) => ({ ...e, sources: sources(e.sources) }));
}
const effectOf = (reason) => String(reason).split(":").slice(1).join(":");

function gatesRows(a) {
  const selected = asList(a.selected);
  const trace = asList(a.trace);
  return asList(a.rows).map((r) => {
    const rank = selected.indexOf(r.row);
    const own = trace.filter((s) => s.target === r.row);
    return {
      key: r.row,
      row: r.row,
      method: r.method,
      technique: r.technique ?? null,
      rowStatus: r.status,                 // candidate | needs_info | excluded
      evidence: r.evidence ?? null,        // application | analogy | physics_only | none
      selected: rank >= 0,
      rank: rank >= 0 ? rank + 1 : null,
      risks: asList(r.risks).map((x) => ({ ruleId: ruleOf(x), high: effectOf(x) === "risk_high" })),
      needs: asList(r.reasons).filter((x) => effectOf(x) === "needs_info").map(ruleOf),
      supports: byRule(own.filter((s) => SUPPORT_EFFECTS.has(s.effect))),
      checks: byRule(own.filter((s) => CHECK_EFFECTS.has(s.effect))),
      excludedBy: own.filter((s) => s.effect === "exclude" || s.effect === "exclude_config")
        .map((s) => ({ ruleId: s.rule_id, config: s.effect === "exclude_config", sources: sources(s.source) })),
      sources: sources([...new Set(own.flatMap((s) => asList(s.source)))]),
    };
  }).sort((x, y) => ((x.rank ?? 99) - (y.rank ?? 99)) || ((ROW_ORDER[x.rowStatus] ?? 3) - (ROW_ORDER[y.rowStatus] ?? 3))
    || x.row.localeCompare(y.row));
}

// Only the steps that explain the decision; the rest is counted (same rule as engine/paths.py).
function decisionPath(a, rows) {
  const focus = new Set([...asList(a.selected), ...rows.filter((r) => r.evidence === "application").map((r) => r.row)]);
  const steps = new Map(PATH_STEPS.map((s) => [s, { step: s, shown: [], hidden: 0 }]));
  const seen = new Set();
  for (const s of asList(a.trace)) {
    const key = `${s.rule_id}|${s.target}|${s.effect}`;
    if (seen.has(key) || !steps.has(s.step)) continue;
    seen.add(key);
    const important = KEY_EFFECTS.has(s.effect) || (focus.has(s.target) && FOCUS_EFFECTS.has(s.effect));
    if (important) steps.get(s.step).shown.push({ ruleId: s.rule_id, row: s.target ?? null, effect: s.effect, sources: sources(s.source) });
    else steps.get(s.step).hidden += 1;
  }
  return [...steps.values()];
}

function gatesQuestions(a, body) {
  // C7 / v0.2 questions with an attribute keep their worded text and the answer box
  const worded = new Map(body.questions.filter((q) => q.attribute).map((q) => [q.attribute, q]));
  const used = new Set();
  const fromEngine = asList(a.questions).map((q) => {
    const w = worded.get(q.attribute);
    if (w) used.add(q.attribute);
    return {
      id: w?.id ?? `g-${q.attribute}`,
      text: w?.text ?? q.text ?? null,
      why: w?.why ?? null,
      priority: w?.priority ?? null,
      attribute: q.attribute,
      kind: q.kind,                          // method | plan
      forced: Boolean(q.forced),
      strength: typeof q.strength === "number" ? q.strength : null,
      flips: null,
      changesTo: [],
      answer: w?.answer ?? null,
      hasAnswerBox: Boolean(w),              // free text only where the contract has questions[].answer
    };
  });
  const rest = body.questions.filter((q) => !q.attribute || !used.has(q.attribute))
    .map((q) => ({ ...q, forced: false, strength: null, hasAnswerBox: true }));
  return [...fromEngine, ...rest];
}

// Step B claims are per METHOD: they go on the first (best) row of that method only, without
// repeating the same sentence, so two NIR rows do not show the same rationale twice.
function withClaims(rows, ranking) {
  const given = new Set();
  return rows.map((r) => {
    if (given.has(r.method)) return { ...r, claims: [] };
    given.add(r.method);
    const seen = new Set();
    const claims = asList(ranking.find((m) => m.method === r.method)?.claims).filter((c) => {
      const k = String(c.claim ?? "").trim().toLowerCase();
      if (!k || seen.has(k)) return false;
      seen.add(k);
      return true;
    });
    return { ...r, claims };
  });
}

function attributeList(b) {
  return asList(b.attributes).map((x) => ({
    name: x.name, value: x.value ?? null, status: x.status ?? "unknown", quote: x.quote ?? null,
  }));
}

function withGates(b, body) {
  const a = b.assessment;
  const rows = gatesRows(a);
  const ranking = body.methods;            // v0.2 ranking from rules.yaml (may be empty)
  return {
    ...body,
    status: { code: a.decision_status, reason: body.status?.reason ?? null, sources: body.status?.sources ?? [] },
    premises: asList(a.premise_flags).map((p) => ({
      id: p.rule_id ?? null, verdict: p.verdict ?? "not_supported", text: p.text, sources: sources(p.source),
    })),
    questions: gatesQuestions(a, body),
    // step B rationale (v0.2 methods.ranked[].claims) for the same method, shown on the row card
    methods: withClaims(rows.filter((r) => r.rowStatus !== "excluded"), ranking),
    excluded: rows.filter((r) => r.rowStatus === "excluded").map((r) => ({
      row: r.row, key: r.row, method: r.method, technique: r.technique, reason: null, hard: true,
      ruleId: r.excludedBy.map((x) => x.ruleId).join(", ") || null, sources: r.sources, relations: null,
    })),
    // methods.ranked is filled from gates since PR #10 (points only for display): the screen shows
    // status + row id, never points, and there is no second ranking to compare with
    ranking: [],
    divergence: null,
    combinations: asList(a.combinations),
    labChecks: asList(a.lab_checks).map((q) => ({ attribute: q.attribute, text: q.text })),
    path: decisionPath(a, rows),
    rulesVersion: a.rules_version ?? null,
    // values the engine could not read: strings or {name|attribute, value, reason}
    ignoredInputs: asList(a.ignored_inputs).map((x) => (typeof x === "string" ? { text: x }
      : { text: [x.name ?? x.attribute, x.value].filter((y) => y != null).join(" = ") || JSON.stringify(x), reason: x.reason ?? null })),
  };
}

// The six relations of docs/decision-model.md, in the order of the table there.
export const RELATIONS = ["observability", "separability", "achievability", "access", "compatibility", "verifiability"];

// Matrix "relations x candidates": recommended candidates first, ruled-out ones last.
function relationRows(body) {
  const rows = [
    ...body.methods.filter((m) => m.relations).map((m) => ({ method: m.method, technique: m.technique, excluded: false, cells: m.relations })),
    ...body.excluded.filter((x) => x.relations).map((x) => ({ method: x.method, technique: x.technique, excluded: true, cells: x.relations })),
  ];
  return rows;
}

// --- method B (C8 assessment_b + facts_b, contracts v0.4, spec spectroscopy-rules 1.2) --------
// assessment_b: {cases[]: {case_id, target, stream, headline, decision_status, methods[], questions[],
//   ranking[] (candidates with factor_contributions), excluded[], first_experiment}, aggregate_bundle,
//   premises[]}. facts_b[]: {key, value, unit, status, quote, source}. Missing fields stay empty.
const isB = (b) => Array.isArray(b.assessment_b?.cases) && b.assessment_b.cases.length > 0;
export const B_STAGES = ["Q1", "Q1b", "Q2", "Q3"];

function bFactors(cand) {
  return asList(cand?.factor_contributions).map((f) => ({
    id: f.factor_id, stage: f.stage ?? null, group: f.group ?? null, outcome: f.outcome ?? null,
    effect: typeof f.effect === "number" ? f.effect : null, note: f.note ?? null,
    specificity: typeof f.specificity === "number" ? f.specificity : 0,
    sources: sources(f.source ? String(f.source).split(/;\s*/) : []),
  }));
}

function bCase(c) {
  const ranking = asList(c.ranking);
  const byId = new Map(ranking.map((r) => [r.candidate_id, r]));
  const methods = asList(c.methods).map((m) => {
    const cand = byId.get(m.best_candidate_id) ?? ranking.find((r) => r.method_id === m.method_id) ?? null;
    return {
      method: m.method_id, candidateId: m.best_candidate_id ?? null, interface: m.interface ?? cand?.interface_name ?? null,
      total: m.suitability ?? null, interval: Array.isArray(m.suitability_interval) ? m.suitability_interval : null,
      scores: m.scores ?? {}, q4: m.q4_score ?? null, confidence: m.confidence ?? null,
      critical: Boolean(m.critical_unknown), deployment: m.deployment_status ?? null,
      factors: bFactors(cand),
    };
  });
  const leader = methods[0] ?? null;
  // "why": the strongest matching factors of the leader, with their note and source (nothing invented)
  const why = leader ? leader.factors.filter((f) => f.outcome === "MATCH" && (f.effect ?? 0) > 0 && f.note)
    .sort((x, y) => (y.specificity - x.specificity) || ((y.effect ?? 0) - (x.effect ?? 0))).slice(0, 2) : [];
  return {
    id: c.case_id ?? "", target: c.target ?? null, stream: c.stream ?? null,
    headline: c.headline ?? null, status: c.decision_status ?? null, extraction: c.extraction_status ?? null,
    methods, leader, why,
    questions: asList(c.questions).map((q, i) => ({
      id: `b-${c.case_id ?? ""}-${i}`, fact: q.fact ?? null, priority: q.priority ?? null, text: q.text ?? null,
      why: q.why ?? null, ruleIds: asList(q.rule_ids),
    })),
    excluded: asList(c.excluded).map((x) => ({
      id: x.candidate_id, level: x.level ?? null,
      reasons: asList(x.excluded_by).map((e) => ({ text: e.reason ?? null, ruleId: e.rule_id ?? null, scope: e.scope ?? null })),
    })),
    experiment: c.first_experiment ?? null,
  };
}

function fromB(b) {
  const a = b.assessment_b;
  return {
    cases: a.cases.map(bCase),
    bundle: asList(a.aggregate_bundle).map((x) => ({ method: x.method_id, score: x.aggregate_bundle_score, cases: x.cases })),
    premises: asList(a.premises).map((p) => ({ id: p.rule_id ?? null, verdict: p.verdict ?? null, text: p.text, sources: sources(p.source ? String(p.source).split(/;\s*/) : []) })),
    facts: asList(b.facts_b).map((f) => ({ key: f.key, value: f.value ?? null, unit: f.unit ?? null, status: f.status ?? "unknown", quote: f.quote ?? null, source: f.source ?? null })),
    rankMode: a.rank_mode ?? null, version: a.ruleset_version ?? null,
  };
}

export function toView(b) {
  // gates assessment over a v0.2 briefing: the v0.2 body, never the v0.3 draft reader
  let base = isGates(b) ? (b.reasoning ? fromV3({ ...b, assessment: null }) : fromV2(b)) : (isV3(b) ? fromV3(b) : fromV2(b));
  // the rules.yaml ranking (v0.2 methods) stays visible next to the gates rows
  if (isGates(b) && b.reasoning && b.methods?.ranked) base = { ...base, methods: fromV2(b).methods };
  const body = {
    ranking: [], divergence: null, combinations: [], labChecks: [], path: [], rulesVersion: null, ignoredInputs: [],
    ...(isGates(b) ? withGates(b, base) : base),
  };
  body.relationRows = relationRows(body);
  return {
    engineB: isB(b) ? fromB(b) : null,
    engine: isGates(b) ? "gates" : null,
    attributes: attributeList(b),
    version: isGates(b) ? "0.3-gates" : isV3(b) ? "0.3" : (b.schema_version ?? "0.2"),
    caseId: b.case_id ?? "",
    language: b.language ?? "en",
    summary: b.summary ?? null,
    parameters: Array.isArray(b.parameters) ? b.parameters : null,   // editable table (v0.1/v0.2)
    features: b.features ?? null,                                    // v0.2 only
    completeness: typeof b.meta?.completeness === "number" ? b.meta.completeness : null,
    flags: asList(b.expert_flags),
    recomputed: Boolean(b.meta?.recomputed),
    backendChanges: asList(b.changes),
    ...body,
  };
}

// What changed between two views (after "recalculate"). Computed here, no backend needed.
export function diffViews(before, after) {
  if (!before || !after) return null;
  const old = new Map(before.methods.map((m) => [m.key, m]));
  const methods = new Map();
  for (const m of after.methods) {
    const o = old.get(m.key);
    if (!o) { methods.set(m.key, { type: "new" }); continue; }
    const rank = (x) => ({ strong: 3, possible: 2, weak: 1 }[x.category] ?? 0);
    const rowRank = (x) => ({ candidate: 2, needs_info: 1, excluded: 0 }[x.rowStatus] ?? 0);
    if (m.rowStatus && o.rowStatus && m.rowStatus !== o.rowStatus) {
      methods.set(m.key, { type: rowRank(m) > rowRank(o) ? "up" : "down", from: o.rowStatus, to: m.rowStatus, scale: "rs" });
    } else if (m.category && o.category && m.category !== o.category) {
      methods.set(m.key, { type: rank(m) > rank(o) ? "up" : "down", from: o.category, to: m.category });
    } else if (m.score != null && o.score != null && m.score !== o.score) {
      methods.set(m.key, { type: m.score > o.score ? "up" : "down", from: o.score, to: m.score });
    }
  }
  const nowExcluded = new Set(after.excluded.map((x) => keyOf(x.method, x.technique)));
  const wasExcluded = new Set(before.excluded.map((x) => keyOf(x.method, x.technique)));
  const newlyExcluded = after.excluded.filter((x) => !wasExcluded.has(keyOf(x.method, x.technique)));
  const dropped = before.methods.filter((m) => !after.methods.some((n) => n.key === m.key) && !nowExcluded.has(m.key));
  const statusChanged = (before.status?.code ?? null) !== (after.status?.code ?? null)
    ? { from: before.status?.code ?? null, to: after.status?.code ?? null } : null;
  const completeness = before.completeness != null && after.completeness != null && before.completeness !== after.completeness
    ? { from: before.completeness, to: after.completeness } : null;
  const top = (v) => v.methods.find((m) => m.selected)?.key ?? v.methods[0]?.key ?? null;
  const topChanged = top(before) !== top(after) ? { from: top(before), to: top(after) } : null;
  // selection: which methods the assessment picks for the first experiment
  const wasSelected = new Set(before.methods.filter((m) => m.selected).map((m) => m.key));
  const isSelected = new Set(after.methods.filter((m) => m.selected).map((m) => m.key));
  const newlySelected = [...isSelected].filter((k) => !wasSelected.has(k));
  const unselected = [...wasSelected].filter((k) => !isSelected.has(k) && after.methods.some((m) => m.key === k));
  const empty = !methods.size && !newlyExcluded.length && !dropped.length && !statusChanged && !completeness
    && !topChanged && !newlySelected.length && !unselected.length;
  return empty ? { empty: true, methods, unselected: [] }
    : { empty: false, methods, newlyExcluded, dropped, statusChanged, completeness, topChanged, newlySelected, unselected };
}

export { splitKey };
