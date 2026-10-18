import os

# Tests never call the real API: llm/ returns the examples from contracts/examples.
os.environ["LLM_MOCK"] = "1"
