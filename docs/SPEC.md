# Pal Specification

Pal is a personal knowledge agent that learns how you work and builds a compounding knowledge base.

It navigates heterogeneous data sources — files, email, calendar, SQL, and web — using each source's native query interface. Raw data goes in, a structured wiki comes out, and every interaction compounds. A learning loop ties it together: every interaction improves the next one.

## Architecture

```
AgentOS (app/main.py)  [scheduler=True, tracing=True]
├── FastAPI / Uvicorn (port 8000)
├── Slack Interface (optional, thread-based sessions)
├── Custom Router (/context/reload, /wiki/compile, /wiki/lint, /wiki/ingest, /sync/pull)
│
└── Pal (Team Leader — coordinate mode, gpt-5.4)
    ├── Navigator    — routes queries, reads wiki, handles email/calendar/SQL/files
    ├── Researcher   — web search, source gathering, writes to raw/
    ├── Compiler     — reads raw/, writes wiki articles, maintains index
    ├── Linter       — health checks, finds gaps, suggests research
    ├── Syncer       — commits and pushes context/ changes to GitHub (conditional)
    └── Shared:
        ├── Knowledge: pal_knowledge (metadata routing)
        ├── Learnings: pal_learnings (operational memory)
        ├── SQL: pal_* tables (structured user data)
        ├── Files: context/ (user files + raw + wiki)
        └── Tools: Gmail, Calendar, Slack, Exa (conditional)
```

**Infrastructure:**
- **Framework**: [Agno](https://docs.agno.com) (agents, teams, knowledge, tools, orchestration)
- **Model**: OpenAI GPT-5.4 via `OpenAIResponses`
- **Database**: PostgreSQL 18 with pgvector (hybrid vector + keyword search)
- **Embeddings**: `text-embedding-3-small`
- **Container**: Docker + Docker Compose
- **Language**: Python 3.12+, managed with `uv`

**Database layout**: User-created SQL tables (`pal_notes`, `pal_people`, etc.) live in a separate `pal` PostgreSQL schema, isolated from Agno framework tables in the default schema. The SQL engine bootstraps the schema at startup (`CREATE SCHEMA IF NOT EXISTS pal`) and sets `search_path=pal,public` so agents query user tables by default.

## Core Capabilities

### 1. Knowledge Base Pipeline

Raw data flows through a compilation pipeline into a structured wiki:

```
Ingest (Researcher)     →  context/raw/     →  .manifest.json tracks state
Compile (Compiler)      →  context/wiki/    →  concepts/, summaries/, index.md
Query (Navigator)       →  reads wiki index →  pulls specific articles
File outputs (Navigator)→  wiki/outputs/    →  compounds back into wiki
Lint (Linter)           →  wiki/lint-report →  finds gaps, suggests research
```

- **Raw documents** have YAML frontmatter (title, source, date, tags, type, compiled status)
- **Wiki articles** have frontmatter (title, dates, sources, related concepts, tags)
- **Wiki index** lists all articles with 1-line summaries — fits in one LLM read (~5K tokens at 100 articles)
- **Manifest** tracks compile state per raw file — incremental, never rewrites the whole wiki

### 2. Context Navigation

Intent classification determines which sources to check:

| Intent | Sources | Behavior |
|--------|---------|----------|
| `capture` | SQL | Insert, confirm, done |
| `retrieve` | Wiki + SQL + Files + Knowledge | Query, present results |
| `connect` | Wiki + SQL + Files + Gmail + Calendar | Multi-source synthesis |
| `research` | Exa (+ raw/ to save) | Search, summarize, optionally ingest |
| `ingest` | raw/ | Save article/URL/text to raw/ |
| `compile` | raw/ → wiki/ | Process uncompiled sources into articles |
| `lint` | wiki/ | Health check, find gaps |
| `file_read` / `file_write` | Files | Read or write context directory |
| `email_read` / `email_draft` | Gmail + Files (voice) | Search/read or draft |
| `calendar_read` / `calendar_write` | Calendar | View schedule or create events |
| `organize` | SQL | Propose restructuring, execute on confirmation |
| `meta` | Knowledge + Learnings | Questions about Pal itself |

### 3. Execution Loop

Every interaction follows five steps:

1. **Classify** — Determine intent from the user request.
2. **Recall** — Search knowledge, learnings, wiki index, and files.
3. **Read** — Pull from identified sources. Wiki-first for knowledge questions.
4. **Act** — Execute tool calls.
5. **Learn** — Save discoveries, retrieval strategies, and patterns.

### 4. Dual Knowledge System

- **`pal_knowledge`** — Metadata index (routing layer). File manifests (`File:`), table schemas (`Schema:`), source capabilities (`Source:`), cross-source discoveries (`Discovery:`), wiki articles (`Wiki:`), raw sources (`Raw:`).
- **`pal_learnings`** — Operational memory. Retrieval strategies (`Retrieval:`), recurring patterns (`Pattern:`), explicit user corrections (`Correction:`). Corrections always take priority.

**Bootstrap**: `context/load_context.py` populates `pal_knowledge` on first run by scanning the context directory, parsing YAML frontmatter for tags, and inserting `File:` metadata entries. This is the bootstrap step that makes Navigator's recall work — without it, the knowledge routing layer is empty. Supports `--recreate` (clear and reload) and `--dry-run` (preview). Also exposed via `/context/reload` endpoint and scheduled daily.

### 5. Learning System

Navigator uses Agno's `LearningMachine` with `AGENTIC` mode — the agent autonomously decides what to learn from each interaction and saves it to `pal_learnings`. This is the mechanism behind the "learns how you work" promise. Manual learning via `save_learning` tool calls is supplementary.

### 6. Agent Memory Tiers

Not all agents need memory. The team uses a tiered approach:

- **Leader + Navigator**: Full memory — agentic memory, past session search, chat history. These are the agents with user-facing continuity across conversations.
- **Researcher, Compiler, Linter, Syncer**: Datetime context only. No memory, no session search. These are stateless workers that get fresh context per invocation.

This keeps worker agents fast and focused while the user-facing agents maintain conversational continuity.

### 7. Context Directory

```
context/
├── about-me.md             # User background, goals
├── preferences.md          # Working style, file conventions
├── voice/                  # Tone guides (email, slack, x, document)
├── templates/              # Document scaffolds
├── meetings/               # Saved meeting notes
├── projects/               # Project briefs
├── raw/                    # Ingested source material
│   ├── .manifest.json      # Ingest/compile state tracking
│   └── *.md                # Raw documents with YAML frontmatter
└── wiki/                   # LLM-compiled knowledge base
    ├── index.md            # Master index with article summaries
    ├── .state.json         # Compile/lint timestamps and counts
    ├── concepts/           # One article per concept
    ├── summaries/          # One summary per raw document
    └── outputs/            # Filed query results and reports
```

### 8. Email (Gmail)

- Search, read threads, create drafts, manage labels.
- Send is disabled at the code level. Always creates drafts.
- Requires: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID`.

### 9. Calendar (Google Calendar)

- View schedule, create events, update events, find available slots.
- Events with external attendees require user confirmation.
- Requires: same three Google credentials as Gmail.

### 10. Slack

- **Receiving**: DMs, @mentions, thread replies. Each thread = session.
- **Sending**: Leader posts to channels (scheduled tasks, user requests).
- Requires: `SLACK_TOKEN` + `SLACK_SIGNING_SECRET`.

### 11. Web Research

- **Parallel** (Researcher): Search + extract via `parallel_search` and `parallel_extract`. Requires `PARALLEL_API_KEY`. When configured, Researcher is active and `ingest_url` auto-fetches content.
- **Exa** (Navigator, Linter): General web search via Exa MCP server (always loaded). `EXA_API_KEY` optional for authenticated access.

### 12. Scheduled Tasks

| Task | Schedule | Endpoint | Description |
|------|----------|----------|-------------|
| Context Refresh | Daily 8 AM | `/context/reload` | Re-indexes context files into knowledge |
| Daily Briefing | Weekdays 8 AM | `/teams/pal/runs` | Calendar, emails, priorities |
| Wiki Compile | Daily 9 AM | `/teams/pal/runs` | Process new raw/ files into wiki articles |
| Inbox Digest | Weekdays 12 PM | `/teams/pal/runs` | Midday email digest |
| Learning Summary | Monday 10 AM | `/teams/pal/runs` | Weekly learning system summary |
| Weekly Review | Friday 5 PM | `/teams/pal/runs` | End-of-week review draft |
| Wiki Lint | Sunday 8 AM | `/teams/pal/runs` | Wiki health check |
| Sync Pull | Every 30 min | `/sync/pull` | Pull remote context/ changes from GitHub |

**Routing**: Most tasks go through `/teams/pal/runs` (full team orchestration — leader routes to the right agent). Context Refresh and Sync Pull hit direct endpoints that bypass the team.

**Slack post-back**: When `SLACK_TOKEN` is set, team-routed tasks append "post the results to #pal-updates" to their prompt so the leader posts a summary after completion.

## Agents

### Pal (Team Leader)

Routes requests to specialists or responds directly for simple things.

| Request Type | Agent |
|-------------|-------|
| Knowledge queries, email, calendar, SQL, files | Navigator |
| "Ingest this", research a topic | Researcher |
| "Compile the wiki" | Compiler |
| "Lint the wiki", "find gaps" | Linter |
| Greetings, thanks, "what can you do?" | Direct response |

Tools: SlackTools (leader-only).

### Navigator

Primary agent for user interaction. Handles email, calendar, SQL, files, web search, and wiki-aware Q&A.

Tools: SQLTools, FileTools, MCPTools (Exa), GmailTools, CalendarTools, update_knowledge, read_wiki_index, read_wiki_state.

Navigator cannot post to Slack — that's the leader's job. Slack instructions are always disabled for Navigator regardless of whether `SLACK_TOKEN` is set.

Wiki retrieval priority: `wiki/concepts/` → `wiki/summaries/` → `raw/` → live sources.

### Researcher

Gathers sources from the web, extracts content, converts to clean markdown, saves to `raw/`.

Tools: FileTools, ParallelTools (parallel_search, parallel_extract), update_knowledge, ingest_url (auto-fetches via Parallel), ingest_text, read_manifest.

Conditional — only instantiated when `PARALLEL_API_KEY` is set. Without it, Navigator handles basic web search via Exa.

Does NOT compile wiki articles, modify wiki/, or interact with email/calendar/slack.

### Compiler

Reads uncompiled raw documents and produces/updates wiki articles.

Tools: FileTools, update_knowledge, read_manifest, update_manifest_compiled, read_wiki_index, update_wiki_index, read_wiki_state, update_wiki_state.

Design principles: incremental, additive, source-tracked, index-first.

Does NOT interact with users, query live sources, or run web searches.

### Linter

Periodic health checks on the wiki.

Tools: FileTools, MCPTools (Exa), update_knowledge, read_wiki_index, read_wiki_state, update_wiki_state.

Checks: contradictions, stale articles, missing concepts, orphans, thin articles, duplicates, gap analysis.

### Syncer

Commits and pushes context/ changes to GitHub. Called by the leader after any workflow that creates or modifies files. Writes descriptive commit messages.

Tools: sync_push, sync_pull, sync_status.

Conditional — only included if `GITHUB_ACCESS_TOKEN` and `PAL_REPO_URL` are set.

Push is event-driven (chained by leader after work). Pull is scheduled (every 30 min) and runs at startup.

## Git-Backed Persistence

Git replaces volumes as the persistence layer for context/. This enables horizontal scaling (no shared disk), portability (pull locally, read in Obsidian), and durability (GitHub is the backup).

```
Container startup → git pull (get latest from remote)
User ingests → Researcher writes to raw/ → Syncer pushes
Scheduled compile → Compiler writes to wiki/ → Syncer pushes
User edits locally → git push → Syncer pulls on next cycle (every 30 min)
```

Requires: `GITHUB_ACCESS_TOKEN` (fine-grained PAT with Contents RW) and `PAL_REPO_URL`.

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/teams/pal/runs` | POST | Run the Pal team with a prompt |
| `/context/reload` | POST | Re-index context files |
| `/wiki/compile` | POST | Trigger wiki compilation |
| `/wiki/lint` | POST | Trigger wiki health check |
| `/wiki/ingest` | POST | Ingest URL or text to raw/ |
| `/sync/pull` | POST | Pull remote context/ changes from GitHub |

## Governance

1. **No external side effects without confirmation.** Calendar events with attendees, messages to others — always confirm first.
2. **Personal events are free.** No external attendees = no confirmation needed.
3. **No file deletion.** Disabled at the code level.
4. **No email sending.** Send tools excluded. Always create drafts.
5. **No cross-user data access.** All queries scoped to `user_id`.

## Startup

All 8 scheduled tasks register at startup via a lifespan context manager in `app/main.py` (idempotent, `if_exists="update"`).

Production authorization is enabled when `RUNTIME_ENV=prd` via `authorization=runtime_env == "prd"` on AgentOS. This requires a `JWT_VERIFICATION_KEY` from os.agno.com.

## Design Constraints

1. **Navigation over search.** Each source keeps its native query interface.
2. **Metadata in vectors, content on demand.** Knowledge stores routing information, not raw data.
3. **Learning is agentic.** The agent decides what to learn. Corrections always take priority.
4. **Graceful degradation.** Missing credentials disable capabilities with clear fallback messages.
5. **Incremental compilation.** Wiki compilation only processes new raw files. Never rewrites the whole wiki.
6. **Index-first routing.** The wiki index is designed to fit in one LLM read for fast article selection.
7. **Thread-as-session.** Slack thread timestamps map to session IDs.
8. **Slack is leader-only.** Only the team leader can post to Slack. Member agents cannot.
9. **Git is the persistence layer.** No volumes needed. Context/ is synced to GitHub via the Syncer agent. Push is event-driven, pull is scheduled.
