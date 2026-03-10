# Pal

A personal context-agent that learns how you work.

- It works through a set of context files that define common tasks, brand voice, work preferences, templates. These are read on demand to shape behavior.
- It maintains a SQL database of notes, people, projects, and decisions it picks up from your conversations. This helps Pal build a map of your environment over time.
- It connects with tools like Gmail and Google Calendar to gather context and complete tasks as needed.

Built with [Agno](https://docs.agno.com).

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

1. Open [os.agno.com](https://os.agno.com) and login
2. Add OS → Local → `http://localhost:8000`
3. Click "Connect"

## Integrations

Pal starts with SQL + Context Files + Exa. Gmail, Google Calendar, and Slack are pre-wired and activate when you add the relevant environment variables.

<details>
<summary><strong>Gmail + Google Calendar</strong></summary>

Google auth is generally a pain, but you only need to do these steps once. The goal is to get three values: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_PROJECT_ID`.

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

#### 1. Create a Slack app

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App → From scratch**
2. Name it (e.g. `Pal`) and select your workspace

#### 2. Configure bot permissions

1. Go to **OAuth & Permissions** in the sidebar
2. Under **Bot Token Scopes**, add:
   - `app_mentions:read` — respond when mentioned
   - `chat:write` — post messages
   - `chat:write.public` — post to public channels
   - `im:history` — read DM history
   - `im:read` — view DMs
   - `im:write` — send DMs
   - `channels:read` — list public channels

#### 3. Install to workspace

1. Click **Install to Workspace** at the top of the OAuth & Permissions page
2. Authorize the requested permissions
3. Copy the **Bot User OAuth Token** (`xoxb-...`) → `SLACK_TOKEN`

#### 4. Get the signing secret

1. Go to **Basic Information** in the sidebar
2. Under **App Credentials**, copy **Signing Secret** → `SLACK_SIGNING_SECRET`

#### 5. Expose your local server

Slack needs a public URL to send events to Pal. For local development, use ngrok:
```sh
ngrok http 8000
```

Copy the `https://` URL that ngrok provides (e.g. `https://abc123.ngrok-free.app`).

For production, use your deployed URL instead.

#### 6. Configure event subscriptions

1. Go to **Event Subscriptions** in the sidebar and toggle **Enable Events**
2. Set the **Request URL** to: `https://your-ngrok-url.ngrok-free.app/slack/events`
3. Wait for Slack to verify the endpoint (Pal must be running)
4. Under **Subscribe to bot events**, add:
   - `app_mention`
   - `message.im`
   - `message.channels`
   - `message.groups`
5. Click **Save Changes**

#### 7. Enable App Home

1. Go to **App Home** in the sidebar
2. Under **Show Tabs**, enable **Messages Tab**
3. Check **Allow users to send Slash commands and messages from the messages tab**

#### 8. Add to your `.env` and restart
```env
SLACK_TOKEN="xoxb-your-bot-token"
SLACK_SIGNING_SECRET="your-signing-secret"
```

```sh
docker compose up -d --build
```

After changing scopes or event subscriptions, go to **Install App** and click **Reinstall to Workspace** to apply the new permissions.

Thread timestamps map to session IDs, so each Slack thread gets its own conversation context.

</details>

<details>
<summary><strong>Exa Web Research</strong></summary>

Available by default as it's free via their MCP server. Optionally add an API key for authenticated access:

```env
EXA_API_KEY=your-exa-key
```

</details>

## Context Agents: Navigation over Search

When you point Claude Code at a codebase, it navigates. It reads the directory structure, follows imports, checks dependencies, builds a map of where things live. It gets more accurate the more it explores.

Pal applies this pattern to personal and work data. Email is queried by sender and date. A database is queried with SQL. A calendar is queried with time ranges. Files are navigated by structure. Each source is queried on its own terms, and a learning loop improves retrieval with every interaction.

The industry has gone through three generations of context-gathering:

**Generation 1: Traditional RAG.** Embed your documents, store in a vector database, search at query time. RAG gave agents access to large knowledge bases, and the developer adoption was extraordinary. The limitation: everything gets flattened into one interface. A SQL table should be queried with SQL. A calendar should be queried with time ranges. A file system should be navigated by structure.

**Generation 2: Agentic RAG.** Improvements in tool calling made agents reliable enough to decide when to search, run multiple retrievals, and act on results. The underlying architecture remains the bottleneck: agents still search a vector store, still flatten sources, still have no memory of what worked last time.

**Generation 3: Agentic Navigation.** The agent navigates a context graph of heterogeneous sources, each queried on its own terms. It builds a map of where things live, learns which retrieval strategies work, and improves with every interaction. Routing over search as the core retrieval primitive.

Pal is a Generation 3 context agent.

## How It Works

Every interaction follows the same execution loop:

1. **Classify** intent from the user request.
2. **Recall** source metadata and routing patterns from knowledge and learnings.
3. **Retrieve** from the right sources, in the order informed by learnings.
4. **Act** through tool calls.
5. **Learn** so the next request is better.

### Context Systems

Pal maintains four systems that make up its context graph:

1. **Knowledge** (`pal_knowledge`): the map. A metadata index of where things live: file manifests, table schemas, source capabilities, cross-source discoveries. This is a routing layer that tells Pal where to look.

2. **Learnings** (`pal_learnings`): the compass. Operational memory of what works: which retrieval strategies succeeded, recurring user patterns, and explicit user corrections. Corrections always take priority.

3. **Files** (`context/`): the territory. User-authored context files read on demand. Voice guidelines, preferences, templates, and references that shape Pal's behavior. Pal also writes back here: meeting notes, exports, generated documents.

4. **SQL** (`pal_*` tables): structured data. Notes, people, projects, and decisions. Pal owns the schema and creates tables on demand. All queries are scoped to the active user, a hard security boundary.

### Context Directory

The context directory (`PAL_CONTEXT_DIR`, default `./context`) is Pal's primary document store. Files are searched and read on demand, so edits are immediately reflected without reindexing.

**User → Pal**: Place voice guidelines, preferences, templates, and references here. Pal reads them to shape its behavior.

**Pal → User**: Pal writes summaries, exports, and generated documents back here.

```
context/
├── about-me.md             # User background, goals, active projects
├── preferences.md          # Working-style config, file conventions, scheduled tasks
├── voice/                  # Writing tone guides per channel
│   ├── email.md
│   ├── linkedin-post.md
│   ├── x-post.md
│   ├── slack-message.md
│   └── document.md
├── templates/              # Document scaffolds Pal fills per use
│   ├── meeting-notes.md
│   ├── weekly-review.md
│   └── project-brief.md
├── meetings/               # Saved meeting notes and weekly reviews
└── projects/               # Project briefs and docs
```

File deletion is disabled at the code level.

### Context Loading

Preload file metadata into the knowledge map for retrieval routing from inside the container:

```sh
docker compose exec pal-api python context/load_context.py
docker compose exec pal-api python context/load_context.py --recreate   # clear knowledge index and reload
docker compose exec pal-api python context/load_context.py --dry-run    # preview without writing
```

This writes compact `File:` metadata entries (intent tags, size, path) into `pal_knowledge`. File contents are still read on demand by FileTools.

### Intent Classification

Intent classification determines which sources to check and at what depth:

| Intent | Sources | Behavior |
|--------|---------|----------|
| `capture` | SQL | Insert, confirm, done |
| `retrieve` | SQL + Files + Knowledge | Query, present results |
| `connect` | SQL + Files + Gmail + Calendar | Multi-source synthesis |
| `research` | Exa (+ SQL to save) | Search, summarize, optionally save |
| `file_read` / `file_write` | Files | Read or write context directory |
| `email_read` / `email_draft` | Gmail + Files (voice) | Search/read or draft |
| `calendar_read` / `calendar_write` | Calendar | View schedule or create events |

Requests can have multiple intents. "Draft a reply to Sarah's email about Project X" = `email_read` + `retrieve` + `email_draft`.

## Example Prompts

```
Save a note: Met with Sarah Chen from Acme Corp. She's interested in a partnership.
What do I know about Sarah?
Check my latest emails
What's on my calendar this week?
Draft an X post in my voice about AI productivity
Save a summary of today's meeting to meeting-notes.md
What do I know about Project X?
Research web trends on AI productivity
```

## Architecture

```
AgentOS (app/main.py)  [scheduler=True, tracing=True]
 ├── FastAPI / Uvicorn
 ├── Slack Interface (optional)
 └── Pal Agent (pal/agent.py)
     ├─ Model: GPT-5.2
     ├─ SQLTools         → PostgreSQL (pal_* tables)
     ├─ FileTools        → context/
     ├─ MCPTools         → Exa web search
     ├─ update_knowledge → custom tool (pal/tools.py)
     ├─ SlackTools       → Post to Slack channels (requires SLACK_TOKEN)
     ├─ GmailTools       → Gmail (requires Google credentials)
     └─ CalendarTools    → Google Calendar (requires Google credentials)

     Knowledge:  pal_knowledge  (metadata map — where things are)
     Learnings:  pal_learnings  (retrieval patterns — how to navigate)
```

### Sources

| Source | Purpose | Availability |
|--------|---------|--------------|
| SQL (`pal_*`) | Structured notes, people, projects, decisions | Always |
| Files (`context/`) | Voice guides, templates, preferences, references, exports | Always |
| Exa | Web research | Always (API key optional for auth) |
| Slack | Post messages to channels (e.g. scheduled task results to `#pal-updates`) | Requires `SLACK_TOKEN` |
| Gmail | Search, read, draft, label management | Requires all 3 Google credentials |
| Calendar | Event lookup, creation, updates | Requires all 3 Google credentials |

### Storage

| Layer | What goes there |
|-------|----------------|
| PostgreSQL | `pal_*` user tables, `pal_knowledge` + `pal_knowledge_contents`, `pal_learnings` + `pal_learnings_contents`, `pal_contents` |
| `context/` | Voice guides, preferences, templates, references, generated exports |

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | Yes | — | GPT-5.2 |
| `EXA_API_KEY` | No | `""` | Exa web search auth (tool loads regardless) |
| `GOOGLE_CLIENT_ID` | No | `""` | Gmail + Calendar OAuth (all 3 required) |
| `GOOGLE_CLIENT_SECRET` | No | `""` | Gmail + Calendar OAuth (all 3 required) |
| `GOOGLE_PROJECT_ID` | No | `""` | Gmail + Calendar OAuth (all 3 required) |
| `PAL_CONTEXT_DIR` | No | `./context` | Context directory path |
| `SLACK_TOKEN` | No | `""` | Slack bot token (interface + tools) |
| `SLACK_SIGNING_SECRET` | No | `""` | Slack signing secret (interface only) |
| `DB_HOST` | No | `localhost` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |
| `DB_USER` | No | `ai` | PostgreSQL user |
| `DB_PASS` | No | `ai` | PostgreSQL password |
| `DB_DATABASE` | No | `ai` | PostgreSQL database |
| `PORT` | No | `8000` | API port |
| `RUNTIME_ENV` | No | `prd` | `dev` enables hot reload |

## Troubleshooting

**Context prompts stop making sense**: Rerun `python context/load_context.py` to refresh the knowledge map.

**Google token expired**: The app defaults to Google's "Testing" mode, which expires tokens every 7 days. Re-run `python scripts/google_auth.py` to re-authorize. Publishing the app through Google's verification process removes this limit.

**Docker config issues**: Run `docker compose config` and verify optional vars have fallback defaults.

**PAL_CONTEXT_DIR not found**: Ensure the directory is mounted to `./context` in your compose file.

## Links

- [Agno Docs](https://docs.agno.com)
- [AgentOS Docs](https://docs.agno.com/agent-os/introduction)