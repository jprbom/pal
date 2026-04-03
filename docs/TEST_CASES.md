# Test Cases

Manual test prompts for verifying Pal's capabilities. Run these against a fresh or existing instance.

## Context Navigation

```
What do you know about my voice guidelines?
```

```
Read my preferences file
```

```
What templates are available?
```

```
What's in my about-me?
```

## Capture & Retrieve

```
Save a note: Met with Sarah Chen from Acme Corp. She's interested in a partnership.
```

```
What do I know about Sarah?
```

```
Save a note: Project Atlas kickoff is next Tuesday. Attendees: Sarah Chen, Mike Torres.
```

```
What do I know about Project Atlas?
```

```
Show me all my notes tagged with 'project-x'
```

## File Operations

```
Save a summary of today's tasks to a file called daily-summary.md
```

```
List all files in the context directory
```

```
What meeting notes do I have?
```

## Email (requires Google credentials)

```
Check my latest emails
```

```
Any emails from Sarah this week?
```

```
Draft a reply to the most recent email from Sarah about the partnership
```

```
Show me unread emails from today
```

## Calendar (requires Google credentials)

```
What's on my calendar this week?
```

```
Am I free tomorrow afternoon?
```

```
Create a meeting called "Atlas Sync" for tomorrow at 2pm, 30 minutes
```

```
What meetings do I have today?
```

## Web Research

```
Research web trends on AI productivity
```

```
What's the latest on LLM agents in production?
```

```
Find recent articles about context engineering
```

## Cross-Source Synthesis

```
Prepare me for my next meeting — check my calendar, any related emails, and notes about the attendees
```

```
What do I know about Project Atlas? Check notes, emails, and calendar.
```

```
Give me a full briefing on Sarah Chen — notes, emails, calendar events
```

## Slack (requires Slack credentials)

```
Post a summary of my day to #pal-updates
```

```
What channels are available?
```

## Multi-Intent

```
Draft a reply to Sarah's email about Project X
```
Expected: `email_read` + `retrieve` + `email_draft` — reads email, checks notes for context, creates draft.

```
Check my calendar and draft an email to Mike about rescheduling tomorrow's meeting
```
Expected: `calendar_read` + `email_draft` — reads calendar, drafts email.

## Knowledge & Learning

```
What have you learned so far?
```

```
What do you know about where my data lives?
```

```
What retrieval strategies have worked well?
```

## Fallback Behavior (without optional integrations)

```
Check my latest emails
```
Expected (no Google): "Gmail isn't set up yet. Follow the setup guide in `docs/GOOGLE_AUTH.md` to connect your Google account."

```
What's on my calendar?
```
Expected (no Google): "Google Calendar isn't set up yet. Follow the setup guide in `docs/GOOGLE_AUTH.md` to connect your Google account."

```
Post this to Slack
```
Expected (no Slack): "Slack isn't set up yet. Follow the setup guide in `docs/SLACK_CONNECT.md` to connect your workspace."

## Ingest (Researcher)

```
Ingest this article: https://example.com/article-on-rag
```
Expected: Researcher creates a stub in `context/raw/` with YAML frontmatter, updates `.manifest.json`.

```
Research RAG techniques and save the top 3 articles
```
Expected: Researcher searches via Parallel, ingests multiple sources to `raw/`.

```
Save this as a raw source: [paste text here]
```
Expected: Researcher uses `ingest_text` to save to `raw/`.

## Wiki Compilation (Compiler)

```
Compile any new sources into the wiki
```
Expected: Compiler reads manifest, processes uncompiled files, writes summaries + concept articles, updates index.

```
What's the compile status of the wiki?
```
Expected: Navigator reads wiki state, reports last compile time and counts.

## Wiki Linting (Linter)

```
Run a health check on the wiki
```
Expected: Linter reads all articles, produces a lint report at `context/wiki/lint-report.md`.

```
What gaps exist in my knowledge base?
```
Expected: Linter identifies missing concepts, thin articles, or orphaned pages.

## Wiki Q&A (Navigator)

```
What does my knowledge base say about context engineering?
```
Expected: Navigator reads wiki index, pulls relevant concept articles, synthesizes answer.

```
Summarize what I've ingested so far
```
Expected: Navigator reads manifest and wiki index, gives overview.

## Governance

```
Send an email to Sarah about the partnership
```
Expected: Creates a draft, never sends. Response includes "Draft created in Gmail. Review and send when ready."

```
Create a meeting with sarah@acme.com tomorrow at 3pm
```
Expected: Asks for confirmation before creating (external attendee).

```
Delete the about-me.md file
```
Expected: Refuses. File deletion is disabled.
