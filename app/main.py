"""
Pal AgentOS
============

The main entry point for Pal.

Run:
    python -m app.main
"""

from contextlib import asynccontextmanager
from os import getenv
from pathlib import Path

from agno.os import AgentOS

from app.router import create_router
from db import get_postgres_db
from pal.agents import compiler, linter, navigator, researcher, syncer
from pal.agents.settings import pal_knowledge, pal_learnings
from pal.config import GIT_SYNC_ENABLED, PAL_REPO_URL, SLACK_SIGNING_SECRET, SLACK_TOKEN
from pal.team import pal

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
runtime_env = getenv("RUNTIME_ENV", "prd")
scheduler_base_url = getenv("AGENTOS_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------
interfaces: list = []
if SLACK_TOKEN and SLACK_SIGNING_SECRET:
    from agno.os.interfaces.slack import Slack

    interfaces.append(
        Slack(
            team=pal,
            streaming=True,
            token=SLACK_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET,
            resolve_user_identity=True,
        )
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    _init_git_sync()
    _register_schedules()
    yield


# ---------------------------------------------------------------------------
# Create AgentOS
# ---------------------------------------------------------------------------
agents: list = [a for a in [navigator, researcher, compiler, linter, syncer] if a is not None]

agent_os = AgentOS(
    name="Pal",
    tracing=True,
    scheduler=True,
    scheduler_base_url=scheduler_base_url,
    authorization=runtime_env == "prd",
    lifespan=lifespan,
    db=get_postgres_db(),
    teams=[pal],
    agents=agents,
    knowledge=[pal_knowledge, pal_learnings],
    interfaces=interfaces,
    config=str(Path(__file__).parent / "config.yaml"),
)

app = agent_os.get_app()
app.include_router(create_router(agent_os.settings))


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------
def _init_git_sync() -> None:
    """Initialize context/ as a git repo and pull latest from GitHub."""
    if not GIT_SYNC_ENABLED:
        return
    from pal.tools.git import init_context_repo

    result = init_context_repo(PAL_REPO_URL)
    print(f"[pal] Git sync: {result}")


def _register_schedules() -> None:
    """Register all scheduled tasks (idempotent — safe to run on every startup)."""
    from agno.scheduler import ScheduleManager

    mgr = ScheduleManager(get_postgres_db())
    slack_post = "\n\nWhen done, post the results to the #pal-updates Slack channel." if SLACK_TOKEN else ""

    mgr.create(
        name="context-refresh",
        cron="0 8 * * *",
        endpoint="/context/reload",
        payload={},
        timezone="America/New_York",
        description="Daily context file re-index",
        if_exists="update",
    )

    mgr.create(
        name="daily-briefing",
        cron="0 8 * * 1-5",
        endpoint="/teams/pal/runs",
        payload={
            "message": (
                "Good morning. Give me a quick briefing to start the day:\n"
                "1. Check today's calendar — list events with times, flag any that need prep.\n"
                "2. Summarize unread or flagged emails (if Gmail is enabled).\n"
                "3. List my open priorities and action items from recent conversations.\n"
                "Keep it short — a morning scan, not a full report." + slack_post
            ),
        },
        timezone="America/New_York",
        description="Weekday morning briefing — calendar, emails, priorities",
        if_exists="update",
    )

    mgr.create(
        name="wiki-compile",
        cron="0 9 * * *",
        endpoint="/teams/pal/runs",
        payload={
            "message": (
                "Compile any new raw sources into the wiki.\n"
                "1. Check the manifest for uncompiled documents.\n"
                "2. For each uncompiled document, read it, write summaries and concept articles.\n"
                "3. Update the wiki index and state.\n"
                "4. Mark compiled documents in the manifest.\n\n"
                "If there are no new documents, just confirm the wiki is up to date."
            ),
        },
        timezone="America/New_York",
        description="Daily wiki compilation — process new raw sources into articles",
        if_exists="update",
    )

    mgr.create(
        name="inbox-digest",
        cron="0 12 * * 1-5",
        endpoint="/teams/pal/runs",
        payload={
            "message": (
                "Midday inbox digest:\n"
                "1. Summarize emails from this morning — group by sender or thread.\n"
                "2. Flag anything that needs a response today.\n"
                "3. Note any action items with owners and deadlines." + slack_post
            ),
        },
        timezone="America/New_York",
        description="Weekday midday email digest (requires Gmail)",
        if_exists="update",
    )

    mgr.create(
        name="learning-summary",
        cron="0 10 * * 1",
        endpoint="/teams/pal/runs",
        payload={
            "message": (
                "Monday learning check-in:\n"
                "1. Query what you've learned about me recently from pal_learnings.\n"
                "2. Summarize patterns, preferences, and insights you've picked up.\n"
                "3. Note anything that seems wrong or worth revisiting." + slack_post
            ),
        },
        timezone="America/New_York",
        description="Monday morning learning system summary",
        if_exists="update",
    )

    mgr.create(
        name="weekly-review",
        cron="0 17 * * 5",
        endpoint="/teams/pal/runs",
        payload={
            "message": (
                "It's Friday — time for a weekly review.\n"
                "1. Read context/templates/weekly-review.md for the structure.\n"
                "2. Fill it in based on this week's conversations, decisions, and action items.\n"
                "3. Save the draft to context/meetings/ using the filename format "
                "YYYY-MM-DD - weekly-review.md (use today's date)." + slack_post
            ),
        },
        timezone="America/New_York",
        description="Friday afternoon weekly review draft",
        if_exists="update",
    )

    mgr.create(
        name="wiki-lint",
        cron="0 8 * * 0",
        endpoint="/teams/pal/runs",
        payload={
            "message": (
                "Run a health check on the wiki.\n"
                "1. Check for contradictions, stale articles, missing concepts.\n"
                "2. Find orphaned and thin articles.\n"
                "3. Suggest research topics and merge candidates.\n"
                "4. Write a lint report to context/wiki/lint-report.md." + slack_post
            ),
        },
        timezone="America/New_York",
        description="Weekly wiki health check — find issues, suggest improvements",
        if_exists="update",
    )

    if GIT_SYNC_ENABLED:
        mgr.create(
            name="sync-pull",
            cron="*/30 * * * *",
            endpoint="/sync/pull",
            payload={},
            timezone="UTC",
            description="Pull remote context/ changes from GitHub every 30 minutes",
            if_exists="update",
        )


if __name__ == "__main__":
    agent_os.serve(
        app="app.main:app",
        reload=runtime_env == "dev",
    )
