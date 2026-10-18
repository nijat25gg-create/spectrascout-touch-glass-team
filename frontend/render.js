// Draws the briefing in the AFS answer structure (Examples, section 3):
// decision status -> requirements -> questions -> recommendation -> measurement concept
// -> spectral range -> risks -> feasibility plan -> sources.
// Display only: it reads the view from adapt.js and never changes the briefing.
import { makeT } from "./i18n.js";
import { featureName, featureValueName } from "./features.js";
import { toView, RELATIONS, B_STAGES } from "./adapt.js";

// Allowed values per attribute (copy of rules/gates.yaml, see vocab.json). Set by app.js.
let VOCAB = {};
let RULES = {};
export function setVocab(v) { VOCAB = v?.attributes ?? {}; RULES = v?.rules ?? {}; }
// rule id -> its "because" text from rules/gates.yaml (via vocab.json); null if unknown
function ruleText(id) { return RULES[id]?.because ?? null; }
export function attributeValues(attr) { return VOCAB[attr]?.values ?? []; }

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };
const KIND_ORDER = { method: 0, status: 1, plan: 2 };
const MAX_CRITERION_SCORE = 3; // engine scale v0.2: 0–3 points per criterion

// --- small helpers ---------------------------------------------------------

// el("p", "summary", "Hello") -> <p class="summary">Hello</p>
// Strings are added as text, never as HTML, so data cannot inject code.
function el(tag, className, ...children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  for (const child of children.flat()) {
    if (child !== null && child !== undefined && child !== false) node.append(child);
  }
  return node;
}

function fill(id, ...nodes) {
  document.getElementById(id).replaceChildren(...nodes.flat().filter(Boolean));
}

function show(id, visible) {
  document.getElementById(id).hidden = !visible;
}

// A list of <li>, or one "Nothing listed" line when the list is empty.
function items(list, t, makeItem) {
  if (!list || list.length === 0) return [el("li", "empty", t("none"))];
  return list.map(makeItem);
}

// "parameters.temperature" -> "t-parameters-temperature" (safe as an HTML id)
function anchorId(target) {
  return "t-" + target.replace(/[^a-zA-Z0-9_]/g, "-");
}

// "nir+raman" -> "NIR + Raman"
function methodName(method, t) {
  return String(method ?? "").split("+").map((m) => t(`m.${m}`)).join(" + ");
}

// method + technique for one line: "Raman probe" already names Raman, so it stands alone
function setupName(method, technique, t) {
  const name = methodName(method, t);
  if (!technique) return name;
  return technique.toLowerCase().startsWith(name.toLowerCase()) ? technique : `${name}, ${technique}`;
}

// "sample_form" -> "Probenform" (label) or "sample form" (fallback)
function attrName(attr, t) {
  const label = t(`a.${attr}`);
  return label === `a.${attr}` ? String(attr).replace(/_/g, " ") : label;
}

// Source chips: "S01 p.17". With a quote, the chip opens it.
function sourceChips(list) {
  if (!list || list.length === 0) return null;
  return el("span", "sources", list.map((s) => {
    if (!s.quote) return el("span", "src", s.ref);
    const d = el("details", "src src-quote", el("summary", null, s.ref), el("q", null, s.quote));
    return d;
  }));
}

// --- blocks ----------------------------------------------------------------

function renderDecision(v, t) {
  const has = Boolean(v.status) || v.premises.length > 0 || Boolean(v.divergence) || v.ignoredInputs.length > 0;
  show("decision", has);
  if (!has) return;
  const code = v.status?.code ?? null;
  const label = code ? (t(`st.${code}`) === `st.${code}` ? code : t(`st.${code}`)) : null;
  const box = document.getElementById("decision");
  box.className = `decision st-${code ?? "none"}`;
  fill("decision",
    code && el("div", "decision-head",
      el("span", "decision-label", t("decision")),
      el("span", "decision-code", label)),
    v.status?.reason && el("p", "decision-reason", v.status.reason, " ", sourceChips(v.status.sources)),
    v.premises.length > 0 && el("ul", "premises",
      v.premises.map((p) => el("li", `premise-${p.verdict ?? "not_supported"}`,
        el("b", null, t(p.verdict === "contradicted" ? "premise_contradicted" : "premise_not_supported")), " ", p.text, " ",
        p.id && el("code", null, p.id), " ", sourceChips(p.sources)))),
    v.ignoredInputs.length > 0 && el("div", "ignored",
      el("b", null, `${t("ignored_inputs")}: `),
      el("span", null, v.ignoredInputs.map((x) => x.reason ? `${x.text} (${x.reason})` : x.text).join("; ")),
      " ", el("span", "ignored-hint", t("ignored_hint"))),
    v.divergence && el("p", "divergence",
      el("b", null, `${t("divergence")}: `),
      `${t("divergence_ranking")} ${methodName(v.divergence.ranking, t)} · ${t("divergence_gates")} `,
      setupName(v.divergence.gates.method, v.divergence.gates.technique, t), ". ", t("divergence_hint")));
}

function renderCompleteness(v, t) {
  show("completeness", v.completeness != null);
  if (v.completeness == null) return;
  const pct = Math.round(v.completeness * 100);
  const bar = el("div", "meter", el("i"));
  bar.firstChild.style.width = `${pct}%`;
  bar.setAttribute("role", "img");
  bar.setAttribute("aria-label", `${t("completeness")}: ${pct} %`);
  const open = v.questions.filter((q) => q.kind !== "plan").length;
  fill("completeness",
    el("div", "meter-head", el("span", null, t("completeness")), el("b", null, `${pct} %`)),
    bar,
    open > 0 && el("div", "meter-note", `${open} ${t("completeness_hint")}`));
}

function renderRequirements(v, t) {
  const r = v.requirements;
  show("requirements", Boolean(r));
  if (!r) return;
  fill("requirements",
    el("div", "req-col", el("h3", null, t("stated")), el("ul", "req known", items(r.stated, t, (x) => el("li", null, x)))),
    el("div", "req-col", el("h3", null, t("unknowns")), el("ul", "req unknown", items(r.unknowns, t, (x) => el("li", null, x)))));
}

// Section 1 of the AFS answer (skill afs-answer-and-feasibility): stated facts and key unknowns, kept
// separate and visible above the questions. From C7 requirements if sent, else from the C8 attributes
// (stated = attributes with a value; key unknowns = the attributes the method questions ask for).
function renderReqLine(v, t) {
  let stated = v.requirements?.stated ?? [];
  let unknowns = v.requirements?.unknowns ?? [];
  if (!v.requirements && v.attributes.length) {
    stated = v.attributes.filter((x) => x.status !== "unknown" && x.value != null)
      .map((x) => `${attrName(x.name, t)}: ${valueName(x.name, x.value, t)}`);
    unknowns = [...new Set(v.questions.filter((q) => q.kind === "method" && q.attribute).map((q) => attrName(q.attribute, t)))];
  }
  const has = stated.length > 0 || unknowns.length > 0;
  show("req-line", has);
  if (!has) return;
  const MAX = 6;
  const list = (xs) => xs.length > MAX ? `${xs.slice(0, MAX).join(" · ")} · +${xs.length - MAX}` : xs.join(" · ");
  fill("req-line",
    stated.length > 0 && el("p", "req-row req-stated", el("b", null, `${t("stated")}: `), list(stated)),
    unknowns.length > 0 && el("p", "req-row req-unknown", el("b", null, `${t("unknowns")}: `), list(unknowns)));
}

// Parameters exist in v0.1/v0.2 only. Editable: the expert fixes values before recalculating.
export const UNIT_PARAMS = {
  temperature: { prefix: "", suffix: "°C" },
  pressure: { prefix: "", suffix: "bar" },
  distance_to_instrument: { prefix: "", suffix: "m" },
  water_content: { prefix: "", suffix: "%" },
  required_accuracy: { prefix: "±", suffix: "%" },
};

// "40–80 °C (typisch …)" -> "40–80"; text without a number -> ""
function numberPart(value) {
  const match = (value ?? "").match(/[\d.,]+(?:\s*[–-]\s*[\d.,]+)?/);
  return match ? match[0] : "";
}

function valueEditor(p, t) {
  const unit = UNIT_PARAMS[p.id];
  if (!unit) {
    const box = el("textarea", "param-input");
    box.rows = 1;
    box.value = p.value ?? "";
    box.placeholder = "—";
    box.dataset.paramId = p.id;
    box.setAttribute("aria-label", t(`p.${p.id}`));
    return el("div", "no-print", box);
  }
  const box = el("input", "param-input param-number");
  box.inputMode = "decimal";
  box.value = numberPart(p.value);
  box.placeholder = "—";
  box.dataset.paramId = p.id;
  box.setAttribute("aria-label", `${t(`p.${p.id}`)} (${unit.suffix})`);
  const extra = p.source !== "expert_edit" && p.value && p.value.trim() !== `${unit.prefix}${box.value} ${unit.suffix}`;
  return el("div", "no-print",
    el("div", "unit-field", unit.prefix && el("span", "unit", unit.prefix), box, el("span", "unit", unit.suffix)),
    extra && el("div", "param-hint", p.value));
}

function renderParameters(v, t, flagged) {
  show("parameters-block", Boolean(v.parameters));
  if (!v.parameters) return;
  const counts = { known: 0, assumed: 0, unknown: 0 };
  for (const p of v.parameters) counts[p.status] = (counts[p.status] ?? 0) + 1;
  fill("param-stats",
    ...["known", "assumed", "unknown"].map((s) => el("span", `chip ${s}`, `${t(s)} ${counts[s]}`)));

  const head = el("tr", null,
    el("th", null, t("col_parameter")), el("th", null, t("col_value")),
    el("th", null, t("col_status")), el("th", null, t("col_quote")));
  const rows = v.parameters.map((p) => {
    const target = `parameters.${p.id}`;
    const row = el("tr", `status-${p.status}`,
      el("td", null, t(`p.${p.id}`), flagged.has(target) && el("span", "flag", " ⚑"),
        p.source === "expert_edit" && el("span", "edited", t("edited"))),
      el("td", null, valueEditor(p, t), el("span", "param-print print-only", p.value ?? "—")),
      el("td", "status", t(p.status)),
      el("td", "quote", p.evidence_quote ? `„${p.evidence_quote}“` : "—"));
    row.id = anchorId(target);
    return row;
  });
  fill("parameters", el("thead", null, head), el("tbody", null, ...rows));

  // the 12 v0.2 features are replaced by the gates attributes when those are present
  document.getElementById("features-block").hidden = !v.features || v.engine === "gates";
  fill("features", ...Object.entries(v.features ?? {}).map(([feature, f]) =>
    el("div", `feature status-${f.status}`,
      el("span", "feature-name", featureName(feature, v.language)),
      el("span", "feature-value", featureValueName(feature, f.value, v.language)),
      el("span", "status", t(f.status)))));
}

function questionSort(a, b) {
  const k = (KIND_ORDER[a.kind] ?? 3) - (KIND_ORDER[b.kind] ?? 3);
  if (k) return k;
  return (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3);
}

function renderQuestions(v, t) {
  const all = [...v.questions].sort(questionSort);
  // gates: plan questions never change the method -> one compact list under the deciding ones,
  // without an answer list (the free-text box stays where step B asked the question)
  const compactPlan = v.engine === "gates";
  const deciding = compactPlan ? all.filter((q) => q.kind !== "plan") : all;
  const plan = compactPlan ? all.filter((q) => q.kind === "plan") : [];
  const fullItem = (q) => {
    const [n, m] = String(q.flips ?? "").split("/");
    return el("li", `prio-${q.priority ?? "none"} q-kind-${q.kind ?? "none"}`,
      el("div", "q-tags",
        q.forced && el("span", "kind kind-forced", t("forced")),
        q.kind && el("span", `kind kind-${q.kind}`, t(`kind_${q.kind}`)),
        q.strength != null && el("span", "q-strength", `${Math.round(q.strength * 100)} % ${t("strength")}`),
        q.priority && el("span", "prio", t(q.priority)),
        q.attribute && el("span", "q-attr", attrName(q.attribute, t))),
      el("div", "q-text", q.text ?? attrName(q.attribute, t)),
      q.why && el("div", "why", `${t("why")}: ${q.why}`),
      (q.flips || q.changesTo.length > 0) && el("div", "q-impact",
        q.flips && m && `${n} ${t("of")} ${m} ${t("answers_change")}`,
        q.changesTo.length > 0 && el("span", "q-then",
          `${q.flips ? " · " : ""}${t("then")}: `,
          el("b", null, q.changesTo.map((c) => setupName(c.method, c.technique, t)).join("; ")))),
      valuePicker(q, t),
      q.hasAnswerBox !== false && answerInput(q, t),
      q.answer && el("div", "answer-text print-only", `${t("answer")}: ${q.answer}`));
  };
  const planItem = (q) => el("li", "plan-q",
    el("span", "q-text-small", q.text ?? attrName(q.attribute, t)),
    q.hasAnswerBox !== false && answerInput(q, t),
    q.answer && el("div", "answer-text print-only", `${t("answer")}: ${q.answer}`));
  let planGroup = null;
  if (plan.length) {
    const ol = el("ol", "plan-qs", ...plan.map(planItem));
    ol.start = deciding.length + 1;
    planGroup = el("li", "plan-group", el("div", "card-label", t("kind_plan")), ol);
  }
  fill("questions", ...deciding.map(fullItem), planGroup);
}

// Gates questions: the answer is a value of the attribute (vocabulary of rules/gates.yaml).
// app.js writes it into briefing.attributes before "recalculate".
function valuePicker(q, t) {
  if (!currentView?.engine || !q.attribute) return null;
  const values = attributeValues(q.attribute);
  if (!values.length) return null;
  const now = currentView.attributes.find((x) => x.name === q.attribute);
  const select = el("select", "value-picker no-print",
    el("option", null, `— ${t("pick_value")} —`),
    ...values.map((x) => {
      const o = el("option", null, valueName(q.attribute, x, t));
      o.value = x;
      if (now && now.value === x) o.selected = true;
      return o;
    }));
  select.firstChild.value = "";
  select.dataset.attribute = q.attribute;
  select.setAttribute("aria-label", `${t("answer")}: ${attrName(q.attribute, t)}`);
  return el("div", "picker-row", el("span", "field-label", t("answer_value")), select,
    now && el("span", "picker-print print-only", valueName(q.attribute, now.value, t)));
}

// "silica_vis_nir" -> label if translated, else "silica vis nir"
function valueName(attr, value, t) {
  const key = `val.${attr}.${value}`;
  const label = t(key);
  return label === key ? String(value ?? "—").replace(/_/g, " ") : label;
}

function answerInput(q, t) {
  const input = el("input", "answer-input no-print");
  input.value = q.answer ?? "";
  input.placeholder = t("answer_placeholder");
  input.dataset.questionId = q.id;
  input.setAttribute("aria-label", `${t("answer")}: ${q.text ?? q.attribute}`);
  return input;
}

function changeBadge(change, t) {
  if (!change) return null;
  if (change.type === "new") return el("span", "delta delta-up", t("delta_new"));
  const arrow = change.type === "up" ? "▲" : "▼";
  const pre = change.scale === "rs" ? "rs_" : "cat_";
  const from = typeof change.from === "string" ? t(`${pre}${change.from}`) : change.from;
  const to = typeof change.to === "string" ? t(`${pre}${change.to}`) : change.to;
  return el("span", `delta delta-${change.type}`, `${arrow} ${from} → ${to}`);
}

function methodCard(m, index, t, flagged, change, wasDropped) {
  if (m.rowStatus) return gatesCard(m, t, change, wasDropped);
  const target = `methods.ranked[${index}]`;
  const criteria = m.criteria.map((s) => {
    const percent = Math.max(0, Math.min(100, (s.score / MAX_CRITERION_SCORE) * 100));
    const bar = el("div", "bar", el("i"));
    bar.firstChild.style.width = `${percent}%`;
    return el("div", "crit",
      el("span", null, s.criterion), bar, el("b", null, String(s.score)),
      el("span", "crit-note", s.note, s.rule_id && " ", s.rule_id && el("code", null, s.rule_id)));
  });
  const claims = m.claims.map((c) => claimItem(c, t));

  // v0.3: category word instead of a bare number (plan v4, decision 2)
  const badge = m.category
    ? el("div", `cat cat-${m.category}`, t(`cat_${m.category}`))
    : el("div", "score", String(m.score ?? "–"), el("small", null, t("points")));

  const card = el("article", `method${m.selected ? " is-selected" : ""}${change ? " has-change" : ""}`,
    badge,
    el("div", "method-body",
      el("h3", null,
        m.rank ? `#${m.rank} ` : "", methodName(m.method, t),
        m.technique && el("span", "technique", ` · ${m.technique}`),
        m.confidence && el("span", `conf conf-${m.confidence}`, ` ${t("confidence")}: ${t(m.confidence)}`),
        m.selected && m.category && el("span", "chip selected-chip", t("selected")),
        wasDropped && el("span", "delta delta-down", t("unselected")),
        flagged.has(target) && el("span", "flag", " ⚑"),
        changeBadge(change, t)),
      m.text && el("p", "method-text", m.text, " ", sourceChips(m.sources)),
      !m.text && m.sources.length > 0 && el("p", "method-text", sourceChips(m.sources)),
      (m.matched.length > 0 || m.missing.length > 0) && el("div", "attrs",
        m.matched.map((a) => el("span", "attr attr-ok", `✓ ${attrName(a, t)}`)),
        m.missing.map((a) => el("span", "attr attr-missing", `? ${attrName(a, t)}`))),
      m.specs && el("dl", "specs",
        el("dt", null, t("mode")), el("dd", null, t(`mode.${m.specs.mode}`)),
        el("dt", null, t("range")), el("dd", null, m.specs.range),
        el("dt", null, t("fiber")), el("dd", null, m.specs.fiber),
        el("dt", null, t("probe")), el("dd", null, m.specs.probe)),
      ...criteria,
      claims.length > 0 && el("ul", "claims", ...claims)));
  card.id = anchorId(target);
  return card;
}

// Step B claim: text, AFS source as a chip (C7 claims[].source), kb card unless "afs-source"
function claimItem(c, t) {
  const src = c.source ? sourceChips([{ ref: c.source, quote: null }]) : null;
  const card = c.kb_card && c.kb_card !== "afs-source" ? el("code", null, c.kb_card) : null;
  return el("li", "claim", c.claim, " ", src, " ", card);
}

// One catalog row of the gates engine: status, AFS evidence, risks and open points, sources.
function gatesCard(m, t, change, wasDropped) {
  const why = m.supports.filter((x) => ruleText(x.ruleId));
  const check = m.checks;
  const card = el("article", `method gates-row rs-${m.rowStatus}${m.selected ? " is-selected" : ""}${change ? " has-change" : ""}`,
    el("div", `cat rs rs-${m.rowStatus}`, m.rank ? `#${m.rank}` : "", el("small", null, t(`rs_${m.rowStatus}`))),
    el("div", "method-body",
      el("h3", null, setupName(m.method, m.technique, t), " ", el("code", "row-id", m.row),
        wasDropped && el("span", "delta delta-down", t("unselected")),
        changeBadge(change, t)),
      m.evidence && el("div", "attrs", el("span", `attr ev ev-${m.evidence}`, t(`ev_${m.evidence}`))),
      // why it fits: the engine rules that supported this row (text from rules/gates.yaml) + step B claims
      (why.length > 0 || m.claims?.length > 0) && el("div", "why-fits",
        el("div", "card-label why-label", t("why_fits")),
        el("ul", "why-list",
          ...why.map((x) => el("li", null, ruleText(x.ruleId), " ", sourceChips(x.sources), " ", el("code", "rule-id", x.ruleId))),
          ...(m.claims ?? []).map((c) => claimItem(c, t)))),
      // still to check: risks and open points of this row
      check.length > 0 && el("div", "still-check",
        el("div", "card-label check-label", t("still_check")),
        el("ul", "check-list", ...check.map((x) => el("li", `eff-${x.effect}`,
          el("span", `chip check-chip check-${x.effect}`, t(`eff_${x.effect}`)), " ",
          ruleText(x.ruleId) ?? "", " ", sourceChips(x.sources), " ", el("code", "rule-id", x.ruleId)))))));
  card.id = anchorId(`rows.${m.row}`);
  return card;
}

// Catalog rows that are not selected: one compact line each (status, evidence, open points).
function gatesLine(m, t, change) {
  const li = el("li", `gates-line rs-${m.rowStatus}${change ? " has-change" : ""}`,
    el("span", `chip rs-chip rs-${m.rowStatus}`, t(`rs_${m.rowStatus}`)), " ",
    el("b", null, setupName(m.method, m.technique, t)), " ", el("code", "row-id", m.row), " ",
    m.evidence && el("span", `attr ev ev-${m.evidence}`, t(`ev_${m.evidence}`)), " ",
    ...m.risks.filter((r) => r.high).map((r) => el("span", "attr attr-risk-high", `⚠ ${r.ruleId}`)),
    ...m.needs.map((id) => el("span", "attr attr-missing", `? ${id}`)),
    ...m.excludedBy.filter((x) => x.config).map((x) => el("span", "attr attr-risk-high", `⛔ ${t("config_excluded")}: ${x.ruleId}`)),
    changeBadge(change, t));
  li.id = anchorId(`rows.${m.row}`);
  return li;
}

function renderMethods(v, t, flagged, diff) {
  const unselected = new Set(diff?.unselected ?? []);
  let others = [];
  if (v.engine === "gates") {
    const top = v.methods.filter((m) => m.selected);
    others = v.methods.filter((m) => !m.selected);
    fill("ranked",
      ...(top.length ? top.map((m, i) => methodCard(m, i, t, flagged, diff?.methods?.get(m.key), false))
        : [el("p", "empty", t("none_selected"))]));
    fill("others", others.length > 0 && el("ul", "plain gates-lines", ...others.map((m) => gatesLine(m, t, diff?.methods?.get(m.key)))));
  } else {
    fill("others");
    fill("ranked", ...(v.methods.length ? v.methods.map((m, i) => methodCard(m, i, t, flagged, diff?.methods?.get(m.key), unselected.has(m.key)))
      : [el("p", "empty", t("none"))]));
  }
  // folded block "other options": other rows + ruled out; nothing to show = no block (no empty "why not")
  const count = others.length + v.excluded.length;
  show("others-block", count > 0 || v.ranking.length > 0);
  fill("others-title", `${t("other_options")} (${count})`);
  fill("rejected", ...v.excluded.map((x) =>
    el("li", x.hard ? "is-hard" : null,
      el("b", null, methodName(x.method, t)),
      x.technique && el("span", "technique", ` · ${x.technique}`), " ",
      x.row ? el("span", "chip rs-chip rs-excluded", t("rs_excluded"))
        : el("span", x.hard ? "chip unknown" : "chip", x.hard ? t("hard_rule") : t("low_score")),
      el("div", null, x.reason, " ", sourceChips(x.sources)),
      x.ruleId && el("code", null, x.ruleId))));
  // gates on screen: the rules.yaml points ranking is shown next to it, not as the decision
  show("ranking-block", v.ranking.length > 0);
  fill("ranking", ...v.ranking.map((m) => el("li", null,
    el("b", null, methodName(m.method, t)), " ", el("span", "score-inline", `${m.score ?? "–"} ${t("points")}`))));
}

// Lab checks: done on samples in step 0 of the plan, never asked to the client (AFS ref D01).
function renderLabChecks(v, t) {
  show("labchecks-block", v.labChecks.length > 0);
  fill("labchecks", ...v.labChecks.map((c) => el("li", null, c.text ?? attrName(c.attribute, t))));
}

// Decision path Q1 -> Q4 from the engine trace: rule, effect, row, source.
function renderPath(v, t) {
  const has = v.path.some((s) => s.shown.length || s.hidden);
  show("path-block", has);
  if (!has) return;
  const label = (row) => {
    const r = [...v.methods, ...v.excluded].find((x) => x.row === row || x.key === row);
    return r ? setupName(r.method, r.technique, t) : row;
  };
  fill("path", ...v.path.map((s) => el("li", `path-step${s.shown.length ? "" : " is-quiet"}`,
    el("div", "path-head", el("b", null, `${s.step} `), t(`path_${s.step}`),
      s.hidden > 0 && el("span", "path-hidden", ` · +${s.hidden} ${t("path_hidden")}`)),
    s.shown.length > 0 && el("ul", "path-items", ...s.shown.map((x) => el("li", `eff eff-${x.effect}`,
      el("code", null, x.ruleId), " ",
      el("span", "eff-word", t(`eff_${x.effect}`) === `eff_${x.effect}` ? x.effect : t(`eff_${x.effect}`)),
      x.row && el("span", "path-row", ` → ${label(x.row)} (${x.row})`), " ", sourceChips(x.sources)))))),
  el("li", "path-step path-end", el("div", "path-head", el("b", null, "→ "), t("decision"), ": ",
    t(`st.${v.status?.code}`), v.methods.some((m) => m.selected)
      && ` · ${v.methods.filter((m) => m.selected).map((m) => m.row).join(", ")}`)));
}

// Folded tab "parameters and attributes": a short count in its title; hidden when it holds nothing.
function renderParamsTabNote(v, t) {
  const parts = [];
  if (v.engineB?.facts.length) parts.push(`${v.engineB.facts.length} ${t("b_facts")}`);
  else if (v.parameters) parts.push(`${v.parameters.length} ${t("parameters")}`);
  if (v.attributes.length && !v.engineB) parts.push(`${v.attributes.length} ${t("attributes")}`);
  show("params-tab", parts.length > 0 || Boolean(v.requirements));
  fill("params-tab-note", parts.length ? `· ${parts.join(" · ")}` : "");
}

// Attributes of the request (C3/C8 v0.3): value · status · quote.
function renderAttributes(v, t) {
  show("attributes-block", v.attributes.length > 0);
  if (!v.attributes.length) return;
  const head = el("tr", null, el("th", null, t("col_attribute")), el("th", null, t("col_value")),
    el("th", null, t("col_status")), el("th", null, t("col_quote")));
  const row = (x) => el("tr", `status-${x.status}`,
    el("td", null, attrName(x.name, t), " ", el("code", "attr-key", x.name)),
    el("td", null, x.value == null ? "—" : valueName(x.name, x.value, t)),
    el("td", "status", t(x.status)),
    el("td", "quote", x.quote ? `„${x.quote}“` : "—"));
  const known = v.attributes.filter((x) => x.status !== "unknown");
  const unknown = v.attributes.filter((x) => x.status === "unknown");
  fill("attributes", el("thead", null, head), el("tbody", null, ...known.map(row)));
  fill("attributes-unknown", unknown.length > 0 && el("details", "unknown-attrs",
    el("summary", null, `${t("unknown_attrs")} (${unknown.length})`),
    el("p", "unknown-list", unknown.map((x) => attrName(x.name, t)).join(" · "))));
}

// Matrix "six relations x candidates" (docs/decision-model.md, section 2).
const VERDICTS = ["fit", "part", "no", "block", "?"];
const VERDICT_MARK = { fit: "✓", part: "◐", no: "✗", block: "⛔", "?": "?" };

function verdictCell(value, t) {
  const v = VERDICTS.includes(value) ? value : "?";
  const cls = v === "?" ? "unknown-v" : v;
  const cell = el("td", `verdict v-${cls}`, el("span", null, VERDICT_MARK[v]), el("span", "verdict-word", t(`v.${cls}`)));
  return cell;
}

function renderMatrix(v, t) {
  const rows = v.relationRows ?? [];
  show("matrix-block", rows.length > 0);
  if (!rows.length) return;
  const head = el("tr", null, el("th", null, t("candidate")),
    ...RELATIONS.map((r) => { const th = el("th", null, t(`r.${r}`)); th.title = t(`rq.${r}`); return th; }));
  const body = rows.map((row) => el("tr", row.excluded ? "is-excluded" : null,
    el("td", "cand", setupName(row.method, row.technique, t), row.excluded && el("span", "chip unknown", t("ruled_out"))),
    ...RELATIONS.map((r) => verdictCell(row.cells?.[r], t))));
  fill("matrix", el("thead", null, head), el("tbody", null, ...body));
  fill("matrix-legend", ...VERDICTS.map((x) => {
    const cls = x === "?" ? "unknown-v" : x;
    return el("span", `legend-item v-${cls}`, `${VERDICT_MARK[x]} ${t(`v.${cls}`)}`);
  }));
}

function renderConcept(v, t) {
  const blocks = [["concept", v.concept], ["spectral_range", v.spectralRange]].filter(([, b]) => b);
  show("concept-block", blocks.length > 0);
  fill("concept", ...blocks.map(([key, b]) =>
    el("div", "concept-card", el("h3", null, t(key)), el("p", null, b.text, " ", sourceChips(b.sources)))));
}

function renderPlan(v, t) {
  const p = v.plan;
  show("plan-block", Boolean(p));
  if (!p) return;
  const e = p.details; // v0.2 experiment fields
  const row = (key, value) => [el("dt", null, t(key)), el("dd", null, value || "—")];
  fill("experiment",
    p.goal && el("p", "goal", p.goal),
    e && el("dl", null,
      ...row("samples", `${e.sample_count} — ${e.sample_design}`),
      ...row("reference", e.reference_method),
      ...row("compared", (e.methods_compared ?? []).map((m) => methodName(m, t)).join(", ")),
      ...row("interferents", (e.interferents ?? []).join(", ")),
      ...row("duration", e.duration_estimate)),
    el("ol", "plan-steps", ...p.steps.map((s) => el("li", null, s))),
    p.decisionBasis && el("p", "decision-basis", el("b", null, `${t(e ? "success" : "decision_basis")}: `), p.decisionBasis));
}

function flagLabel(target, v, t) {
  if (target.startsWith("parameters.")) return t(`p.${target.slice("parameters.".length)}`);
  const match = target.match(/^methods\.ranked\[(\d+)\]$/);
  const method = match && v.methods[Number(match[1])];
  if (method) return `#${method.rank ?? Number(match[1]) + 1} ${methodName(method.method, t)}`;
  return target;
}

function renderFlags(v, t) {
  show("flags-block", v.flags.length > 0);
  fill("flags", ...v.flags.map((f) => {
    const link = el("a", null, `⚑ ${flagLabel(f.target, v, t)}`);
    link.href = `#${anchorId(f.target)}`;
    return el("li", null, link, ` — ${f.reason}`);
  }));
}

function renderChanges(diff, v, t) {
  const box = document.getElementById("changes-box");
  box.hidden = !diff;
  if (!diff) return;
  const lines = [];
  if (diff.empty) lines.push(el("li", "empty", t("no_changes")));
  else {
    const key = (k) => {
      const row = [...v.methods, ...v.excluded].find((x) => x.row === k);
      if (row) return `${setupName(row.method, row.technique, t)} (${k})`;
      const [m, ...rest] = String(k).split(":");
      return setupName(m, rest.join(":"), t);
    };
    if (diff.topChanged) lines.push(el("li", null, el("b", null, `${t("new_top")}: `), `${key(diff.topChanged.from ?? "–")} → ${key(diff.topChanged.to ?? "–")}`));
    if (diff.statusChanged) lines.push(el("li", null, el("b", null, `${t("decision")}: `), `${t(`st.${diff.statusChanged.from}`)} → ${t(`st.${diff.statusChanged.to}`)}`));
    for (const k of diff.newlySelected ?? []) if (k !== diff.topChanged?.to) lines.push(el("li", null, el("b", null, `${t("newly_selected")}: `), key(k)));
    for (const k of diff.unselected ?? []) lines.push(el("li", null, el("b", null, `${t("unselected_long")}: `), key(k)));
    for (const [k, c] of diff.methods) if (c.type !== "new") lines.push(el("li", null, `${key(k)} `, changeBadge(c, t)));
    for (const x of diff.newlyExcluded) lines.push(el("li", null, el("b", null, `${t("newly_excluded")}: `), setupName(x.method, x.technique, t)));
    for (const m of diff.dropped) lines.push(el("li", null, el("b", null, `${t("dropped")}: `), key(m.key)));
    if (diff.completeness) lines.push(el("li", null, el("b", null, `${t("completeness")}: `),
      `${Math.round(diff.completeness.from * 100)} % → ${Math.round(diff.completeness.to * 100)} %`));
  }
  for (const c of v.backendChanges) lines.push(el("li", null, el("code", null, c.field), ` ${c.before ?? "—"} → ${c.after ?? "—"}`));
  fill("changes-box", el("h2", null, t("changes")), el("ul", "plain changes", ...lines));
}

// --- method B ------------------------------------------------------------------
// One screen per Case (tabs when the request splits, e.g. fat + protein): headline, methods with
// Q1/Q1b/Q2/Q3 (0-9), suitability of 36 with interval, Q4 (0-3), confidence, critical question;
// questions (high/medium + why), premises, ruled out, decision path by factors, facts table.
let activeCase = 0;
const methodLabel = (id, t) => methodName(String(id ?? "").toLowerCase(), t);
const factLabel = (key) => String(key ?? "").split(".").map((p) => p.replace(/_/g, " ")).join(" · ");

function bScoreBar(label, value, max) {
  const pct = Math.max(0, Math.min(100, ((value ?? 0) / max) * 100));
  const bar = el("div", "bar", el("i"));
  bar.firstChild.style.width = `${pct}%`;
  return el("div", "b-score", el("span", "b-score-label", label), bar, el("b", null, value ?? "–"), el("small", null, `/${max}`));
}

function bMethodCard(m, i, t) {
  const iv = m.interval ? `[${m.interval[0]}–${m.interval[1]}]` : null;
  return el("article", `method b-card${i === 0 ? " is-selected" : ""}`,
    el("div", "b-total",
      el("div", "b-rank", `#${i + 1}`),
      el("div", "b-sum", el("b", null, m.total ?? "–"), el("small", null, "/36")),
      iv && el("div", "b-interval", `${t("b_interval")} ${iv}`)),
    el("div", "method-body",
      el("h3", null, methodLabel(m.method, t), m.interface && el("span", "technique", ` · ${m.interface}`)),
      el("div", "attrs",
        m.confidence && el("span", `attr conf-chip conf-${m.confidence}`, `${t("confidence")}: ${t(m.confidence)}`),
        m.critical && el("span", "attr attr-risk-high", `⚠ ${t("b_critical")}`)),
      el("div", "b-scores",
        ...B_STAGES.map((q) => bScoreBar(q, m.scores?.[q], 9)),
        bScoreBar("Q4", m.q4, 3))));
}

function renderB(v, t) {
  const B = v.engineB;
  document.getElementById("result").classList.toggle("engine-b", Boolean(B));
  show("b-view", Boolean(B));
  show("b-facts-block", Boolean(B) && B.facts.length > 0);
  if (!B) return;
  if (activeCase >= B.cases.length) activeCase = 0;
  const c = B.cases[activeCase];
  // tabs: one per Case
  show("b-tabs", B.cases.length > 1);
  fill("b-tabs", ...B.cases.map((x, i) => {
    const btn = el("button", `b-tab${i === activeCase ? " is-active" : ""}`, [x.target, x.stream].filter(Boolean).join(" · ") || x.id);
    btn.type = "button";
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", String(i === activeCase));
    btn.addEventListener("click", () => { activeCase = i; renderB(v, t); });
    return btn;
  }));
  show("b-bundle", B.bundle.length > 0 && B.cases.length > 1);
  fill("b-bundle", el("b", null, `${t("b_bundle")}: `), B.bundle.map((x) => `${methodLabel(x.method, t)} ${x.score}`).join(" · "));
  // headline: the engine's own sentence + the leading method + up to two reasons with sources
  const code = c.status;
  const label = code ? (t(`st.${code}`) === `st.${code}` ? code : t(`st.${code}`)) : null;
  fill("b-head",
    el("div", "decision-head", el("span", "decision-label", t("decision")), label && el("span", `decision-code st-${code}`, label)),
    c.headline && el("p", "b-headline", c.headline),
    c.leader && el("p", "b-leader", el("b", null, `${methodLabel(c.leader.method, t)}${c.leader.interface ? `, ${c.leader.interface}` : ""}`),
      ` · ${c.leader.total ?? "–"}/36`),
    c.why.length > 0 && el("ul", "why-list b-why", ...c.why.map((f) => el("li", null, f.note, " ", sourceChips(f.sources), " ", el("code", "rule-id", f.id)))));
  // premises (case-independent)
  show("b-premises", B.premises.length > 0);
  fill("b-premises", ...B.premises.map((p) => el("li", `premise-${p.verdict ?? "not_supported"}`,
    el("b", null, t(`b_verdict_${p.verdict}`) === `b_verdict_${p.verdict}` ? `${t("premise_not_supported")}` : t(`b_verdict_${p.verdict}`)), " ",
    p.text, " ", p.id && el("code", null, p.id), " ", sourceChips(p.sources))));
  // the first three methods as cards, the rest folded
  const TOP = 3;
  const cards = c.methods.map((m, i) => bMethodCard(m, i, t));
  fill("b-methods", ...(cards.length ? cards.slice(0, TOP) : [el("p", "empty", t("none_selected"))]),
    cards.length > TOP && el("details", "b-more", el("summary", null, `${t("b_more")} (${cards.length - TOP})`),
      el("div", "b-methods", ...cards.slice(TOP))));
  // questions
  show("b-questions-block", c.questions.length > 0);
  fill("b-questions", ...c.questions.map((q) => el("li", `prio-${q.priority ?? "none"}`,
    el("div", "q-tags", q.priority && el("span", `prio prio-${q.priority}`, t(q.priority)), q.fact && el("span", "q-attr", factLabel(q.fact))),
    el("div", "q-text", q.text ?? factLabel(q.fact)),
    q.why && el("details", "b-q-why", el("summary", null, t("why")), el("p", null, q.why), q.ruleIds.length > 0 && el("code", null, q.ruleIds.join(", "))))));
  // ruled out
  show("b-excluded", c.excluded.length > 0);
  fill("b-excluded-title", `${t("b_excluded")} (${c.excluded.length})`);
  fill("b-excluded-list", ...c.excluded.map((x) => el("li", null, el("b", null, x.id.split("|").slice(0, 2).join(" · ")), " ",
    ...x.reasons.map((r) => el("div", null, r.text, " ", r.ruleId && el("code", null, r.ruleId))))));
  // decision path of the leading candidate: factors per stage
  const factors = c.leader?.factors ?? [];
  show("b-path", factors.length > 0);
  fill("b-path-body", ...B_STAGES.map((st) => {
    const fs = factors.filter((f) => f.stage === st);
    if (!fs.length) return null;
    return el("div", "b-stage", el("h3", null, st),
      el("ul", "plain b-factors", ...fs.map((f) => el("li", `outcome-${(f.outcome ?? "").toLowerCase()}`,
        el("span", `chip b-outcome b-${(f.outcome ?? "").toLowerCase()}`, f.outcome ?? "?"), " ",
        f.effect != null && el("b", "b-effect", f.effect > 0 ? `+${f.effect}` : String(f.effect)), " ",
        f.note ?? "", " ", sourceChips(f.sources), " ", el("code", "rule-id", f.id)))));
  }));
  // facts table (tab "parameters and attributes")
  fill("b-facts", el("thead", null, el("tr", null, el("th", null, t("b_fact")), el("th", null, t("col_value")),
    el("th", null, t("b_unit")), el("th", null, t("col_status")))),
  el("tbody", null, ...B.facts.map((f, i) => {
    const input = el("input", "param-input b-fact-input no-print");
    input.value = f.value ?? "";
    input.placeholder = "—";
    input.dataset.factIndex = String(i);
    input.setAttribute("aria-label", factLabel(f.key));
    const row = el("tr", `fact-${f.status}`,
      el("td", null, factLabel(f.key)),
      el("td", null, input, el("span", "param-print print-only", f.value ?? "—")),
      el("td", "unit-cell", f.unit && f.unit !== "category" ? f.unit : ""),
      el("td", null, el("span", `chip fact-chip fact-${f.status}`, t(`fs_${f.status}`) === `fs_${f.status}` ? f.status : t(`fs_${f.status}`)),
        f.quote && el("span", "fact-quote", " „…“")));
    if (f.quote) row.title = `„${f.quote}“`;
    return row;
  })));
}

// --- public ----------------------------------------------------------------

// Translate the fixed parts of the page: [data-t] text, [data-t-placeholder].
export function applyLabels(language) {
  const t = makeT(language);
  document.documentElement.lang = language;
  for (const node of document.querySelectorAll("[data-t]")) node.textContent = t(node.dataset.t);
  for (const node of document.querySelectorAll("[data-t-placeholder]")) {
    node.placeholder = t(node.dataset.tPlaceholder);
  }
}

// b = raw briefing from the backend, language = interface language, diff = from diffViews() or null.
// Returns the view, so app.js can keep it for the next comparison.
let currentView = null;
let lastCaseId = null;
export function render(b, language, diff = null) {
  if ((b.case_id ?? null) !== lastCaseId) { activeCase = 0; lastCaseId = b.case_id ?? null; }
  const t = makeT(language);
  const v = toView(b);
  currentView = v;
  applyLabels(language);

  const flagged = new Set(v.flags.map((f) => f.target));
  fill("summary", v.summary ?? "");
  document.getElementById("recomputed-badge").hidden = !v.recomputed;
  renderChanges(diff, v, t);
  renderDecision(v, t);
  renderCompleteness(v, t);
  renderRequirements(v, t);
  renderReqLine(v, t);
  renderParameters(v, t, flagged);
  renderQuestions(v, t);
  // no method can be justified yet: the deciding questions go first (skill: insufficient information)
  document.getElementById("result").classList.toggle("q-first",
    v.engine === "gates" && !v.methods.some((m) => m.selected));
  // empty data is not drawn: no question list, no risks block
  for (const id of ["questions"]) document.getElementById(id).hidden = v.questions.length === 0;
  document.querySelector("#questions-block h2").hidden = v.questions.length === 0;
  show("risks-block", v.risks.length > 0);
  renderMethods(v, t, flagged, diff);
  renderMatrix(v, t);
  renderLabChecks(v, t);
  renderPath(v, t);
  renderAttributes(v, t);
  renderParamsTabNote(v, t);
  renderB(v, t);
  renderConcept(v, t);
  fill("risks", ...items(v.risks, t, (r) =>
    el("li", null, r.severity && el("span", `chip sev-${r.severity}`, t(r.severity)), " ", r.text, " ", sourceChips(r.sources))));
  renderPlan(v, t);
  show("sources-block", v.sources.length > 0);
  fill("sources", sourceChips(v.sources));
  renderFlags(v, t);
  const date = new Date().toLocaleDateString(language);
  fill("print-head", `SpectraScout — ${t("briefing")} ${v.caseId}, ${date}`);
  fill("case-meta", v.caseId);
  document.getElementById("result").hidden = false;
  // Copy / PDF sit right above the questions of method B (with method A they stay after its questions).
  const bar = document.getElementById("actions-bar");
  if (v.engineB) document.getElementById("b-questions-block").before(bar);
  else document.getElementById("questions-block").after(bar);
  // Recalculate is off for the submission: facts and attributes are shown read-only, answers go into the customer text.
  for (const node of document.querySelectorAll("#result input, #result select, #result textarea")) node.disabled = true;
  return v;
}

// Numbered list of the questions, method-changing ones first, for an e-mail.
export function questionsAsText(b, language = "en") {
  const t = makeT(language);
  const B = toView(b).engineB;
  if (B) {
    const c = B.cases[Math.min(activeCase, B.cases.length - 1)];
    return c.questions.map((q, i) => `${i + 1}. ${q.text ?? factLabel(q.fact)}`).join("\n");
  }
  return [...toView(b).questions]
    .sort(questionSort)
    .map((q, i) => `${i + 1}. ${q.text ?? attrName(q.attribute, t)}`)
    .join("\n");
}
