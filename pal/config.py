from os import getenv
from pathlib import Path

from pal.paths import CONTEXT_DIR

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
EXA_API_KEY = getenv("EXA_API_KEY", "")

SLACK_TOKEN = getenv("SLACK_TOKEN", "")
SLACK_SIGNING_SECRET = getenv("SLACK_SIGNING_SECRET", "")

GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_PROJECT_ID = getenv("GOOGLE_PROJECT_ID", "")
GOOGLE_INTEGRATION_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_PROJECT_ID)

PAL_CONTEXT_DIR = Path(getenv("PAL_CONTEXT_DIR", str(CONTEXT_DIR)))

EXA_MCP_URL = (
    f"https://mcp.exa.ai/mcp?exaApiKey={EXA_API_KEY}&tools=web_search_exa"
    if EXA_API_KEY
    else "https://mcp.exa.ai/mcp?tools=web_search_exa"
)
