"""Tool assembly — builds tool lists for each agent role."""

from agno.knowledge import Knowledge
from agno.tools.file import FileTools
from agno.tools.mcp import MCPTools
from agno.tools.parallel import ParallelTools
from agno.tools.sql import SQLTools

from db import PAL_SCHEMA, get_sql_engine
from pal.config import (
    EXA_MCP_URL,
    GOOGLE_INTEGRATION_ENABLED,
    PAL_CONTEXT_DIR,
)
from pal.tools.git import create_sync_tools
from pal.tools.ingest import create_ingest_tools
from pal.tools.knowledge import create_update_knowledge
from pal.tools.wiki import create_wiki_tools

RAW_DIR = PAL_CONTEXT_DIR / "raw"
WIKI_DIR = PAL_CONTEXT_DIR / "wiki"


def build_navigator_tools(knowledge: Knowledge) -> list:
    """Tools for the Navigator agent — email, calendar, SQL, files, Exa, wiki reading."""
    tools: list = [
        SQLTools(db_engine=get_sql_engine(), schema=PAL_SCHEMA),
        FileTools(base_dir=PAL_CONTEXT_DIR, enable_delete_file=False),
        create_update_knowledge(knowledge),
        MCPTools(url=EXA_MCP_URL),
    ]

    # create_wiki_tools returns: [read_index, update_index, read_state, update_state]
    read_wiki_index, _, read_wiki_state, _ = create_wiki_tools(WIKI_DIR)
    tools.extend([read_wiki_index, read_wiki_state])

    if GOOGLE_INTEGRATION_ENABLED:
        from agno.tools.google.calendar import GoogleCalendarTools
        from agno.tools.google.gmail import GmailTools

        tools.append(GmailTools(send_email=False, send_email_reply=False, list_labels=True))
        tools.append(GoogleCalendarTools(allow_update=True))

    return tools


def build_researcher_tools(knowledge: Knowledge) -> list:
    """Tools for the Researcher agent — Parallel search/extract + ingest to raw/."""
    ingest_url, ingest_text, read_manifest, _ = create_ingest_tools(RAW_DIR)
    return [
        FileTools(base_dir=PAL_CONTEXT_DIR, enable_delete_file=False),
        ParallelTools(),
        create_update_knowledge(knowledge),
        ingest_url,
        ingest_text,
        read_manifest,
    ]


def build_compiler_tools(knowledge: Knowledge) -> list:
    """Tools for the Compiler agent — reads raw/, writes wiki/."""
    _, _, read_manifest, update_compiled = create_ingest_tools(RAW_DIR)
    return [
        FileTools(base_dir=PAL_CONTEXT_DIR, enable_delete_file=False),
        create_update_knowledge(knowledge),
        read_manifest,
        update_compiled,
        *create_wiki_tools(WIKI_DIR),
    ]


def build_linter_tools(knowledge: Knowledge) -> list:
    """Tools for the Linter agent — reads wiki/, writes lint reports, web search for gaps."""
    read_wiki_index, _, read_wiki_state, update_wiki_state = create_wiki_tools(WIKI_DIR)
    return [
        FileTools(base_dir=PAL_CONTEXT_DIR, enable_delete_file=False),
        MCPTools(url=EXA_MCP_URL),
        create_update_knowledge(knowledge),
        read_wiki_index,
        read_wiki_state,
        update_wiki_state,
    ]


def build_syncer_tools() -> list:
    """Tools for the Syncer agent — git commit + push context/, pull remote."""
    return create_sync_tools()
