# SpectraScout: Auswahl einer Methode für die spektroskopische Analyse

SpectraScout (Team Touch Glass, schubKI 2026, Challenge von Art Fiber Systems) erstellt für einen AFS-Experten eine erste technische Einschätzung einer Anfrage zur Inline-Spektroskopie. Start und API-Schlüssel: [Schnellstart](#schnellstart) direkt darunter. Kosten: [API-Kosten](#api-kosten) am Ende. English: [README.md](README.md).

## Schnellstart

> **Tipp:** Diesen ganzen Abschnitt kann man in einen KI-Assistenten (ChatGPT, Claude, …) kopieren und fragen:
> *„Hilf mir, dieses Projekt Schritt für Schritt auf meinem Computer zu starten. Mein Betriebssystem ist …“*

Benötigt werden **Python 3.10+**, **Node.js 20.19+** (oder 22) und **git**. Die Befehle gelten für macOS/Linux; Hinweise für Windows stehen am Ende dieses Abschnitts.

### 1. Code holen und installieren

```bash
git clone https://github.com/nijat25gg-create/spectrascout-touch-glass-team.git
cd spectrascout-touch-glass-team
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt      # installiert auch requirements.txt
cp .env.example .env
```

### 2. API-Schlüssel eintragen (Datei `.env` im Projektordner)

`.env` in einem Texteditor öffnen und `[API KEY needed]` ersetzen:

| Feld in `.env` | Eintrag | Benötigt für |
|---|---|---|
| `ANTHROPIC_API_KEY` | eigener Anthropic-Schlüssel (`sk-ant-…`, von [console.anthropic.com](https://console.anthropic.com)) | Live-Analyse (Schritte A und B, Claude) |
| `LLM_MOCK` | `0` = echte Claude-Aufrufe, `1` = eingebaute Beispiele, ohne Schlüssel und Kosten | immer (Standard `1`) |
| `OPENROUTER_API_KEY` | eigener OpenRouter-Schlüssel (`sk-or-…`, von [openrouter.ai](https://openrouter.ai)) | nur der optionale Jev-Abgleich |
| `JEV_LIVE` | `1` = Jev an, `0` = aus | optional (Standard `0`) |

Ohne Schlüssel läuft die App im Demo-Modus (`LLM_MOCK=1`): Jeder Text liefert dann dasselbe Beispiel-Briefing (Feuchte in einem pharmazeutischen Pulver). Für eigene Texte `LLM_MOCK=0` und den Schlüssel setzen. `.env` steht in `.gitignore` und darf nie committet werden.

### 3. Backend starten (Terminal 1)

```bash
cd spectrascout-touch-glass-team
source .venv/bin/activate
cd backend
uvicorn app.main:app --port 8000
```

Prüfen: <http://localhost:8000/health> antwortet mit `{"status":"ok"}`.

### 4. Frontend starten (Terminal 2)

```bash
cd spectrascout-touch-glass-team/frontend
npm install
npm run dev
```

<http://localhost:5173> öffnen. Kundentext einfügen (mindestens 20 Zeichen) oder **Feuchte** anklicken, Sprache wählen und auf **Analysieren** klicken. Eine Live-Analyse dauert etwa 30–90 Sekunden.

### Ohne Web-App

```bash
LLM_MOCK=1 python run_case.py                                   # Demo, ohne Schlüssel
python run_case.py "Wir wollen die Feuchte eines Pulvers inline messen." de   # live, Schlüssel in .env nötig
```

### Tests

```bash
python contracts/check_contracts.py
python -m pytest -q engine/test_gates.py engine/b/test_b.py
cd backend && pytest -q
```

### Windows (PowerShell)

`python` statt `python3` verwenden, mit `.venv\Scripts\Activate.ps1` aktivieren, mit `copy .env.example .env` kopieren und Variablen so setzen: `$env:LLM_MOCK=1; python run_case.py`.

## Was das System macht

Der Kunde beschreibt seine geschäftliche Fragestellung, das Material und die Prozessbedingungen. Das System überführt die Anfrage in strukturierte Fakten, vergleicht spektroskopische Messansätze und erstellt eine vorläufige Empfehlung: geeignete Methoden und Schnittstellen zur Probe, ein Konfigurationskonzept, die Begründung der Auswahl, wesentliche offene Punkte und einen ersten Versuch. Die abschließende fachliche Bewertung bestätigt ein Experte.

Das System stellt dem Experten die Informationen bereit, die er zur Auswahl einer geeigneten spektroskopischen Analysemethode und zur Formulierung gezielter Rückfragen an den Kunden benötigt. Die Bewertung berücksichtigt die Messaufgabe, die Eigenschaften der Probe und die tatsächlichen Prozessbedingungen. Die Bezeichnung einer Methode allein bestimmt weder die Genauigkeit noch die Nachweisgrenze oder die Eignung einer Anlage.

## Grundprinzip des Entscheidungsverfahrens

Der Algorithmus bewertet konkrete Kandidaten anhand einzelner Faktoren. Jeder Faktor vergleicht ein Attribut der Anfrage mit einer Eigenschaft der Methode, der Schnittstelle zur Probe oder des Aufbaus: beispielsweise die Transparenz der Probe mit der Messgeometrie, die Zielkonzentration mit der nachgewiesenen Empfindlichkeit oder die Betriebstemperatur mit dem zulässigen Temperaturbereich einer Komponente.

```text
Kundentext und ergänzende Angaben
  → Fakten mit zugehörigen Zitaten extrahieren
  → Messaufgabe × Probe × Prozessbedingungen
  → Methoden und Kombinationen aus Methode und Probenschnittstelle prüfen
  → Konzepte für Configuration
  → Eignung + separate Konfidenzbewertung
  → Rückfragen und ein Versuch
```

`MeasurementTask`, `Sample` und `ProcessContext` beschreiben einen konkreten Anwendungsfall. `Method` und `SampleInterface` sind gemeinsame Kataloge mit versionierten Eigenschaften, Beziehungen und Einschränkungen. Sie werden aus Tabellen, PDF- und DOCX-Dateien zusammengestellt. Der aktuelle Katalog ist ein Entwurf, den ein Prozesschemiker noch prüfen muss. Sie werden für verschiedene Kunden wiederverwendet; die Anwendbarkeit jeder Eigenschaft hängt von der Probe und den Bedingungen ab.

`Configuration` wird für den Anwendungsfall aus zulässigen Kombinationen zusammengestellt und enthält einen oder mehrere `MeasurementChannel`-Datensätze. Der Katalog muss nicht sämtliche möglichen Aufbauten im Voraus aufzählen. Zunächst wird das Messkonzept festgelegt, anschließend werden die Komponenten konkretisiert. `SuitabilityEvidence` speichert Quellen und Prüfergebnisse zusammen mit ihrem Geltungsbereich.

Zu jedem Fakt werden der Wert, die Einheit oder Kategorie, das ursprüngliche Zitat und der Status gespeichert: ausdrücklich angegeben, abgeleitet, bestätigt, unbekannt oder widersprüchlich. Fehlende Informationen werden nicht als negative Antwort behandelt.

Ein LLM extrahiert Freitext und zugehörige Zitate. JEV kann Kategorien und einzelne inhaltliche Aussagen überprüfen. In der aktuellen Version läuft JEV nur im Extraktionsschritt (Choice-Fragen zu extrahierten Attributen, aktiviert mit `JEV_LIVE=1`): Es kann die Konfidenz eines extrahierten Werts senken, fügt aber nie einen Fakt hinzu und wählt nie eine Methode. Die übrigen JEV-Einsätze in der Tabelle unten sind geplant. Die Regelengine berechnet numerische Vergleiche, Einschränkungen, Faktorgewichte, Übergänge und die endgültige Rangfolge. JEV liefert typisierte Beurteilungen und Überprüfungen; die endgültige Entscheidung wird nicht an eine einzelne Frage „Wähle die beste Methode“ delegiert.

Diese Zerlegung entspricht dem Ansatz von TypeSafe: einzelne Aussagen bewerten und die Ergebnisse im Code zusammenführen. Innerhalb eines Aufrufs verwenden die Fragen denselben `state`, sehen jedoch die Antworten auf die anderen Fragen nicht. Benötigt ein späterer Schritt ein vorheriges Ergebnis, aktualisiert der Code zunächst den Zustand. Daraus folgt keine statistische Unabhängigkeit der bewerteten Ereignisse. [TypeSafe Introduction](https://docs.typesafe.ai/introduction)

## Welche Fragen in den einzelnen Schritten beantwortet werden

| Schritt | Frage | Was wird verglichen? | Werkzeug und Kennzahl | Ergebnis für den nächsten Schritt |
|---|---|---|---|---|
| Extraktion | Was soll gemessen werden, und was ist über die Probe und den Prozess bekannt? | Kundentext und ergänzende Angaben → MeasurementTask, Sample, ProcessContext | LLM: Fakten und Zitate. Bei aktivierter Überprüfung: **JEV Choice** — Frage nach einer Kategorie; Antwort: Kategorie und Wahrscheinlichkeitsverteilung. geplant: **JEV Noul** — Frage nach dem Wahrheitsgehalt einer einzelnen Aussage; Antwort: Wahrscheinlichkeit für „Ja“ von 0 bis 1 | Ein konkreter Case und eine Liste offener Punkte |
| Q1 | Kann die Methode ein unterscheidbares Signal für die Zielgröße liefern? | target, matrix, Komponenten und optische Eigenschaften ↔ observable_properties, signal_prerequisites, interferences | Regelprädikate; geplant: **JEV Noul** zur Überprüfung einer einzelnen Aussage über den Zusammenhang zwischen Zielgröße und Signal oder über eine Störung; Antwort: Wahrscheinlichkeit für „Ja“ von 0 bis 1. Der Code berechnet einen Punktwert von 0 bis 9 | Methodenkandidaten sowie Risiken durch Störungen und Kalibrierung |
| Q1b | Lassen sich die Anforderungen an Konzentration, Messfehler und Zeit erfüllen? | Kundenanforderungen ↔ anwendbare Profile für LOD/LOQ, Messfehler und Gesamtlatenz | Numerische Vergleiche im Code (der aktuelle Katalog enthält keine numerischen Profile für LOD/LOQ, Messfehler oder Latenz, daher bleibt Q1b meist UNKNOWN); geplant: **JEV Choice** zur Bewertung der Erreichbarkeit anhand der vorliegenden Belege; Antwort: „erreichbar / bedingt erreichbar / nicht erreichbar / unbekannt“ und Wahrscheinlichkeitsverteilung. Der Code berechnet einen Punktwert von 0 bis 9 | Bewertung der Anforderungen und noch nicht bestätigte Prüfpunkte |
| Q2 | Kann die Schnittstelle ein repräsentatives Signal von dieser Probe erfassen? | phase, form, opacity, heterogeneity und spatial_scope ↔ geometry, contact, sample_region, path/depth | Regeln zur Kompatibilität und zum optischen Zugang; Punktwert von 0 bis 9 | Zulässige Kombinationen Method × SampleInterface und Konzepte für Configuration |
| Q3 | Kann die Konfiguration im Prozess des Kunden eingesetzt werden? | Temperatur, Druck, Umgebung, Entfernung, Ressourcen und Einschränkungen ↔ Eigenschaften des Konzepts bzw. der Komponenten | Zunächst Regeln für Klassen von Bedingungen, anschließend Prüfung der spezifizierten Komponentengrenzen; Punktwert von 0 bis 9 | Bewertung des Aufbaus und Stand seiner Ausarbeitung |
| Q4 | Wie gut ist die Eignung für diese Zielgröße, Probe und Bedingungen belegt? | SuitabilityEvidence ↔ Case und Configuration | Regeln zur Prüfung der Übertragbarkeit von Belegen; Evidenzbewertung von 0 bis 3 und separate Konfidenzbewertung des Projekts | Konfidenzstufe, Grenzen der Übertragbarkeit und ein erster Versuch |

Die Regelengine berechnet die Punktwerte der Schritte von 0 bis 9. Dies sind interne `stage_score`-Werte. Sie unterscheiden sich von einer **JEV Score**-Antwort: Diese beschreibt die erwartete Position auf einer definierten Skala und kann Nachkommastellen enthalten. Die Formeln aller drei JEV-Formate folgen weiter unten.

### Allgemeine Kriterien für die Entscheidung

1. **Beobachtbarkeit — Q1:** Besteht ein Zusammenhang zwischen der Zielgröße und dem Signal dieser Methode? Ist der Zusammenhang direkt, oder ist eine indirekte Kalibrierung erforderlich?
2. **Unterscheidbarkeit — Q1:** Lässt sich das Nutzsignal von der Matrix, dem Hintergrund und anderen Komponenten trennen?
3. **Optischer Zugang — Q2:** Kann das Licht den relevanten Bereich der Probe erreichen und bei der gewählten Geometrie ein ausreichend starkes Signal zurückliefern?
4. **Prozesskompatibilität — Q3:** Halten Sonde und Komponenten der Temperatur, dem Druck, der chemischen Umgebung und den Einbaubedingungen stand?
5. **Erreichbarkeit der Anforderungen — Q1b:** Gibt es eine belastbare Grundlage für die erwartete Genauigkeit, Nachweisgrenze und Messgeschwindigkeit?
6. **Überprüfbarkeit — Q4:** Stehen repräsentative Proben und eine unabhängige Referenz zur Verfügung, um das Ergebnis zu bestätigen?

Die Vollständigkeit dieser Prüfungen hängt vom Inhalt der Regeln und des Katalogs ab und wird anhand von Anwendungsfällen bewertet, die von Experten geprüft wurden.

**Stand der Algorithmuskalibrierung.** Zur Verbesserung der Empfehlungsgenauigkeit ist eine Kalibrierung der Faktorgewichte, Schwellenwerte, JEV-Bewertungsraster und Konfidenzregeln anhand von Experten bewerteter Anwendungsfälle geplant. Diese Kalibrierung wurde bislang noch nicht durchgeführt. Die nachfolgenden Einstellungen sind daher Ausgangsparameter; die damit erzielte Empfehlungsgenauigkeit ist noch nicht bestätigt. Die Kalibrierung des Algorithmus und die analytische Kalibrierung einer spektroskopischen Messung sind getrennte Verfahren.

## JEV-Formeln aus der TypeSafe-Dokumentation

Dieser Abschnitt beschreibt die Mathematik der JEV-Primitive. Die projektspezifischen Formeln für die Eignung und Q4 werden anschließend separat erläutert; sie werden nicht von TypeSafe vorgegeben.

### Noul — Wahrscheinlichkeit einer Aussage

Für einen Zustand $x$ und eine einzelne Aussage $A$ gilt:

$$
p = P(A=\mathrm{true}\mid x), \qquad p\in[0,1].
$$

Die Antwort `noul` ist die Wahrscheinlichkeit für „Ja“. Die Anwendung legt die Schwellenwerte $\tau_-<\tau_+$ fest:

$$
\operatorname{decision}(p)=
\begin{cases}
\mathrm{yes}, & p\ge\tau_+,\\
\mathrm{no}, & p\le\tau_-,\\
\mathrm{unknown/review}, & \tau_-<p<\tau_+.
\end{cases}
$$

Diese Schwellenwertregel wird von der Anwendung festgelegt. Die Schwellenwerte hängen von den Folgen einer Fehlentscheidung ab und müssen anhand eigener Daten validiert werden. Ein unbekannter Sachverhalt gilt nicht allein aufgrund einer Modellantwort als nachgewiesen. [TypeSafe Noul](https://docs.typesafe.ai/primitives/noul)

### Choice — Auswahl einer Kategorie

Für $n$ Optionen liefert JEV eine Verteilung und die ausgewählte Option:

$$
p_i=P(Y=i\mid x),\qquad \sum_{i=1}^{n}p_i=1,
\qquad \hat y=\underset{i}{\operatorname{argmax}}\;p_i.
$$

Anwendungsbeispiele sind die Klassifikation der Transparenz, der Phase oder des Zieltyps. Wenn die Liste möglicherweise unvollständig ist, enthält sie eine Kategorie `unknown`/`other`. [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice)

### Score — Erwartete Position auf einer Skala

Für $n$ beschriebene Stufen mit den Indizes $0,\ldots,n-1$ gilt:

$$
s_{\mathrm{JEV}}=\sum_{i=0}^{n-1}i\,p_i.
$$

Für zehn Stufen:

$$
s_{\mathrm{JEV}}=\sum_{i=0}^{9}i\,p_i\in[0,9].
$$

Das Ergebnis kann Nachkommastellen enthalten. Beispielsweise ergeben $p_7=0.2$, $p_8=0.6$ und $p_9=0.2$ den Wert $s=8$. Dieser Wert bezeichnet eine Position innerhalb des definierten Bewertungsrasters, keine gemessene Konzentration und keine Wahrscheinlichkeit eines erfolgreichen Einsatzes. [TypeSafe Score](https://docs.typesafe.ai/primitives/score)

### Konfidenz der Primitive

Die folgenden Formeln sind unter [TypeSafe Confidence](https://docs.typesafe.ai/confidence#how-confidence-is-calculated) veröffentlicht.

Noul gibt kein separates Konfidenzfeld zurück. Die Dokumentation schlägt bei Bedarf folgende Berechnung vor:

$$
C_{\mathrm{Noul}}=|2p-1|.
$$

Für Choice mit $n\ge2$ und $p_{\max}=\max_i p_i$ gilt:

$$
C_{\mathrm{Choice}}=
\frac{p_{\max}-\frac1n}{1-\frac1n}.
$$

Für Score mit $m=\operatorname{argmax}_i p_i$ gilt:

$$
D_{\mathrm{unif}}=
\frac1n\sum_{i=0}^{n-1}\left|i-\frac{n-1}{2}\right|,
$$

$$
C_{\mathrm{Score}}=
\max\left(0,\;1-
\frac{\sum_{i=0}^{n-1}p_i|i-m|}{D_{\mathrm{unif}}}
\right).
$$

Für $n=10$ gilt $D_{\mathrm{unif}}=2.5$. In der obigen Beispielverteilung ist $m=8$, also:

$$
C_{\mathrm{Score}}=
1-\frac{0.2\cdot1+0.6\cdot0+0.2\cdot1}{2.5}=0.84.
$$

Dieser Wert beschreibt die Bestimmtheit der Modellantwort. Er bestätigt nicht die Qualität eines physikalischen Versuchs.

### Klarstellung zum API-Vertrag

In der offiziellen HTTP-API wird die Anzahl der Score-Stufen durch die Länge des geordneten Arrays `criteria` festgelegt: Zehn Beschreibungen definieren die Stufen 0–9. Ein Feld `levels: 10` in unserem Entwurf wäre eine Einstellung unseres Adapters; es ist nicht automatisch ein Feld der TypeSafe-Anfrage. Der native Wert `score` ist numerisch und erlaubt Nachkommastellen. [TypeSafe API reference](https://docs.typesafe.ai/api)

Der ganzzahlige Punktwert eines Schritts und die JEV-Antwort mit möglichen Nachkommastellen sollen deshalb getrennt als `stage_score` und `jev_score` gespeichert werden (geplant für den JEV-Adapter), zusammen mit `probabilities`, `confidence` und der Version des Bewertungsrasters. Werte mit Nachkommastellen dürfen für einen internen `stage_score` abgelehnt werden, jedoch nicht für den ursprünglichen `jev_score`.

## Berechnung der Kennzahlen des Algorithmus

Die folgenden Formeln definieren das Rankingmodell des Projekts. Seine Gewichte, Gruppenbegrenzungen und Schwellenwerte müssen anhand von Anwendungsfällen kalibriert werden, die von Experten geprüft wurden; es handelt sich nicht um TypeSafe-Formeln.

### Faktoren und Punktwerte der Schritte

Für einen Faktor $f$ und einen Kandidaten $c$ liefert eine Regel einen Beitrag:

$$
e_f(c)=
\begin{cases}
+k_f, & \text{eine Übereinstimmung ist bestätigt},\\
-k_f, & \text{ein weiches Risiko oder eine Abweichung ist festgestellt},\\
0, & \text{das Ergebnis ist neutral, unbekannt oder nicht anwendbar}.
\end{cases}
$$

Die letzten drei Zustände bleiben im Regelprotokoll unterscheidbar. Für UNKNOWN wird der Bereich möglicher Beiträge gespeichert; ein numerischer Nullwert belegt keine Übereinstimmung. Ein harter Ausschluss wird als separates Flag erfasst.

Jeder technische Schritt umfasst vier Faktorgruppen. Im Ausgangsmodell gilt:

$$
r_g(c)=\operatorname{clip}\left(\sum_{f\in g}e_f(c),-3,3\right),
\qquad r_q(c)=\sum_{g=1}^{4}r_g(c)\in[-12,12].
$$

Faktoren, die dieselbe Ursache wiederholen, werden gemäß den Regeln für sich gegenseitig ausschließende Gruppen nur einmal berücksichtigt. Der Punktwert eines Schritts lautet:

$$
q_q(c)=B_q\bigl(r_q(c)\bigr)\in\{0,1,\ldots,9\}.
$$

Für die vorgeschlagenen, bislang nicht freigegebenen Klassengrenzen gilt:

$$
B_q(r)=\sum_{t\in\{-5,-3,-1,0,1,2,3,4,6\}}\mathbf1\{r\ge t\}.
$$

Diese Regel quantisiert **gewichtete Faktorbeiträge**. Sie ersetzt weder die JEV-Formel für den Erwartungswert noch verlangt sie von JEV, die Berechnung zu wiederholen.

### Eignung und Ausschlüsse

Für einen Kandidaten ohne bestätigten Ausschluss gilt:

$$
S(c)=q_{Q1}(c)+q_{Q1b}(c)+q_{Q2}(c)+q_{Q3}(c)\in[0,36],
$$

$$
S_{\%}(c)=100\frac{S(c)}{36}.
$$

Der Prozentwert ist ein relativer Eignungsindex. Bei nachgewiesener physikalischer Unvereinbarkeit wird der Kandidat unabhängig vom Gesamtpunktwert ausgeschlossen. Der Geltungsbereich des Ausschlusses ist auf den Nachweis beschränkt: eine Methode für den Case, eine Kombination aus Methode und Probenschnittstelle oder ein konkreter Aufbau. Ein niedriger Punktwert allein bedeutet nicht EXCLUDE.

### Q4 und Konfidenz der Empfehlung

Die Evidenzbewertung $E(c)=q_{Q4}(c)\in\{0,1,2,3\}$ beschreibt die Abstufung von fehlenden relevanten Daten bis zu einer vergleichbaren unabhängigen Überprüfung. Die Stärke eines Belegs wird zusammen mit seinem positiven oder negativen Ergebnis gespeichert.

$F_c$ sei die Menge der wesentlichen anwendbaren technischen Faktoren, ohne rein diagnostische Faktoren. Dann gilt:

$$
\operatorname{coverage}(c)=
\frac{\#\{f\in F_c:\text{Eingaben explicit/confirmed, Grundlage geprüft}\}}
{|F_c|}.
$$

Ist $F_c$ leer, ist die Abdeckung unbekannt. Die Ausgangsregel des Projekts lautet:

$$
C_{\mathrm{recommendation}}(c)=
\begin{cases}
\mathrm{high}, & E\ge2,\ coverage\ge0.80,\ \text{keine kritischen Unbekannten},\\
\mathrm{medium}, & E\ge1,\ coverage\ge0.50,\\
\mathrm{low}, & \text{sonst}.
\end{cases}
$$

Es gilt der erste zutreffende Zweig; $E=0$ oder unbekannte Abdeckung ergibt immer low. Eine Prüfung auf Quellenkonflikte ist geplant. Dies ist die **projektspezifische Konfidenz**; sie unterscheidet sich von $C_{\mathrm{Choice}}$ und $C_{\mathrm{Score}}$ aus JEV. Q4 geht nicht in $S(c)$ ein, und eine hohe Modellkonfidenz ersetzt keinen relevanten Versuch.

### Rangfolge und gezielte Rückfragen

Der Code entfernt ausgeschlossene Kandidaten, kennzeichnet Kandidaten mit kritischen offenen Punkten und erstellt anschließend die Rangfolge nach $S(c)$, der Summe der Rohwerte $r_q(c)$ und bei Gleichstand nach Konfidenz. Der Rang einer Methode wird durch ihre beste zulässige Konfiguration für den Case bestimmt.

Für ein unbekanntes Attribut $a$ durchläuft der Algorithmus die zulässigen Klassen $v\in V_a$ und berechnet die Rangfolge $R_{a\leftarrow v}$ erneut. Eine Frage hat hohe Priorität, wenn unterschiedliche Werte den führenden Kandidaten oder die Menge der ausgeschlossenen Kandidaten verändern. Sie hat mittlere Priorität, wenn sich nur die ersten drei Plätze ändern. Bleibt die Reihenfolge im geprüften Bereich stabil, wird die Frage zu diesem Zeitpunkt nicht gestellt. Eine unvollständige Aufzählung beweist keine Stabilität.

Jede Rückfrage erläutert, wie die Antwort die Entscheidung beeinflussen könnte. Der erste Versuch prüft eine Hypothese, die die Auswahl unter aussichtsreichen Kandidaten mit unzureichenden Belegen verändern könnte: Er vergleicht Kandidaten an repräsentativen Proben mit einer unabhängigen Referenz und vereinbarten Akzeptanzkriterien.

## Was der Experte erhält

Die Rangliste enthält die Methode, die Schnittstelle zur Probe, das Konfigurationskonzept, vier technische Punktwerte, die Eignung von 0 bis 36, eine separate Konfidenzbewertung und nachvollziehbare Faktorbeiträge. Zusätzlich werden Ausschlussgründe, Annahmen, entscheidungsrelevante Rückfragen und ein erster Versuch ausgegeben. Der Experte kann einen Fakt oder eine Bedingung korrigieren und erhält über die API (`POST /assessments/recalculate`) ein neu berechnetes Ergebnis mit aktualisiertem Regelprotokoll. In der aktuellen Weboberfläche werden die Antworten auf die Rückfragen im Kundentext ergänzt und die Analyse erneut gestartet.

Detaillierte Spezifikation: [docs/method-b.md](docs/method-b.md) (Russisch); Regeln in [rules/b/rules_b.yaml](rules/b/rules_b.yaml), Katalog in [rules/b/catalog_b.yaml](rules/b/catalog_b.yaml). Die dortigen Schwellenwerte und Gewichte sind Ausgangsparameter des Projekts. Die Klarstellungen zur offiziellen Noul-/Score-Semantik und zur API in dieser README sind bei der Implementierung des JEV-Adapters zu berücksichtigen.

Die offiziellen TypeSafe-Seiten wurden am 18. Oktober 2026 geprüft. Als Quellen wurden typesafe.ai und docs.typesafe.ai verwendet; ähnlich benannte Websites und Zusammenfassungen Dritter dienten nicht als Grundlage für die Formeln.

## API-Kosten

Preise pro Million Token (USD), Stand 18. Oktober 2026:

| Modell | Einsatz | Eingabe | Ausgabe |
|---|---|---|---|
| Claude Haiku 5.5 (`MODEL_EXTRACT`) | Schritt A, Extraktion | 0,10 $ | 0,50 $ |
| Claude Sonnet 5.5 (`MODEL_REASON`) | Schritt B, Begründung | 2,00 $ | 10,00 $ |
| Jev 1.14 über OpenRouter (`JEV_MODEL`) | optionaler Abgleich | 0,042 $ | kostenlos |

Kosten einer Analyse:

| Aufruf | Token (Eingabe / Ausgabe) | Kosten |
|---|---|---|
| Schritt A (Haiku) | etwa 7.000 / 2.000–5.000 | etwa 0,003 $ |
| Schritt B (Sonnet) | etwa 10.000–15.000 / 2.000–4.000 | etwa 0,05–0,06 $ |
| Jev (alle Aufrufe einer Analyse) | — | 0,0002 $ (gemessen: 0,0001976 $) |
| **Summe** | | **etwa 0,06 $**, im ungünstigsten Fall etwa 0,21 $ |

100 Analysen kosten etwa 6 $. Der Demo-Modus (`LLM_MOCK=1`) kostet nichts. Details und Annahmen: [docs/api-costs.md](docs/api-costs.md) (Englisch). Quellen: [Claude-Preise](https://platform.claude.com/docs/en/about-claude/pricing), [OpenRouter: jev 1.14](https://openrouter.ai/models/typesafe/jev-1.14).

Beispielergebnisse für die sechs Evaluationsfälle H01–H06 (Live-Lauf, Methode B): [cases/](cases/).
