"""
Pal - Personal Context-Agent
==============================

A personal agent that learns how you work.

Pal navigates a heterogeneous context graph — structured data, context directory files,
email, calendar, and web — to complete tasks and improve over time.

Test:
    python -m pal.agent
"""

from agno.agent import Agent
from agno.learn import LearnedKnowledgeConfig, LearningMachine, LearningMode
from agno.models.openai import OpenAIResponses

from db import create_knowledge, get_postgres_db
from pal.instructions import build_instructions
from pal.tools import build_tools

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
agent_db = get_postgres_db()

# Dual knowledge system
pal_knowledge = create_knowledge("Pal Knowledge", "pal_knowledge")
pal_learnings = create_knowledge("Pal Learnings", "pal_learnings")

# ---------------------------------------------------------------------------
# Create Agent
# ---------------------------------------------------------------------------
pal = Agent(
    id="pal",
    name="Pal",
    model=OpenAIResponses(id="gpt-5.4"),
    db=agent_db,
    instructions=build_instructions(),
    # Knowledge and Learning
    knowledge=pal_knowledge,
    search_knowledge=True,
    learning=LearningMachine(
        knowledge=pal_learnings,
        namespace="user",
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC, namespace="user"),
    ),
    # Tools
    tools=build_tools(pal_knowledge),
    enable_agentic_memory=True,
    # Context
    search_past_sessions=True,
    num_past_sessions_to_search=5,
    add_datetime_to_context=True,
    add_history_to_context=True,
    read_chat_history=True,
    num_history_runs=10,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Run Agent
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        # Smoke 1: Gmail fallback (no Google vars)
        "Check my latest emails",
        # Smoke 2: Calendar fallback (no Google vars)
        "What's on my calendar this week?",
        # Smoke 3: Web research without EXA_API_KEY
        "Research web trends on AI productivity",
        # Smoke 4: File-first retrieval
        "What do you know about my voice guidelines?",
        # Smoke 5: Cross-source retrieval (full capability)
        "What do I know about Project Atlas?",
        # Core: capture + learn cycle
        "Save a note: Met with Sarah Chen from Acme Corp. She's interested in a partnership.",
        "What do I know about Sarah?",
        # Core: file write
        "Save a summary of today's tasks to a file called daily-summary.md",
    ]
    for idx, prompt in enumerate(test_cases, start=1):
        print(f"\n--- Pal test case {idx}/{len(test_cases)} ---")
        print(f"Prompt: {prompt}")
        pal.print_response(prompt, stream=True)
