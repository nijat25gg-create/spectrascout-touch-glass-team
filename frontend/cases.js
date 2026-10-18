// Demo cases: one click fills the text box, so nobody types during the demo.
// D01–D08 and H01–H06 are AFS material: the repository keeps only id and title. Their texts
// (and the D01/H04 test briefings) live in frontend/cases.local.js, which is git-ignored
// (template: cases.local.example.js). Without it the button leaves the box empty with a hint.
// The S row is the team's own material and stays in the repository.
// `fake` = which test briefing the fake mode shows for this case.
export const DEMO_GROUPS = [
  {
    label: "D",
    cases: [
      {
        id: "D01", title: "Blend potency in a tablet press feed frame", language: "en",
      },
      {
        id: "D02", title: "Fat and protein monitoring in opaque dairy product", language: "en",
      },
      {
        id: "D03", title: "A clear whey stream before concentration", language: "en",
      },
      {
        id: "D04", title: "Glucose and lactate trends in an aqueous bioprocess", language: "en",
      },
      {
        id: "D05", title: "Biomass related monitoring during yeast fermentation", language: "en",
      },
      {
        id: "D06", title: "Water content in a petroleum stream", language: "en",
      },
      {
        id: "D07", title: "API concentration during hot polymer extrusion", language: "en",
      },
      {
        id: "D08", title: "Local measurements of heterogeneous model tissues", language: "en",
      },
    ],
  },
  {
    label: "H",
    cases: [
      {
        id: "H01", title: "A new formulation after an existing NIR pilot", language: "en",
      },
      {
        id: "H02", title: "Composition monitoring across two dairy streams", language: "en",
      },
      {
        id: "H03", title: "A fluorescence instrument requested for glucose and viable biomass", language: "en",
      },
      {
        id: "H04", title: "Reuse of a silica link for petroleum MIR ATR", language: "en",
      },
      {
        id: "H05", title: "An undefined off specification liquid", language: "en",
      },
      {
        id: "H06", title: "A research sensor requested for immediate surgical use", language: "en",
      },
    ],
  },
  {
    // Synthetic cases of the team (not AFS material, may be shown and committed). The briefings are
    // C8 v0.3 from Nidzhat (18.10): gates `assessment` + step B texts simulated with our prompts.
    // The customer texts are not in the briefings: the button text is the briefing summary.
    label: "S",
    cases: [
      {
        id: "S02", title: "Ethanol in beer fermentation, MIR ATR from a brochure (synthetic)", language: "en", fake: "fake-s02.json",
        text: "The customer wants to monitor ethanol during beer fermentation with MIR ATR and asks AFS to approve an analyzer in a control room in another building, based on a brochure claim of a 50 m fiber.",
      },
      {
        id: "S04", title: "Fat and protein in yogurt, two recipes (synthetic)", language: "de", fake: "fake-s04.json",
        text: "Der Kunde möchte in der Joghurtproduktion Fett und Protein in zwei Rezepturen (Natur und Frucht) überwachen und wünscht zunächst eine Pilotstudie und einen Vergleich geeigneter Methoden.",
      },
      {
        id: "Feuchte", title: "Residual moisture of a pharma powder (contracts example)", language: "de", fake: "fake-moisture.json",
        text: "Wir trocknen ein pharmazeutisches Pulver im Wirbelschichttrockner und wollen die Restfeuchte inline messen, Zielbereich etwa 1–5 %. Aktuell ziehen wir stündlich Proben für Karl-Fischer-Titration.",
      },
    ],
  },
];

export const DEMO_CASES = DEMO_GROUPS.flatMap((g) => g.cases);
