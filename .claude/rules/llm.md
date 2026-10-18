---
paths:
  - "llm/**"
  - "kb/**"
---
Two LLM calls only: extract (step A) and explain (step B), structured output via
client.messages.parse into contracts models. Step A must not invent values: no data →
status unknown; silence is not a "no". Quotes must exist verbatim in the customer text
(llm.vocab.quote_in_text; a failing quote makes the attribute unknown). Step B explains only
from kb cards and the gates trace (sources copied exactly; llm.explain._check removes invented
sources, claims and attributes) and never changes the ranking. Prompt examples come from D01-D08
or are generic, never from H01-H06 texts. Keep LLM_MOCK working for every change.
