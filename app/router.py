"""Custom API routes for Pal."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agno.os.auth import get_authentication_dependency
from agno.os.settings import AgnoAPISettings


class ContextReloadRequest(BaseModel):
    recreate: bool = False


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

    return router
