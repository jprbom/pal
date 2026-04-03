"""Custom API routes for Pal."""

from agno.os.auth import get_authentication_dependency
from agno.os.settings import AgnoAPISettings
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ContextReloadRequest(BaseModel):
    recreate: bool = False


class WikiCompileRequest(BaseModel):
    force: bool = False


class WikiIngestRequest(BaseModel):
    title: str
    url: str | None = None
    text: str | None = None
    tags: list[str] = []
    doc_type: str = "article"


def create_router(settings: AgnoAPISettings) -> APIRouter:
    router = APIRouter(
        dependencies=[Depends(get_authentication_dependency(settings))],
    )

    @router.post("/context/reload")
    def reload_context(body: ContextReloadRequest = ContextReloadRequest()):
        """Re-index context files into pal_knowledge."""
        from context.load_context import load_context

        loaded = load_context(recreate=body.recreate)
        return {"loaded": loaded, "recreate": body.recreate}

    @router.post("/wiki/compile")
    def compile_wiki(body: WikiCompileRequest = WikiCompileRequest()):
        """Trigger wiki compilation — process uncompiled raw/ files into wiki articles."""
        from pal.team import pal

        prompt = "Compile any new raw sources into the wiki."
        if body.force:
            prompt = "Recompile all raw sources into the wiki, even those already compiled."
        response = pal.run(prompt)
        content = response.content if response else "No response"
        return {"status": "completed", "force": body.force, "response": content}

    @router.post("/wiki/lint")
    def lint_wiki():
        """Trigger wiki health check."""
        from pal.team import pal

        response = pal.run("Run a health check on the wiki. Write a lint report.")
        content = response.content if response else "No response"
        return {"status": "completed", "response": content}

    @router.post("/wiki/ingest")
    def ingest_to_wiki(body: WikiIngestRequest):
        """Ingest a URL or text into raw/."""
        if not body.text and not body.url:
            return JSONResponse(content={"error": "Either url or text is required"}, status_code=400)

        from pal.config import PAL_CONTEXT_DIR
        from pal.tools.ingest import create_ingest_tools

        raw_dir = PAL_CONTEXT_DIR / "raw"
        ingest_url_tool, ingest_text_tool, _, _ = create_ingest_tools(raw_dir)

        if body.text:
            result = ingest_text_tool(
                title=body.title,
                content=body.text,
                source=body.url or "api",
                tags=body.tags or None,
                doc_type=body.doc_type,
            )
        else:
            result = ingest_url_tool(
                url=body.url,
                title=body.title,
                tags=body.tags or None,
                doc_type=body.doc_type,
            )

        return {"status": "ingested", "result": result}

    @router.post("/sync/pull")
    def sync_pull():
        """Pull latest context/ changes from GitHub."""
        from pal.config import GIT_SYNC_ENABLED
        from pal.tools.git import run_git

        if not GIT_SYNC_ENABLED:
            return JSONResponse(
                content={"error": "Git sync not configured. Set GITHUB_ACCESS_TOKEN and PAL_REPO_URL."}, status_code=400
            )

        ok, out = run_git(["pull", "--rebase", "--autostash"])
        return {"status": "ok" if ok else "error", "output": out}

    return router
