# Pal (Personal Agent that Learns)

Pal is a Personal Agent that Learns how you work by building a compounding knowledge base.

You feed it raw data — articles, papers, notes, URLs — and Pal compiles a structured wiki: extracting concepts, writing summaries, linking related articles, and maintaining a master index. Scheduled tasks compile new sources daily and run weekly health checks to find gaps, contradictions, and stale articles.

Chat with Pal via Slack, the terminal, or the [AgentOS](https://os.agno.com) web UI. When you ask a question, it navigates across sources to gather context:

1. A knowledge base with raw ingested sources and a compiled wiki of concept articles.
2. A local file system with preferences, voice guidelines, and templates.
2. Tools like Gmail, Google Calendar, and Slack.
3. Self-maintained PostgreSQL database for structured data (notes, people, projects, decisions).
4. The web via Exa search.

Each source keeps its native query interface. Databases get queried with SQL. Email gets queried by sender and date. Files get navigated by directory structure. The wiki gets navigated by its index. A learning loop ties it together: every interaction improves the next one.

Here's a no-speed up video of Pal ingesting a page from the [AgentOS docs](https://docs.agno.com/agent-os/introduction), compiling it into a wiki by breaking it down into numerous concepts, and then answering questions about it in a neutral, no-frills manner.

https://github.com/user-attachments/assets/03a1c5e1-c344-4a2b-b839-dee68a7b0f5e

## Quick Start

```sh
# Clone the repo
git clone https://github.com/agno-agi/pal
cd pal

# Add OPENAI_API_KEY
cp example.env .env
# Edit .env and add your key

# Start the application
docker compose up -d --build

# Load context metadata into the knowledge base
docker compose exec pal-api python context/load_context.py

# Optional: preview what will be loaded without writing
docker compose exec pal-api python context/load_context.py --dry-run
```

Confirm Pal is running at [http://localhost:8000/docs](http://localhost:8000/docs).

### Connect to the Web UI

1. Open [os.agno.com](https://os.agno.com?utm_source=github&utm_medium=example-repo&utm_campaign=agent-example&utm_content=pal&utm_term=agentos) and login
2. Add OS → Local → `http://localhost:8000`
3. Click "Connect"

## How It Works

Pal is a team of five specialists coordinated by a leader:

```
Pal (Team Leader)
├── Navigator    — routes queries, reads wiki, handles email/calendar/SQL/files
├── Researcher   — web search, source gathering, writes to raw/
├── Compiler     — reads raw/, compiles structured wiki articles
├── Linter       — health checks on the wiki, finds gaps
├── Syncer       — commits and pushes context/ changes to GitHub
```

### Knowledge Base Pipeline

Raw data flows through a compilation pipeline:

1. **Ingest** — feed Pal URLs, articles, papers, or text. The Researcher saves them to `context/raw/` with metadata.
2. **Compile** — the Compiler reads raw sources and produces structured wiki articles in `context/wiki/`: concept articles, source summaries, and a master index.
3. **Query** — the Navigator reads the wiki index first for knowledge questions, then pulls specific articles. Falls back to raw sources and live tools.
4. **Lint** — the Linter runs periodic health checks: finds contradictions, stale articles, missing concepts, and suggests research.

```
context/
├── raw/                    # Ingested source material
│   ├── .manifest.json      # Tracks ingest/compile state
│   └── *.md                # Raw docs with YAML frontmatter
└── wiki/                   # LLM-compiled knowledge base
    ├── index.md            # Master index (article summaries)
    ├── concepts/           # One article per concept
    ├── summaries/          # One summary per raw document
    └── outputs/            # Filed query results and reports
```

### Execution Loop

Every interaction follows the same loop:

1. **Classify** intent from the input message.
2. **Recall** metadata and routing patterns from knowledge, learnings, and the wiki index.
3. **Read** from the right sources, in the order informed by learnings.
4. **Act** through tool calls.
5. **Learn** so the next request is better.

### Context Systems

Five systems make up Pal's context graph, plus external tool integrations:

1. **Knowledge** (`pal_knowledge`): A metadata index of where things live: file manifests, table schemas, source capabilities, cross-source discoveries, wiki articles, raw sources. This is a routing layer that tells Pal where to look.

2. **Learnings** (`pal_learnings`): Operational memory of what works: which retrieval strategies succeeded, recurring user patterns, and explicit user corrections. Corrections always take priority.

3. **Wiki** (`context/wiki/`): LLM-compiled knowledge base. Concept articles, source summaries, a master index. The Navigator reads this first for knowledge questions.

4. **Files** (`context/`): User-authored context files read on demand. Voice guidelines, preferences, templates, and references that shape Pal's behavior.

5. **SQL** (`pal_*` tables): Structured data. Notes, people, projects, and decisions. Pal owns the schema and creates tables on demand.

External tools (Gmail, Calendar, Slack, Exa) are queried through their native interfaces and activate when configured.

## Integrations

Pal starts with SQL + Context Files + Exa + Wiki. Gmail, Google Calendar, and Slack are pre-wired and activate when you add the relevant configuration.

<details>
<summary><strong>Gmail + Google Calendar</strong></summary>

Google auth is generally a pain, but you only need to do these steps once. The goal is to get three values: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_PROJECT_ID`.

See [docs/GOOGLE_AUTH.md](docs/GOOGLE_AUTH.md) for the full setup guide, or follow the steps below.

#### 1. Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top-left) → **New Project**
3. Give the project a name (e.g. `agents`) and click **Create**
4. Copy the **Project ID** from the project dashboard and save it as `GOOGLE_PROJECT_ID` in your `.env`

#### 2. Enable the APIs

1. Go to **APIs & Services → Library**
2. Search for and enable **Gmail API**
3. Search for and enable **Google Calendar API**

#### 3. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**
2. Click **Get started** (this opens the Google Auth Platform wizard)
3. **App Information**: Enter an app name (e.g. `pal`) and your support email, click **Next**
4. **Audience**: Select **External**, click **Next**
5. **Contact Information**: Enter your email, click **Next**
6. **Finish**: Click **Create**
7. In the left sidebar, go to **Audience** and add your Google email as a test user

#### 4. Create OAuth credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name it (e.g. `pal-desktop`) and click **Create**
5. Copy **Client ID** → `GOOGLE_CLIENT_ID`
6. Copy **Client secret** → `GOOGLE_CLIENT_SECRET`

#### 5. Add to your `.env`

```env
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GOOGLE_PROJECT_ID="your-google-project-id"
```

#### 6. Generate `token.json`

Run the OAuth script on your local machine:

```sh
set -a; source .env; set +a
python scripts/google_auth.py
```

This opens a browser for Google consent and saves `token.json` to the project root. The script uses `prompt='consent'` to ensure a refresh token is always returned, even on re-authorization.

#### 7. Restart Pal

```sh
docker compose up -d --build
```

Gmail + Google Calendar are now configured. A few things to know:

- Gmail is draft-only. Send tools are disabled at the code level. Thread reading, draft lifecycle (create, list, update), and label management are all enabled.
- Calendar events with external attendees require user confirmation before creation.

</details>

<details>
<summary><strong>Slack</strong></summary>

Slack gives Pal two capabilities: receiving messages from users in Slack threads, and proactively posting to channels (e.g. scheduled task results to `#pal-updates`).

See [docs/SLACK_CONNECT.md](docs/SLACK_CONNECT.md) for the full setup guide with the app manifest.

#### 1. Get a public URL

For local development, use [ngrok](https://ngrok.com/download/mac-os):

```sh
ngrok http 8000
```

Copy the `https://` URL (e.g. `https://abc123.ngrok-free.app`).

#### 2. Create app from manifest

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App → From a manifest**
2. Select your workspace, switch to **JSON**
3. Paste the manifest from [docs/SLACK_CONNECT.md](docs/SLACK_CONNECT.md) — replace `YOUR_URL_HERE` with your URL
4. Click **Create**

#### 3. Install and get credentials

1. **Install to Workspace** and authorize
2. Copy **Bot User OAuth Token** (`xoxb-...`) → `SLACK_TOKEN`
3. Go to **Basic Information → App Credentials**, copy **Signing Secret** → `SLACK_SIGNING_SECRET`

#### 4. Add to `.env` and restart

```env
SLACK_TOKEN="xoxb-your-bot-token"
SLACK_SIGNING_SECRET="your-signing-secret"
```

```sh
docker compose up -d --build
```

Thread timestamps map to session IDs, so each Slack thread gets its own conversation context.

</details>

<details>
<summary><strong>Parallel Web Research</strong></summary>

Parallel enables the Researcher agent with full web search and content extraction. When configured, `ingest_url` automatically fetches page content instead of creating stubs.

```env
PARALLEL_API_KEY=your-parallel-key
```

Get a key at [parallel.ai](https://parallel.ai).

Without this key, the Researcher agent is disabled. Navigator and Linter still have basic web search via Exa.

</details>

<details>
<summary><strong>Exa Web Search</strong></summary>

Available by default as it's free via their MCP server. Used by Navigator and Linter for general web search. Optionally add an API key for authenticated access:

```env
EXA_API_KEY=your-exa-key
```

</details>

## Example Prompts

```
Save a note: Met with Sarah Chen from Acme Corp. She's interested in a partnership.
What do I know about Sarah?
Check my latest emails
What's on my calendar this week?
Draft an X post in my voice about AI productivity
Save a summary of today's meeting to meeting-notes.md
Research web trends on AI productivity
Ingest this article: https://example.com/article-on-rag
Compile the wiki
What does my knowledge base say about context engineering?
Lint the wiki
```

## Scheduled Tasks

Pal comes with eight automated tasks on a cron schedule (all times `America/New_York`):

| Task | Schedule | Description |
|------|----------|-------------|
| Context Refresh | Daily 8 AM | Re-indexes context files into the knowledge map |
| Daily Briefing | Weekdays 8 AM | Morning briefing — calendar, emails, priorities |
| Wiki Compile | Daily 9 AM | Process new raw sources into wiki articles |
| Inbox Digest | Weekdays 12 PM | Midday email digest (requires Gmail) |
| Learning Summary | Monday 10 AM | Weekly summary of the learning system |
| Weekly Review | Friday 5 PM | End-of-week review draft |
| Wiki Lint | Sunday 8 AM | Wiki health check — find issues, suggest improvements |
| Sync Pull | Every 30 min | Pull remote context/ changes from GitHub |

Each task can post its results to Slack (requires `SLACK_TOKEN`).

## Architecture

```
AgentOS (app/main.py)  [scheduler=True, tracing=True]
 ├── FastAPI / Uvicorn
 ├── Slack Interface (optional)
 ├── Custom Router (/context/reload, /wiki/compile, /wiki/lint, /wiki/ingest, /sync/pull)
 └── Pal Team (pal/team.py, coordinate mode)
     ├─ Navigator (pal/agents/navigator.py)
     │  ├─ SQLTools         → PostgreSQL (pal_* tables)
     │  ├─ FileTools        → context/
     │  ├─ MCPTools         → Exa web search
     │  ├─ update_knowledge → custom tool
     │  ├─ Wiki read tools  → read_wiki_index, read_wiki_state
     │  ├─ GmailTools       → Gmail (optional)
     │  └─ CalendarTools    → Google Calendar (optional)
     ├─ Researcher (pal/agents/researcher.py) [conditional]
     │  ├─ FileTools, ParallelTools (search + extract), update_knowledge
     │  └─ ingest_url (auto-fetch), ingest_text, read_manifest
     ├─ Compiler (pal/agents/compiler.py)
     │  ├─ FileTools, update_knowledge
     │  ├─ read_manifest, update_manifest_compiled
     │  └─ Wiki tools (read/update index, read/update state)
     ├─ Linter (pal/agents/linter.py)
     │  ├─ FileTools, MCPTools (Exa), update_knowledge
     │  └─ Wiki tools (read index, read/update state)
     └─ Syncer (pal/agents/syncer.py) [conditional]
        └─ sync_push, sync_pull, sync_status

     Leader tools: SlackTools (post to channels)
     Knowledge:    pal_knowledge (metadata routing)
     Learnings:    pal_learnings (retrieval patterns — Navigator only)
```

### Sources

| Source | Purpose | Availability |
|--------|---------|--------------|
| Wiki (`context/wiki/`) | Compiled knowledge base — concept articles, summaries, index | Always |
| Raw (`context/raw/`) | Ingested source material — articles, papers, notes | Always |
| SQL (`pal_*`) | Structured notes, people, projects, decisions | Always |
| Files (`context/`) | Voice guides, templates, preferences, references, exports | Always |
| Parallel | Web research + content extraction (Researcher) | Requires `PARALLEL_API_KEY` |
| Exa | General web search (Navigator, Linter) | Always (API key optional for auth) |
| Slack | Post messages to channels | Requires `SLACK_TOKEN` |
| Gmail | Search, read, draft, label management | Requires all 3 Google credentials |
| Calendar | Event lookup, creation, updates | Requires all 3 Google credentials |

### Storage

| Layer | What goes there |
|-------|----------------|
| PostgreSQL | `pal_knowledge`, `pal_learnings`, `pal_contents`, `pal_*` user tables |
| `context/raw/` | Ingested source documents with YAML frontmatter |
| `context/wiki/` | LLM-compiled knowledge base (index, concepts, summaries, outputs) |
| `context/` | Voice guides, preferences, templates, generated exports |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/teams/pal/runs` | POST | Run the Pal team with a prompt |
| `/context/reload` | POST | Re-index context files into pal_knowledge |
| `/wiki/compile` | POST | Trigger wiki compilation |
| `/wiki/lint` | POST | Trigger wiki health check |
| `/wiki/ingest` | POST | Ingest a URL or text into raw/ |
| `/sync/pull` | POST | Pull remote context/ changes from GitHub |

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | Yes | — | GPT-5.4 |
| `PARALLEL_API_KEY` | No | `""` | Parallel web research — enables Researcher agent |
| `EXA_API_KEY` | No | `""` | Exa web search for Navigator + Linter (tool loads regardless) |
| `GOOGLE_CLIENT_ID` | No | `""` | Gmail + Calendar OAuth (all 3 required) |
| `GOOGLE_CLIENT_SECRET` | No | `""` | Gmail + Calendar OAuth (all 3 required) |
| `GOOGLE_PROJECT_ID` | No | `""` | Gmail + Calendar OAuth (all 3 required) |
| `PAL_CONTEXT_DIR` | No | `./context` | Context directory path |
| `SLACK_TOKEN` | No | `""` | Slack bot token (interface + tools) |
| `SLACK_SIGNING_SECRET` | No | `""` | Slack signing secret (interface only) |
| `GITHUB_ACCESS_TOKEN` | No | `""` | Git sync — push context/ to GitHub (both required) |
| `PAL_REPO_URL` | No | `""` | Git sync — repo URL (both required) |
| `DB_HOST` | No | `localhost` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |
| `DB_USER` | No | `ai` | PostgreSQL user |
| `DB_PASS` | No | `ai` | PostgreSQL password |
| `DB_DATABASE` | No | `ai` | PostgreSQL database |
| `PORT` | No | `8000` | API port |
| `RUNTIME_ENV` | No | `prd` | `dev` enables hot reload |
| `AGENTOS_URL` | No | `http://127.0.0.1:8000` | Scheduler callback URL (production) |
| `JWT_VERIFICATION_KEY` | Production | — | RBAC public key from os.agno.com |

## Troubleshooting

**Context prompts stop making sense**: Rerun `python context/load_context.py` to refresh the knowledge map.

**Google token expired**: The app defaults to Google's "Testing" mode, which expires tokens every 7 days. Re-run `python scripts/google_auth.py` to re-authorize. Publishing the app through Google's verification process removes this limit.

**Docker config issues**: Run `docker compose config` and verify optional vars have fallback defaults.

**PAL_CONTEXT_DIR not found**: Ensure the directory is mounted to `./context` in your compose file.

## Links

- [Agno Docs](https://docs.agno.com?utm_source=github&utm_medium=example-repo&utm_campaign=agent-example&utm_content=pal&utm_term=docs)
- [AgentOS Docs](https://docs.agno.com/agent-os/introduction?utm_source=github&utm_medium=example-repo&utm_campaign=agent-example&utm_content=pal&utm_term=docs)
