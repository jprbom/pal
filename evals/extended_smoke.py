"""
Extended PAL Smoke Tests
========================

Comprehensive Slack + Knowledge Pipeline tests.
Run after Phase 2 env vars are configured.

    docker compose exec -T pal-api python -c "
    import logging; logging.disable(logging.DEBUG)
    import os; os.environ['AGNO_LOG_LEVEL'] = 'WARNING'
    from evals.extended_smoke import run_extended
    run_extended(verbose=True)
    " 2>/dev/null
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field


@dataclass
class TestCase:
    id: str
    name: str
    group: str
    prompt: str
    response_contains: list[str] = field(default_factory=list)
    response_not_contains: list[str] = field(default_factory=list)
    response_matches: list[str] = field(default_factory=list)
    depends_on: str | None = None


@dataclass
class TestResult:
    test: TestCase
    status: str  # PASS, FAIL, ERROR
    duration: float
    response: str
    failures: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Slack Tests
# ---------------------------------------------------------------------------

SLACK_TESTS: list[TestCase] = [
    # --- Channel discovery ---
    TestCase(
        id="S01",
        name="List all channels",
        group="slack-discovery",
        prompt="List all available Slack channels.",
        response_matches=[r"(?i)(channel|#|slack)"],
    ),
    TestCase(
        id="S02",
        name="Check if #pal-updates exists",
        group="slack-discovery",
        prompt="Does the #pal-updates channel exist in Slack?",
        response_matches=[r"(?i)(pal.updates|yes|exists|found)"],
    ),
    TestCase(
        id="S03",
        name="Check if #agents exists",
        group="slack-discovery",
        prompt="Does the #agents channel exist in Slack? Just check and tell me.",
        response_matches=[r"(?i)(agent|yes|no|exist|found|not found|doesn.t)"],
    ),
    # --- Post to #pal-updates ---
    TestCase(
        id="S04",
        name="Post simple status to #pal-updates",
        group="slack-post",
        prompt="Post to #pal-updates: System online. All agents healthy.",
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S05",
        name="Post formatted message to #pal-updates",
        group="slack-post",
        prompt=(
            "Post to #pal-updates:\n"
            "*Daily Report — 2026-04-03*\n"
            "• Knowledge base: 3 articles compiled\n"
            "• Sources ingested: 2\n"
            "• Wiki health: Good"
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S06",
        name="Post multi-line update to #pal-updates",
        group="slack-post",
        prompt=(
            "Post this to #pal-updates:\n\n"
            "📋 Smoke Test Report\n"
            "Phase 1: 15/15 passed\n"
            "Phase 2: 8/8 passed\n"
            "Extended: Running now\n"
            "Status: All systems operational"
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S07",
        name="Post learning summary to #pal-updates",
        group="slack-post",
        prompt=(
            "Post to #pal-updates:\n"
            "Weekly Learning Summary:\n"
            "- Discovered context engineering patterns\n"
            "- Compiled 2 wiki articles on RAG and tool-use\n"
            "- User preference: concise async communication"
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S08",
        name="Post code snippet to #pal-updates",
        group="slack-post",
        prompt=(
            "Post to #pal-updates:\n"
            "New tool added:\n"
            "```python\n"
            "@tool\n"
            "def ingest_url(url: str, title: str):\n"
            "    pass\n"
            "```"
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S09",
        name="Post alert format to #pal-updates",
        group="slack-post",
        prompt=(
            "Post to #pal-updates: "
            "⚠️ Wiki Lint Alert: 2 articles flagged as stale, "
            "1 orphaned concept detected. Run `compile` to fix."
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S10",
        name="Post wiki compile report to #pal-updates",
        group="slack-post",
        prompt=(
            "Post to #pal-updates:\n"
            "Wiki Compile Complete:\n"
            "- Processed: context-engineering-primer.md\n"
            "- New concepts: context-engineering, RAG, tool-use\n"
            "- Updated index with 3 articles"
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S11",
        name="Post long detailed message to #pal-updates",
        group="slack-post",
        prompt=(
            "Post this detailed update to #pal-updates:\n\n"
            "🔄 System Status — Extended Test Run\n\n"
            "Infrastructure:\n"
            "• API: Running on port 8000\n"
            "• Database: PostgreSQL + pgvector operational\n"
            "• Agents: Navigator, Researcher, Compiler, Linter active\n\n"
            "Knowledge Pipeline:\n"
            "• Raw sources: 2 ingested\n"
            "• Wiki articles: 3 compiled\n"
            "• Index: Updated\n\n"
            "Integration Status:\n"
            "• Slack: Connected ✅\n"
            "• Parallel: Connected ✅\n"
            "• Gmail: Not configured\n"
            "• Calendar: Not configured\n"
            "• Git Sync: Not configured"
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    # --- Post to #agents ---
    TestCase(
        id="S12",
        name="Post to #agents channel",
        group="slack-agents",
        prompt="Post to #agents: Pal extended smoke tests in progress. Testing all agent capabilities.",
        response_matches=[r"(?i)(posted|sent|agents|not.found|doesn.t exist|channel_not_found)"],
    ),
    TestCase(
        id="S13",
        name="Post agent roster to #agents",
        group="slack-agents",
        prompt=(
            "Post to #agents:\n"
            "Pal Agent Roster:\n"
            "1. Navigator — routes queries, reads wiki, handles SQL\n"
            "2. Researcher — web search, source gathering\n"
            "3. Compiler — raw → wiki articles\n"
            "4. Linter — wiki health checks\n"
            "5. Syncer — git-backed persistence (not configured)"
        ),
        response_matches=[r"(?i)(posted|sent|agents|not.found|doesn.t exist|channel_not_found)"],
    ),
    TestCase(
        id="S14",
        name="Post test results to #agents",
        group="slack-agents",
        prompt=(
            "Post to #agents:\n"
            "Test Results — Knowledge Pipeline:\n"
            "✅ Ingest text: PASS\n"
            "✅ Ingest URL: PASS\n"
            "✅ Compile: PASS\n"
            "✅ Wiki Q&A: PASS\n"
            "✅ Linter: PASS"
        ),
        response_matches=[r"(?i)(posted|sent|agents|not.found|doesn.t exist|channel_not_found)"],
    ),
    # --- Slack edge cases ---
    TestCase(
        id="S15",
        name="Post to nonexistent channel",
        group="slack-edge",
        prompt="Post 'test message' to the #this-channel-does-not-exist channel.",
        response_matches=[r"(?i)(not.found|doesn.t exist|couldn.t|no.*channel|error|unable|channel_not_found)"],
    ),
    TestCase(
        id="S16",
        name="Ask Slack question (not a post)",
        group="slack-edge",
        prompt="How many Slack channels do I have access to?",
        response_matches=[r"(?i)(\d+|channel|slack)"],
    ),
    TestCase(
        id="S17",
        name="Post empty-ish message",
        group="slack-edge",
        prompt="Post to #pal-updates: .",
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
    TestCase(
        id="S18",
        name="Cross-channel: post same message to two channels",
        group="slack-edge",
        prompt="Post 'Cross-channel test: message from Pal' to both #pal-updates and #general.",
        response_matches=[r"(?i)(posted|sent|pal.updates|general)"],
    ),
    TestCase(
        id="S19",
        name="Read channel history",
        group="slack-edge",
        prompt="What are the recent messages in #pal-updates?",
        response_matches=[r"(?i)(message|pal.updates|recent|posted|smoke|system|status)"],
    ),
    TestCase(
        id="S20",
        name="Final Slack status post",
        group="slack-edge",
        prompt=(
            "Post to #pal-updates:\n"
            "✅ Extended smoke test complete.\n"
            "Slack integration: fully operational.\n"
            "20 Slack tests executed."
        ),
        response_matches=[r"(?i)(posted|sent|pal.updates)"],
    ),
]


# ---------------------------------------------------------------------------
# Knowledge Pipeline Tests
# ---------------------------------------------------------------------------

KNOWLEDGE_TESTS: list[TestCase] = [
    # --- Ingest variety ---
    TestCase(
        id="K01",
        name="Ingest text — AI agents overview",
        group="ingest",
        prompt=(
            "Save this as a raw source titled 'AI Agent Architectures':\n\n"
            "AI agents are systems that use LLMs as reasoning engines to take actions "
            "in the world. Key architectural patterns include:\n"
            "1. ReAct (Reason + Act) — interleave reasoning and tool use\n"
            "2. Plan-and-Execute — create a plan, then execute steps\n"
            "3. Multi-agent — multiple specialized agents coordinating\n"
            "4. Reflection — self-critique and iterative improvement\n"
            "5. Tool-augmented — LLM + external tools (search, code, APIs)\n\n"
            "The choice of architecture depends on task complexity, latency "
            "requirements, and reliability needs. Simple tasks use single-agent "
            "ReAct; complex workflows use multi-agent with a coordinator."
        ),
        response_matches=[r"(?i)(ingested|saved|raw|agent)"],
    ),
    TestCase(
        id="K02",
        name="Ingest text — vector databases",
        group="ingest",
        prompt=(
            "Save this as a raw source titled 'Vector Database Comparison':\n\n"
            "Vector databases store and query high-dimensional embeddings for "
            "similarity search. Key options:\n\n"
            "**pgvector**: PostgreSQL extension. Pros: no new infra, ACID, "
            "hybrid search with SQL. Cons: slower at scale vs purpose-built.\n\n"
            "**Pinecone**: Managed service. Pros: zero-ops, fast. Cons: vendor "
            "lock-in, cost at scale.\n\n"
            "**Weaviate**: Open-source. Pros: hybrid search, multi-modal. "
            "Cons: operational overhead.\n\n"
            "**Qdrant**: Open-source. Pros: fast, good filtering. Cons: "
            "smaller ecosystem.\n\n"
            "For most applications, pgvector is the pragmatic choice — it "
            "avoids infrastructure sprawl and supports hybrid keyword+vector search."
        ),
        response_matches=[r"(?i)(ingested|saved|raw|vector|database)"],
    ),
    TestCase(
        id="K03",
        name="Ingest text — prompt engineering",
        group="ingest",
        prompt=(
            "Save this as a raw source titled 'Prompt Engineering Best Practices':\n\n"
            "Effective prompts share these properties:\n"
            "1. Clear role definition — tell the model who it is\n"
            "2. Structured output format — specify the expected shape\n"
            "3. Few-shot examples — show, don't just tell\n"
            "4. Chain-of-thought — ask the model to reason step by step\n"
            "5. Guardrails — explicit constraints on what not to do\n"
            "6. Context window management — prioritize recent, relevant info\n\n"
            "Anti-patterns: overly long system prompts, conflicting instructions, "
            "vague success criteria, no error handling guidance."
        ),
        response_matches=[r"(?i)(ingested|saved|raw|prompt)"],
    ),
    TestCase(
        id="K04",
        name="Check manifest after ingests",
        group="ingest",
        prompt="Show me the current manifest — what raw sources have been ingested and their compile status?",
        response_matches=[r"(?i)(manifest|ingested|compiled|false|source)"],
    ),
    # --- Compile ---
    TestCase(
        id="K05",
        name="Compile all new sources",
        group="compile",
        prompt=(
            "Compile all uncompiled raw sources into wiki articles. "
            "Process each one, create concept articles and summaries, "
            "and update the index."
        ),
        depends_on="K04",
        response_matches=[r"(?i)(compiled|article|wiki|index|concept)"],
    ),
    TestCase(
        id="K06",
        name="Verify manifest after compile",
        group="compile",
        prompt="Show me the manifest again — are all sources now compiled?",
        depends_on="K05",
        response_matches=[r"(?i)(compiled|true|manifest|all)"],
    ),
    TestCase(
        id="K07",
        name="Verify wiki index",
        group="compile",
        prompt="Show me the wiki index — what articles do we have?",
        depends_on="K05",
        response_matches=[r"(?i)(index|article|concept|summary)"],
    ),
    # --- Query compiled wiki ---
    TestCase(
        id="K08",
        name="Query — context engineering",
        group="query",
        prompt="What does my knowledge base say about context engineering?",
        depends_on="K05",
        response_matches=[r"(?i)(context.engineering|RAG|retrieval|LLM|pipeline)"],
    ),
    TestCase(
        id="K09",
        name="Query — AI agents",
        group="query",
        prompt="What do my wiki articles say about AI agent architectures?",
        depends_on="K05",
        response_matches=[r"(?i)(agent|ReAct|multi.agent|plan|tool)"],
    ),
    TestCase(
        id="K10",
        name="Query — vector databases",
        group="query",
        prompt="Compare vector databases based on what's in my knowledge base.",
        depends_on="K05",
        response_matches=[r"(?i)(pgvector|pinecone|vector|database|embedding)"],
    ),
    TestCase(
        id="K11",
        name="Query — prompt engineering",
        group="query",
        prompt="What does my wiki say about prompt engineering best practices?",
        depends_on="K05",
        response_matches=[r"(?i)(prompt|few.shot|chain.of.thought|role|example)"],
    ),
    TestCase(
        id="K12",
        name="Cross-topic query",
        group="query",
        prompt=(
            "Based on my knowledge base, how do context engineering and AI agent architectures relate to each other?"
        ),
        depends_on="K05",
        response_matches=[r"(?i)(context|agent|tool|retrieval|architecture)"],
    ),
    # --- Re-compile (idempotent) ---
    TestCase(
        id="K13",
        name="Re-compile — should skip already compiled",
        group="compile-idem",
        prompt="Compile any new raw sources into the wiki.",
        depends_on="K05",
        response_matches=[r"(?i)(no new|nothing|up to date|already|no.*uncompiled|all.*compiled|0|weren.?t any)"],
    ),
    # --- Incremental ingest + compile ---
    TestCase(
        id="K14",
        name="Ingest additional source",
        group="incremental",
        prompt=(
            "Save this as a raw source titled 'Evaluation-Driven Development':\n\n"
            "Evaluation-driven development (EDD) is the practice of building LLM "
            "applications by writing evaluations first, then iterating on prompts "
            "and architectures until evals pass. Key principles:\n"
            "1. Define success criteria before writing prompts\n"
            "2. Automated evals over manual testing\n"
            "3. Golden datasets for regression testing\n"
            "4. Separate accuracy, latency, and cost metrics\n"
            "5. Version control for prompts alongside code\n\n"
            "EDD is to LLM apps what TDD is to traditional software."
        ),
        response_matches=[r"(?i)(ingested|saved|raw|eval)"],
    ),
    TestCase(
        id="K15",
        name="Incremental compile — only new source",
        group="incremental",
        prompt=(
            "Compile any new raw sources. Only the newly ingested ones — previously compiled sources should be skipped."
        ),
        depends_on="K14",
        response_matches=[r"(?i)(compiled|eval|article|wiki)"],
    ),
    TestCase(
        id="K16",
        name="Query the new topic",
        group="incremental",
        prompt="What does my knowledge base say about evaluation-driven development?",
        depends_on="K15",
        response_matches=[r"(?i)(eval|EDD|test|criteria|prompt|golden)"],
    ),
    # --- Linter on populated wiki ---
    TestCase(
        id="K17",
        name="Lint populated wiki",
        group="lint",
        prompt="Run a health check on the wiki. Check for gaps, stale articles, and quality issues.",
        depends_on="K05",
        response_matches=[r"(?i)(health|lint|report|article|finding|check|concept)"],
    ),
    # --- Retrieval priority ---
    TestCase(
        id="K18",
        name="Query topic not in wiki",
        group="query-edge",
        prompt="What does my knowledge base say about quantum computing?",
        depends_on="K05",
        response_matches=[r"(?i)(no.*article|not.*cover|don.?t have|no.*content|empty|no.*mention|nothing|not.*found)"],
    ),
    TestCase(
        id="K19",
        name="Broad knowledge summary",
        group="query-edge",
        prompt="Give me a summary of everything in my knowledge base right now.",
        depends_on="K05",
        response_matches=[r"(?i)(context.engineering|agent|vector|prompt|wiki|article|concept)"],
    ),
    TestCase(
        id="K20",
        name="Check wiki state",
        group="query-edge",
        prompt="What's the current state of my wiki? How many articles, when was it last compiled?",
        depends_on="K05",
        response_matches=[r"(?i)(article|compiled|state|count|\d+)"],
    ),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_test(team, test: TestCase, session_id: str | None, user_id: str) -> tuple[TestResult, str | None]:
    start = time.time()
    try:
        run_response = team.run(
            test.prompt,
            user_id=user_id,
            session_id=session_id,
        )
        duration = round(time.time() - start, 2)
        response = run_response.content or ""
        new_session_id = run_response.session_id

        failures: list[str] = []
        for phrase in test.response_contains:
            if phrase.lower() not in response.lower():
                failures.append(f"MISSING: expected '{phrase}'")
        for phrase in test.response_not_contains:
            if phrase.lower() in response.lower():
                failures.append(f"PRESENT: unexpected '{phrase}'")
        for pattern in test.response_matches:
            if not re.search(pattern, response):
                failures.append(f"NO MATCH: '{pattern}'")

        status = "PASS" if not failures else "FAIL"
        return TestResult(test, status, duration, response, failures), new_session_id
    except Exception as e:
        duration = round(time.time() - start, 2)
        return TestResult(test, "ERROR", duration, "", [str(e)]), session_id


def _clean_raw_and_wiki():
    """Clean raw/ and wiki/ before knowledge pipeline tests."""
    import shutil

    from pal.config import PAL_CONTEXT_DIR

    raw_dir = PAL_CONTEXT_DIR / "raw"
    wiki_dir = PAL_CONTEXT_DIR / "wiki"

    # Clear raw files (keep directory)
    if raw_dir.exists():
        for f in raw_dir.iterdir():
            if f.name != ".gitkeep":
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)

    # Clear wiki files (keep directory structure)
    if wiki_dir.exists():
        for f in wiki_dir.iterdir():
            if f.name != ".gitkeep":
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)
        # Recreate subdirs
        (wiki_dir / "concepts").mkdir(exist_ok=True)
        (wiki_dir / "summaries").mkdir(exist_ok=True)
        (wiki_dir / "outputs").mkdir(exist_ok=True)


def run_suite(
    tests: list[TestCase],
    suite_name: str,
    verbose: bool = False,
    user_id: str = "smoke-test@pal.dev",
) -> list[TestResult]:
    from pal.team import pal

    print(f"\n{'=' * 60}")
    print(f"  {suite_name} — {len(tests)} tests")
    print(f"  User: {user_id}")
    print(f"{'=' * 60}")

    results: list[TestResult] = []
    sessions: dict[str, str] = {}
    passed_tests: set[str] = set()
    current_group = None
    skipped = 0

    for test in tests:
        if test.group != current_group:
            current_group = test.group
            print(f"\n--- {current_group} ---\n")

        if test.depends_on and test.depends_on not in passed_tests:
            print(f"  [{test.id}] {test.name}... SKIP (depends on {test.depends_on})")
            skipped += 1
            continue

        session_id = None
        if test.depends_on and test.depends_on in sessions:
            session_id = sessions[test.depends_on]

        print(f"  [{test.id}] {test.name}...", end="", flush=True)
        result, new_session_id = run_test(pal, test, session_id, user_id)
        results.append(result)

        if new_session_id:
            sessions[test.id] = new_session_id
        if result.status == "PASS":
            passed_tests.add(test.id)

        icon = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR "}[result.status]
        print(f" {icon} ({result.duration}s)")

        if result.failures and (verbose or result.status != "PASS"):
            for f in result.failures:
                print(f"         {f}")

        if verbose and result.response:
            preview = result.response[:300].replace("\n", "\n         ")
            print(f"         Response: {preview}")
            if len(result.response) > 300:
                print(f"         ... ({len(result.response)} chars total)")

    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    errors = sum(1 for r in results if r.status == "ERROR")
    total_time = sum(r.duration for r in results)

    print(f"\n{'-' * 60}")
    parts = [f"{passed} passed", f"{failed} failed", f"{errors} errors"]
    if skipped:
        parts.append(f"{skipped} skipped")
    print(f"  {suite_name}: {', '.join(parts)} ({round(total_time, 1)}s)")
    print(f"{'-' * 60}")

    if failed + errors > 0:
        print("\nFAILURES:\n")
        for r in results:
            if r.status in ("FAIL", "ERROR"):
                print(f"  [{r.test.id}] {r.test.name}")
                print(f"  Prompt: {r.test.prompt[:120]}")
                for f in r.failures:
                    print(f"  -> {f}")
                if r.response:
                    print(f"  Response: {r.response[:500]}")
                print()

    return results


def run_extended(verbose: bool = False, user_id: str = "smoke-test@pal.dev"):
    """Run all extended tests: Slack first, then Knowledge Pipeline."""
    all_results: list[TestResult] = []

    # --- Slack tests ---
    slack_results = run_suite(SLACK_TESTS, "Slack Tests", verbose, user_id)
    all_results.extend(slack_results)

    # --- Knowledge pipeline tests (clean state first) ---
    print("\n\n>>> Cleaning raw/ and wiki/ for knowledge pipeline tests...")
    _clean_raw_and_wiki()
    print(">>> Clean. Starting knowledge pipeline tests.\n")

    knowledge_results = run_suite(KNOWLEDGE_TESTS, "Knowledge Pipeline Tests", verbose, user_id)
    all_results.extend(knowledge_results)

    # --- Grand summary ---
    passed = sum(1 for r in all_results if r.status == "PASS")
    failed = sum(1 for r in all_results if r.status == "FAIL")
    errors = sum(1 for r in all_results if r.status == "ERROR")
    total_time = sum(r.duration for r in all_results)

    print(f"\n{'=' * 60}")
    print(f"  GRAND TOTAL: {passed} passed, {failed} failed, {errors} errors ({round(total_time, 1)}s)")
    print(f"{'=' * 60}\n")

    return all_results
