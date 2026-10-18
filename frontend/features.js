// The 12 features the rules engine scores on (contract v0.2, briefing.features).
// DRAFT: values and labels are taken from the C8 example. Replace them with the
// final dictionary from Nikita (H2) / contracts/models.py when it is on GitHub.
// On Thursday the "values" lists become the options of the dropdowns.

export const FEATURES = {
  phase: {
    de: "Phase", en: "Phase",
    values: { solid_powder: { de: "Pulver", en: "powder" } },
  },
  water_level: {
    de: "Wasseranteil", en: "Water level",
    values: { low: { de: "niedrig", en: "low" } },
  },
  analyte_type: {
    de: "Art des Analyten", en: "Analyte type",
    values: { moisture: { de: "Feuchte", en: "moisture" } },
  },
  concentration_level: {
    de: "Konzentration", en: "Concentration",
    values: { low_percent: { de: "niedriger Prozentbereich", en: "low percent" } },
  },
  accuracy_need: { de: "Genauigkeitsbedarf", en: "Accuracy need", values: {} },
  temperature_class: {
    de: "Temperatur", en: "Temperature",
    values: { elevated: { de: "erhöht", en: "elevated" } },
  },
  pressure_class: {
    de: "Druck", en: "Pressure",
    values: { ambient: { de: "Normaldruck", en: "ambient" } },
  },
  fouling_risk: {
    de: "Belagsrisiko", en: "Fouling risk",
    values: { medium: { de: "mittel", en: "medium" } },
  },
  distance_class: {
    de: "Abstand", en: "Distance",
    values: { long: { de: "lang", en: "long" } },
  },
  fluorescence_risk: { de: "Fluoreszenzrisiko", en: "Fluorescence risk", values: {} },
  turbidity: {
    de: "Trübung", en: "Turbidity",
    values: { opaque: { de: "undurchsichtig", en: "opaque" } },
  },
  hazardous_area: {
    de: "Ex-Bereich", en: "Hazardous area",
    values: { yes: { de: "ja", en: "yes" }, no: { de: "nein", en: "no" } },
  },
};

const UNKNOWN = { de: "unbekannt", en: "unknown" };

// featureName("distance_class", "de") -> "Abstand"
export function featureName(feature, language) {
  return FEATURES[feature]?.[language] ?? feature;
}

// featureValueName("phase", "solid_powder", "de") -> "Pulver"
export function featureValueName(feature, value, language) {
  if (value === "unknown") return UNKNOWN[language] ?? value;
  return FEATURES[feature]?.values[value]?.[language] ?? value;
}
