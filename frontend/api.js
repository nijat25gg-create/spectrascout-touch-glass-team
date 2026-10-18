// Talks to Semyon's backend. The only file that knows URLs and request formats.
import { CONFIG } from "./config.js";

// An error the screen can show. code: "network", "validation_error", ...
// message: text for the expert from contract E (may be empty).
export class ApiError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

async function postJSON(path, body) {
  let response;
  try {
    response = await fetch(CONFIG.BASE_URL + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    // fetch fails like this when the dev proxy or the backend is unreachable
    throw new ApiError("network", "");
  }
  if (!response.ok) {
    // contract E: {"error": {"code": "...", "message": "...", "details": "..."}}
    let data = null;
    try {
      data = await response.json();
    } catch {
      // body was not JSON
    }
    throw new ApiError(errorCode(data, response.status), errorMessage(data));
  }
  return response.json();
}

// Two error formats are possible:
// Hub contract E: {"error": {"code", "message", "details"}}
// FastAPI default: {"detail": "text"} or {"detail": [{"loc": [...], "msg": "..."}]}
function errorCode(data, status) {
  return data?.error?.code ?? `http_${status}`;
}

function errorMessage(data) {
  if (data?.error?.message) return data.error.message;
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail.map((e) => `${(e.loc ?? []).join(".")}: ${e.msg}`).join("; ");
  }
  return "";
}

// Fake mode: CONFIG.USE_FAKE, or "?fake" in the page address (no need to edit config.js).
export const FAKE_MODE = CONFIG.USE_FAKE || new URLSearchParams(location.search).has("fake");

// C1: {text, language} -> briefing
// fakeFile: which test briefing the fake mode returns (set by the demo case buttons).
export async function analyze(text, language, fakeFile = null) {
  if (FAKE_MODE) return fakeAnalyze(text, language, fakeFile);
  return postJSON(CONFIG.ANALYZE_PATH, { text, language });
}

// Recompute (agreed with Semyon, contract v0.1): send the whole briefing with the
// expert's answers (questions[].answer) and corrected parameters (source "expert_edit").
// The backend returns a new briefing in the same format, meta.recomputed = true.
export async function recompute(briefing) {
  if (FAKE_MODE) return fakeRecompute(briefing);
  return postJSON(CONFIG.RECOMPUTE_PATH, briefing);
}

// --- fake mode: behaves like the backend, without a backend ------------------

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const TOO_SHORT = {
  de: "Der Text ist zu kurz. Bitte mindestens 20 Zeichen eingeben.",
  en: "The text is too short. Please enter at least 20 characters.",
};

async function fakeAnalyze(text, language, fakeFile) {
  await sleep(1500);
  if (text.trim().length < 20) {
    throw new ApiError("validation_error", TOO_SHORT[language] ?? TOO_SHORT.en);
  }
  const file = fakeFile ?? CONFIG.FAKE_FILE ?? "fake-briefing.json";
  const response = await fetch(`./${file}`, { cache: "no-store" }); // always the current file
  return response.json();
}

// Pretends to be the backend, so the screen visibly changes after "Neu berechnen".
async function fakeRecompute(briefing) {
  await sleep(1000);
  const next = structuredClone(briefing); // deep copy, the old briefing stays as it was
  if (Array.isArray(next.assessment?.rows)) fakeRecomputeGates(next);
  else if (next.reasoning || next.assessment) fakeRecomputeV3(next);
  else fakeRecomputeV2(next);
  next.meta = { ...next.meta, recomputed: true, generated_at: new Date().toISOString() };
  return next;
}

// gates fake: the test file carries the real engine output for each single answer
// (_fake_whatif[attribute][value], made by tools/make_gates_fakes.py). The first answered
// attribute in question order is used. The real backend reruns the engine on all attributes.
function fakeRecomputeGates(next) {
  const whatif = next._fake_whatif ?? {};
  const given = new Map((next.attributes ?? []).map((x) => [x.name, x.value]));
  const attr = (next.assessment.questions ?? []).map((q) => q.attribute)
    .find((name) => whatif[name] && whatif[name][given.get(name)]);
  if (!attr) return;
  next.assessment = structuredClone(whatif[attr][given.get(attr)]);
  delete whatif[attr];
}

// v0.2: copy answers into their parameters and move the top score a little.
function fakeRecomputeV2(next) {
  for (const q of next.questions ?? []) {
    const p = (next.parameters ?? []).find((x) => x.id === q.parameter_id);
    if (q.answer && p) {
      p.value = q.answer;
      p.status = "known";
      p.source = "expert_edit";
    }
  }
  const top = next.methods?.ranked?.[0];
  if (top) top.score_total = Math.min(10, top.score_total + 0.5);
}

// v0.3 draft: answered questions disappear and completeness rises. An answered
// "method" question switches the selection to its changes_to (fake only: the real
// backend decides from the answer itself).
function fakeRecomputeV3(next) {
  const r = next.reasoning ?? {};
  const a = next.assessment ?? {};
  const answered = (r.questions ?? []).filter((q) => q.answer);
  const answeredAttrs = new Set(answered.map((q) => q.attribute));
  // Only the strongest answered method question counts (the first one in the list),
  // and only once: two answers pointing to different methods must not cancel out.
  const flip = (a.questions ?? []).find((q) =>
    answeredAttrs.has(q.attribute) && q.kind === "method" && q.changes_to?.length);
  if (flip) {
    a.selected = [...flip.changes_to];
    for (const s of a.scores ?? []) {
      const key = s.technique ? `${s.method}:${s.technique}` : s.method;
      if (flip.changes_to.includes(key)) { s.category = "strong"; s.score = Math.min(100, (s.score ?? 0) + 15); }
      else if (s.category === "strong") { s.category = "possible"; s.score = Math.max(0, (s.score ?? 0) - 10); }
    }
  }
  r.questions = (r.questions ?? []).filter((q) => !q.answer);
  a.questions = (a.questions ?? []).filter((q) => !answeredAttrs.has(q.attribute));
  if (next.meta && typeof next.meta.completeness === "number") {
    next.meta.completeness = Math.min(0.95, next.meta.completeness + 0.12 * answered.length);
  }
}
