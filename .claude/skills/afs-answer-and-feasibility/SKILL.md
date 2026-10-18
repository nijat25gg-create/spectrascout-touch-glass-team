---
name: afs-answer-and-feasibility
description: Structure of an AFS answer (requirements, questions, recommendation, measurement concept, range, risks, feasibility plan, sources) and the decision status. Use when writing or reviewing step B reasoning and the briefing.
---

# AFS answer structure

Section names follow the worked examples D01/D02. Any clear format works; the content matters.

1. **Requirements**: facts the client stated and the key unknowns, kept separate.
2. **Clarification questions**: prioritised; first the questions whose answers could change the method or the setup. In the product they come from the gates engine (`assessment.questions`).
3. **Recommendation**: methods or combinations worth testing, each with its reason and the conditions under which it applies, plus one decision status.
4. **Measurement concept**: probe and geometry (ATR, diffuse reflection, transmission, transflection), measurement location, fiber link. High level only.
5. **Spectral range**: in correct units (see `afs-premise-check`).
6. **Risks and uncertainty**: what could make the recommendation wrong and which assumptions it rests on.
7. **Feasibility plan**: representative samples or process states, independent reference measurements, what is compared, and the basis for go / no-go. Lab check first (step 0), then in-line.
8. **Sources**: source and page for each important claim.

## Decision status (exactly one)
- `provisional`: provisional feasibility assessment.
- `insufficient_information`: the known facts cannot justify a method choice. Ask the questions that decide it and propose the next step.
- `outside_scope`: the request is outside what AFS methods support.

## Insufficient information is a valid answer
- A conditional shortlist with explicit assumptions is fine.
- An honest provisional plan is more useful than a final configuration built on missing facts.
- Acceptance criteria come from the client; none is invented. Agree numerical criteria with the client before the test.
