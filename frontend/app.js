// Screen state and buttons: interface language, analyze, loading, errors, PDF, copy.
import { analyze, recompute, FAKE_MODE } from "./api.js";
import { render, applyLabels, questionsAsText, UNIT_PARAMS, setVocab } from "./render.js";
import { diffViews } from "./adapt.js";
import { makeT } from "./i18n.js";
import { DEMO_GROUPS } from "./cases.js";

let current = null;       // the briefing on screen (raw, as the backend sent it)
let currentView = null;   // the same briefing as the screen sees it (adapt.js)
let lastDiff = null;      // what changed in the last recalculation
let uiLanguage = "de";    // interface language: "de" or "en"
let dirty = false;        // the expert changed something that is not recalculated yet
let demoFake = null;      // fake briefing of the chosen demo case (fake mode only)
let demoChosen = false;   // a demo button was used (so a missing fake can be explained)
let noFakeShown = false;  // the screen shows the fallback example instead of this case

const form = document.getElementById("case-form");
const textBox = document.getElementById("text");
const languageBox = document.getElementById("language"); // language of the customer text (sent in C1)
const analyzeButton = document.getElementById("analyze");
const statusLine = document.getElementById("status");
const actionStatus = document.getElementById("action-status"); // messages in the bottom bar
const recomputeButton = document.getElementById("recompute");

// The backend needs 10–30 s. These steps follow the real pipeline (step A -> rules -> step B).
const STEPS = ["step_extract", "step_score", "step_explain"];

function showStatus(text, isError = false) {
  statusLine.textContent = text;
  statusLine.classList.toggle("error", isError);
}

function showActionStatus(text, isError = false) {
  actionStatus.textContent = text;
  actionStatus.classList.toggle("error", isError);
}

function setDirty(value) {
  dirty = value;
  recomputeButton.classList.toggle("pending", dirty); // yellow frame = "please recalculate"
  showActionStatus(dirty ? makeT(uiLanguage)("unsaved") : "");
}

// --- interface language (DE | EN switch in the top bar) -----------------------

function setUiLanguage(language) {
  uiLanguage = language;
  try {
    localStorage.setItem("spectrascout-ui-language", language); // remember after reload
  } catch {
    // storage can be blocked (private window): the switch still works for this visit
  }
  for (const button of document.querySelectorAll("[data-ui-lang]")) {
    button.setAttribute("aria-pressed", String(button.dataset.uiLang === language));
  }
  if (current) currentView = render(current, language, lastDiff); // redraw with new labels
  else applyLabels(language);              // only the form and the top bar
  const note = document.getElementById("fake-note");
  note.hidden = !(current && noFakeShown);
  note.textContent = makeT(language)("fake_note");
}

for (const button of document.querySelectorAll("[data-ui-lang]")) {
  button.addEventListener("click", () => setUiLanguage(button.dataset.uiLang));
}

// --- loading progress --------------------------------------------------------

// Shows "Schritt 1/3: ...", then moves to the next step every 4 seconds.
// Returns the timer, so the caller can stop it.
function startProgress(t) {
  let step = 0;
  const show = () => showStatus(`${t("step")} ${step + 1}/${STEPS.length}: ${t(STEPS[step])}`);
  show();
  return setInterval(() => {
    step = Math.min(step + 1, STEPS.length - 1);
    show();
  }, 4000);
}

// Text for an error: the backend's message (contract E), or our own text by code.
function errorText(error, t) {
  if (error.message) return error.message;
  if (error.code === "network") return t("err_network");
  return `${t("err_unknown")} (${error.code ?? "?"})`;
}

// --- demo case buttons ---------------------------------------------------------

// AFS case texts are local only (cases.local.js, git-ignored). The path is a variable so Vite
// neither bundles nor requires it: a missing file just means no texts.
let localCases = {};
const LOCAL_FILE = "./cases.local.js";
import(/* @vite-ignore */ LOCAL_FILE)
  .then((m) => { localCases = m.LOCAL_CASES ?? {}; })
  .catch(() => {})
  .finally(buildDemoButtons);

// Rows: D01–D08, H01–H06 (AFS) and S (team). The title shows on hover.
// Only cases with a text get a button: without cases.local.js the AFS rows are not shown at all.
function buildDemoButtons() {
for (const group of DEMO_GROUPS) {
  const cases = group.cases.filter((demo) => demo.text ?? localCases[demo.id]?.text);
  if (!cases.length) continue;
  const row = document.createElement("div");
  row.className = "row demo-row";
  for (const demo of cases) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip-btn";
    button.textContent = demo.id;
    button.title = demo.title;
    button.addEventListener("click", () => {
      const local = localCases[demo.id] ?? {};
      const text = demo.text ?? local.text ?? "";
      textBox.value = text;
      // no local text: say where it comes from instead of a silent empty box
      textBox.placeholder = text ? makeT(uiLanguage)("placeholder") : makeT(uiLanguage)("local_case_missing");
      languageBox.value = demo.language;
      demoFake = demo.fake ?? local.fake ?? null;
      demoChosen = true;
      for (const b of document.querySelectorAll("#demo-cases .chip-btn")) b.setAttribute("aria-pressed", String(b === button));
    });
    row.append(button);
  }
  document.getElementById("demo-cases").append(row);
}
}

// typing by hand = no demo case any more
textBox.addEventListener("input", () => {
  textBox.placeholder = makeT(uiLanguage)("placeholder");
  demoFake = null;
  demoChosen = false;
  for (const b of document.querySelectorAll("#demo-cases .chip-btn")) b.setAttribute("aria-pressed", "false");
});

// --- analyze ---------------------------------------------------------------------

form.addEventListener("submit", async (event) => {
  event.preventDefault(); // stop the browser from reloading the page
  const t = makeT(uiLanguage);
  if (textBox.value.trim().length < 20) { // the backend needs at least 20 characters
    showStatus(uiLanguage === "de" ? "Der Text ist zu kurz. Bitte mindestens 20 Zeichen eingeben."
                                   : "The text is too short. Please enter at least 20 characters.", true);
    textBox.focus();
    return;
  }

  analyzeButton.disabled = true; // no second request while the first one runs
  const timer = startProgress(t);
  try {
    current = await analyze(textBox.value, languageBox.value, demoFake);
    lastDiff = null;
    // fake mode, demo case without its own test briefing: say so instead of confusing the expert
    noFakeShown = FAKE_MODE && demoChosen && !demoFake;
    showStatus("");
    setDirty(false);
    setUiLanguage(current.language); // show the case in its own language; the switch can change it back
  } catch (error) {
    showStatus(errorText(error, t), true);
  } finally {
    clearInterval(timer); // runs on success and on error
    analyzeButton.disabled = false;
  }
});

// --- expert edits: corrected parameter values and customer answers ----------------
// One listener for the whole result block: it reacts to every input inside it.

document.getElementById("result").addEventListener("input", (event) => {
  const input = event.target;
  const t = makeT(uiLanguage);

  if (input.dataset.paramId) {
    const p = current.parameters.find((x) => x.id === input.dataset.paramId);
    const unit = UNIT_PARAMS[p.id];
    if (unit) {
      // numbers only: digits, comma, dot, dash for ranges, spaces
      input.value = input.value.replace(/[^\d.,\s–-]/g, "");
    }
    // decimal comma (German "40,5") becomes a dot, so the backend's number -> class step reads it
    const value = unit ? input.value.trim().replace(/(\d),(\d)/g, "$1.$2") : input.value.trim();
    p.value = value ? (unit ? `${unit.prefix}${value} ${unit.suffix}` : value) : null;
    input.closest("td").querySelector(".param-hint")?.remove(); // the old backend text is replaced
    p.status = value ? "known" : "unknown";
    p.source = "expert_edit";
    // update only this row, so the cursor stays in the input
    const row = input.closest("tr");
    row.className = `status-${p.status}`;
    row.querySelector(".status").textContent = t(p.status);
    row.querySelector(".param-print").textContent = p.value ?? "—";
    if (!row.querySelector(".edited")) {
      const tag = document.createElement("span");
      tag.className = "edited";
      tag.textContent = t("edited");
      row.cells[0].append(tag);
    }
    setDirty(true);
  }

  if (input.dataset.factIndex) {
    // method B fact edited by the expert: value + status confirmed_expert; recalculate sends facts_b
    const f = current.facts_b?.[Number(input.dataset.factIndex)];
    if (f) {
      const value = input.value.trim().replace(/(\d),(\d)/g, "$1.$2");
      f.value = value || null;
      f.status = value ? "confirmed_expert" : "unknown";
      f.source = value ? "expert" : null;
      f.quote = null;
      const chip = input.closest("tr").querySelector(".fact-chip");
      chip.className = `chip fact-chip fact-${f.status}`;
      chip.textContent = makeT(uiLanguage)(`fs_${f.status}`);
      setDirty(true);
    }
  }

  if (input.dataset.attribute) {
    // gates question: the answer is a value of the attribute. It goes into briefing.attributes
    // (C8 v0.3), the backend reruns the engine from there on "recalculate".
    const name = input.dataset.attribute;
    current.attributes = current.attributes ?? [];
    const i = current.attributes.findIndex((x) => x.name === name);
    if (input.value) {
      const fact = { name, value: input.value, status: "known", quote: null };
      if (i >= 0) current.attributes[i] = fact; else current.attributes.push(fact);
    } else if (i >= 0) {
      current.attributes.splice(i, 1);
    }
    setDirty(true);
  }

  if (input.dataset.questionId) {
    // v0.2: questions[]; v0.3 draft: reasoning.questions[]
    const list = current.reasoning?.questions ?? current.questions ?? [];
    const q = list.find((x) => x.id === input.dataset.questionId);
    if (q) q.answer = input.value.trim() || null;
    setDirty(true);
  }
});

// --- recalculate ---------------------------------------------------------------------

recomputeButton.addEventListener("click", async () => {
  if (!current) return;
  const t = makeT(uiLanguage);
  recomputeButton.disabled = true;
  analyzeButton.disabled = true;
  showActionStatus(t("recomputing"));
  try {
    const before = currentView;
    current = await recompute(current);
    currentView = render(current, uiLanguage);           // first draw, to get the new view
    lastDiff = diffViews(before, currentView);
    currentView = render(current, uiLanguage, lastDiff); // again, with the changes marked
    setDirty(false);
    document.getElementById("changes-box").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    showActionStatus(errorText(error, t), true);
  } finally {
    recomputeButton.disabled = false;
    analyzeButton.disabled = false;
  }
});

// --- folded blocks -------------------------------------------------------------------

// The "parameters and attributes" tab stays as the expert left it (open or closed) across analyses.
const paramsTab = document.getElementById("params-tab");
try {
  paramsTab.open = localStorage.getItem("spectrascout-params-open") === "1";
} catch {
  // no storage: the tab starts closed
}
paramsTab.addEventListener("toggle", () => {
  try {
    localStorage.setItem("spectrascout-params-open", paramsTab.open ? "1" : "0");
  } catch {
    // no storage: nothing to remember
  }
});

// The PDF shows everything: open every folded block for printing, then restore.
let foldedBeforePrint = [];
window.addEventListener("beforeprint", () => {
  foldedBeforePrint = [...document.querySelectorAll("#result details:not([open])")];
  for (const d of foldedBeforePrint) d.open = true;
});
window.addEventListener("afterprint", () => {
  for (const d of foldedBeforePrint) d.open = false;
  foldedBeforePrint = [];
});

// --- PDF and copy -------------------------------------------------------------------

document.getElementById("pdf").addEventListener("click", () => window.print());

document.getElementById("copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(questionsAsText(current, uiLanguage));
    showActionStatus(makeT(uiLanguage)("copied"));
  } catch {
    showActionStatus(makeT(uiLanguage)("copy_failed"), true);
  }
});

// --- start -------------------------------------------------------------------------

// Attribute values for the answer lists (copy of rules/gates.yaml). Without it the lists are hidden.
fetch("./vocab.json").then((r) => (r.ok ? r.json() : null)).then((v) => {
  setVocab(v);
  if (current) currentView = render(current, uiLanguage, lastDiff);
}).catch(() => {});

let saved = null;
try {
  saved = localStorage.getItem("spectrascout-ui-language");
} catch {
  // no storage: start in German
}
setUiLanguage(saved === "en" ? "en" : "de");
