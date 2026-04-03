"""
Wiki Cases
==========

Agent correctly uses wiki tools: reads index, checks manifest,
triggers compilation and linting.
Eval type: ReliabilityEval (expected tool calls)
"""

CASES: list[dict] = [
    {"input": "What's in the wiki right now?", "expected_tools": ["read_wiki_index"]},
    {"input": "What's the compile status of the wiki?", "expected_tools": ["read_wiki_state"]},
    {"input": "Are there any uncompiled sources?", "expected_tools": ["read_manifest"]},
    {"input": "Compile any new sources into the wiki", "expected_tools": ["read_manifest"]},
    {"input": "Run a health check on the wiki", "expected_tools": ["read_wiki_index"]},
    {"input": "How many articles are in the wiki?", "expected_tools": ["read_wiki_state"]},
]
