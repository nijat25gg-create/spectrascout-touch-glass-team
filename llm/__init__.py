"""LLM steps of SpectraScout (owner: Nidzhat, CS 1).

    from llm import extract, explain
    extraction = extract(ExtractInput(...))     # C2 -> C3, step A
    explanation = explain(ExplainInput(...))    # C6 -> C7, step B

Set LLM_MOCK=1 to get the example answers from contracts/examples
without an API key and without cost.
"""
from .extract import extract
from .explain import explain

__all__ = ["extract", "explain"]
