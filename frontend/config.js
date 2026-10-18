// Everything that changes between "no backend", "Semyon's laptop" and "deployed".
export const CONFIG = {
  // true  = use fake-briefing.json, no backend needed
  // false = call Semyon's backend
  USE_FAKE: false,
  // Fake mode, text typed by hand (not a demo button): which test briefing to show.
  // fake-briefing.json = contract v0.2, fake-d01.json / fake-h04.json = draft v0.3.
  FAKE_FILE: "fake-briefing.json",

  // Empty so every call stays on this page's origin. The dev server and the
  // production proxy forward /api to FastAPI and strip that prefix.
  BASE_URL: "",
  ANALYZE_PATH: "/api/assessments", // C1  -> C8 or E
  RECOMPUTE_PATH: "/api/assessments/recalculate", // C1b -> C8 or E
};
