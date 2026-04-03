"""
Pal Evaluations
================

Eval framework for testing Pal's capabilities.

Usage:
    python -m evals
    python -m evals --category routing
    python -m evals --verbose
"""

from agno.models.openai import OpenAIResponses

JUDGE_MODEL = OpenAIResponses(id="gpt-5.4")

CATEGORIES: dict[str, dict] = {
    "security": {"type": "judge_binary", "module": "evals.cases.security"},
    "routing": {"type": "reliability", "module": "evals.cases.routing"},
    "governance": {"type": "judge_binary", "module": "evals.cases.governance"},
    "knowledge": {"type": "accuracy", "module": "evals.cases.knowledge"},
    "voice": {"type": "judge_numeric", "module": "evals.cases.voice"},
    "wiki": {"type": "reliability", "module": "evals.cases.wiki"},
}
